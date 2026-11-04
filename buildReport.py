"""Build the offline report from the recorded present-tense experiment; no API calls."""
import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo

from runBenchmark import PROJECT_ROOT, can_resume, result_name

DATASETS = ('HS_HF_PR_500', 'HS_LF_PR', 'HS_NS_PR_500')
MODELS = ('openai/gpt-4o-mini', 'deepseek/deepseek-v4.1-flash', 'anthropic/claude-sonnet-4.5')
MODEL_NAMES = ('GPT-4o mini', 'DeepSeek v4.1 flash', 'Claude Sonnet 4.5')
EXPERIMENT_DATE = '2026-11-04'
LEADING = re.compile(r'^\s*(?:[*_`>#]+\s*)*(?:(?:final\s+)?answer\s*:\s*(?:[*_`]+\s*)*)?(yes|no)(?=[.!,:;\n]|\s*$)', re.I)
LAST_LINE = re.compile(r'^(?:[*_`>#]+\s*)*(?:(?:final\s+)?answer\s*:\s*)?(?:[*_`]+\s*)*(yes|no)[\s.!*_`]*$', re.I)


def extract_answer(text):
    if text is None:
        return {'answer': None, 'method': 'filtered', 'evidence': [], 'format': False}
    stripped = text.strip()
    direct = stripped.lower().rstrip('.')
    if direct in ('yes', 'no'):
        return {'answer': direct, 'method': 'direct', 'evidence': [{'rule': 'direct', 'text': stripped}], 'format': True}
    signals = []
    leading = LEADING.search(stripped)
    if leading:
        signals.append({'rule': 'prefix', 'text': leading.group(0).strip(), 'answer': leading.group(1).lower()})
    last = LAST_LINE.fullmatch(stripped.splitlines()[-1].strip()) if stripped else None
    if last:
        signals.append({'rule': 'last_line', 'text': last.group(0), 'answer': last.group(1).lower()})
    answers = {signal['answer'] for signal in signals}
    method = 'conflict' if len(answers) > 1 else 'unresolved' if not answers else 'both' if len(signals) == 2 else signals[0]['rule']
    return {'answer': next(iter(answers)) if len(answers) == 1 else None,
            'method': method, 'evidence': signals, 'format': False}


def summarize_observations(observations):
    rows = list(observations)
    total = len(rows)
    counts = Counter()
    for row in rows:
        counts['correct'] += row['correct']
        counts['originalCorrect'] += row['originalCorrect']
        counts['resolved'] += row['answer'] is not None
        counts['format'] += row['format']
        counts['filtered'] += row['status'] == 'filtered'
        counts['historical'] += row['historical']
    return {'total': total, **{key: counts[key] for key in ('correct', 'originalCorrect', 'resolved', 'format', 'filtered', 'historical')}}


def load_report(root=PROJECT_ROOT):
    system = json.loads((root / 'prompts/systemPrompts/zeroShot.json').read_text(encoding='utf-8'))[0]
    migration = json.loads((root / 'summaries/HS_LF_PR_legacy_migration.json').read_text(encoding='utf-8'))
    legacy = {record['destination'] for record in migration['records']}
    cases, costs, sources = [], [], []
    for dataset in DATASETS:
        path = root / 'prompts/userPrompts' / f'{dataset}.json'
        source_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        prompts = json.loads(path.read_text(encoding='utf-8'))
        audit = json.loads((root / 'summaries' / f'{dataset}_label_audit.json').read_text(encoding='utf-8'))
        if audit['dataset_sha256'] != source_hash or len(audit['rows']) != len(prompts):
            raise ValueError(f'Audit does not match source: {dataset}')
        if len(prompts) != 1500:
            raise ValueError(f'Expected 1500 rows: {dataset}')
        audits = {row['row']: row for row in audit['rows']}
        if set(audits) != set(range(1, 1501)):
            raise ValueError(f'Invalid audited row IDs: {dataset}')
        names = [result_name('model', prompt) for prompt in prompts]
        if len(set(names)) != len(names):
            raise ValueError(f'Duplicate result filenames: {dataset}')
        sources.append({'dataset': dataset, 'path': str(path.relative_to(root)), 'sha256': source_hash,
                        'rows': len(prompts), 'labelMismatches': sum(not row['label_matches'] for row in audits.values())})
        for index, prompt in enumerate(prompts, 1):
            original = prompt[6] in ('valid', 'valido')
            audited = audits[index]['implication_valid']
            variant = 'noncanonic' if prompt[7] == 'non-canonic' else 'valid' if original else 'invalid'
            case = {'key': f'{dataset}:{index}', 'dataset': dataset, 'row': index, 'id': prompt[1],
                    'variant': variant, 'originalValid': original, 'auditedValid': audited,
                    'labelMismatch': original != audited, 'prompt': prompt[2], 'responses': []}
            for model_index, model in enumerate(MODELS):
                relative = Path('data/zeroShot') / model.replace('/', '_') / dataset / result_name(model.replace('/', '_'), prompt)
                result_path = root / relative
                if not can_resume(result_path, prompt, system, model):
                    raise ValueError(f'Missing or mismatched result: {relative}')
                result = json.loads(result_path.read_text(encoding='utf-8'))
                filtered = result.get('response_status') == 'content_filter'
                extraction = extract_answer(None if filtered else result['responses'])
                answer = extraction['answer']
                case['responses'].append({
                    'model': model_index, 'text': None if filtered else result['responses'],
                    'status': 'filtered' if filtered else 'answered' if answer else extraction['method'],
                    **extraction, 'correct': answer == ('yes' if audited else 'no'),
                    'originalCorrect': answer == ('yes' if original else 'no'),
                    'historical': str(relative) in legacy, 'source': str(relative),
                })
            cases.append(case)
        summaries = json.loads((root / 'summaries' / f'{dataset}_zeroShot.json').read_text(encoding='utf-8'))
        if {row['model'] for row in summaries} != set(MODELS) or len(summaries) != 3:
            raise ValueError(f'Incomplete summary matrix: {dataset}')
        for summary in summaries:
            if summary['dataset_sha256'] != source_hash or summary['saved'] != 1500:
                raise ValueError(f'Stale summary: {dataset}')
            seen = set()
            current, historical = [], []
            for usage in summary['log_usage']:
                if usage['path'] in seen:
                    raise ValueError(f'Duplicate cost source: {usage["path"]}')
                seen.add(usage['path'])
                stamp = datetime.fromisoformat(usage['first_created_utc']).astimezone(ZoneInfo('America/Argentina/Buenos_Aires'))
                (current if stamp.date().isoformat() == EXPERIMENT_DATE else historical).append(usage)
            costs.append({'dataset': dataset, 'model': MODELS.index(summary['model']),
                          'newUsd': sum(log['cost_usd'] for log in current),
                          'historicalUsd': sum(log['cost_usd'] for log in historical),
                          'newTokens': sum(log['total_tokens'] for log in current),
                          'newRecords': sum(log['responses'] for log in current), 'logs': current + historical})
    all_observations = [response for case in cases for response in case['responses']]
    return {'date': EXPERIMENT_DATE, 'generatedAt': datetime.now(ZoneInfo('America/Argentina/Buenos_Aires')).isoformat(),
            'systemPrompt': system, 'datasets': list(DATASETS), 'models': list(MODELS), 'modelNames': list(MODEL_NAMES),
            'sources': sources, 'costs': costs, 'cases': cases, 'totals': summarize_observations(all_observations)}


def render_report(data):
    template = (Path(__file__).resolve().parent / 'reportTemplate.html').read_text(encoding='utf-8')
    # JSON stays inert even if a model emits a closing script tag or HTML markup.
    embedded = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
    return template.replace('__REPORT_DATA__', embedded)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('reports/presentes-2026-11-04.html'))
    args = parser.parse_args()
    data = load_report()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_report(data), encoding='utf-8')
    totals = data['totals']
    print(f'{args.output}: {totals["total"]} records, {totals["resolved"]} extracted answers, {totals["filtered"]} filters')


if __name__ == '__main__':
    main()

"""Summarize saved benchmark results and the usage costs in their logs."""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from runBenchmark import PROJECT_ROOT, can_resume, result_name


def summarize(dataset, system, model):
    prompt_path = PROJECT_ROOT / 'prompts/userPrompts' / f'{dataset}.json'
    prompts = json.loads(prompt_path.read_text(encoding='utf-8'))
    system_prompt = json.loads((PROJECT_ROOT / 'prompts/systemPrompts' / f'{system}.json').read_text(encoding='utf-8'))[0]
    model_name = model.replace('/', '_')
    directory = PROJECT_ROOT / 'data' / system / model_name / dataset
    groups = defaultdict(lambda: {'saved': 0, 'correct': 0, 'unrecognized': 0, 'filtered': 0, 'answers': defaultdict(int)})
    missing = []
    for index, prompt in enumerate(prompts, 1):
        path = directory / result_name(model_name, prompt)
        if not can_resume(path, prompt, system_prompt, model):
            missing.append(index)
            continue
        result = json.loads(path.read_text(encoding='utf-8'))
        group = groups[f'{prompt[6]} / {prompt[7]}']
        group['saved'] += 1
        if result.get('response_status') == 'content_filter':
            group['filtered'] += 1
            group['answers']['content_filter'] += 1
            continue
        answer = result['responses'].strip().lower().rstrip('.')
        group['answers'][answer if answer in ('yes', 'no') else 'other'] += 1
        expected = {'valid': 'yes', 'valido': 'yes', 'invalid': 'no'}[prompt[6]]
        group['correct'] += answer == expected
        group['unrecognized'] += answer not in ('yes', 'no')
    logs = []
    log_usage = []
    cost = 0
    logged = 0
    tokens = 0
    for path in sorted((PROJECT_ROOT / 'logs').glob(f'{dataset}_{model_name}_*.json')):
        records = json.loads(path.read_text(encoding='utf-8'))
        matching = [r for r in records if (
            r.get('benchmark_input', {}).get('system_prompt') == system_prompt
            or ('benchmark_input' not in r and system == 'zeroShot')
        )]
        if not matching:
            continue
        logs.append(str(path.relative_to(PROJECT_ROOT)))
        timestamps = [r['created'] for r in matching if isinstance(r.get('created'), (int, float))]
        log_usage.append({
            'path': str(path.relative_to(PROJECT_ROOT)),
            'responses': len(matching),
            'cost_usd': sum(r.get('usage', {}).get('cost', 0) or 0 for r in matching),
            'total_tokens': sum(r.get('usage', {}).get('total_tokens', 0) or 0 for r in matching),
            'first_created_utc': datetime.fromtimestamp(min(timestamps), timezone.utc).isoformat() if timestamps else None,
            'last_created_utc': datetime.fromtimestamp(max(timestamps), timezone.utc).isoformat() if timestamps else None,
        })
        logged += len(matching)
        cost += sum(r.get('usage', {}).get('cost', 0) or 0 for r in matching)
        tokens += sum(r.get('usage', {}).get('total_tokens', 0) or 0 for r in matching)
    saved = sum(g['saved'] for g in groups.values())
    correct = sum(g['correct'] for g in groups.values())
    unrecognized = sum(g['unrecognized'] for g in groups.values())
    filtered = sum(g['filtered'] for g in groups.values())
    return {'dataset': dataset, 'dataset_sha256': hashlib.sha256(prompt_path.read_bytes()).hexdigest(),
            'system': system, 'model': model, 'expected': len(prompts), 'saved': saved,
            'missing_or_mismatched_rows': missing, 'correct': correct,
            'accuracy': correct / saved if saved else None, 'unrecognized': unrecognized,
            'filtered': filtered, 'text_responses': saved - filtered,
            'groups': dict(groups),
            'logged_responses': logged, 'logged_cost_usd': cost, 'logged_total_tokens': tokens,
            'logs': logs, 'log_usage': log_usage}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dataset')
    parser.add_argument('--system', default='zeroShot')
    parser.add_argument('--model', action='append', required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    summaries = [summarize(args.dataset, args.system, model) for model in args.model]
    content = json.dumps(summaries, indent=2, ensure_ascii=False) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding='utf-8')
        for summary in summaries:
            print(f'{summary["model"]}: {summary["saved"]}/{summary["expected"]} saved; '
                  f'{summary["correct"]} label matches; {summary["unrecognized"]} non-yes/no; '
                  f'{summary["filtered"]} filtered; '
                  f'USD {summary["logged_cost_usd"]:.10f} recorded')
    else:
        print(content, end='')
    return 0 if all(s['saved'] == s['expected'] for s in summaries) else 1


if __name__ == '__main__':
    raise SystemExit(main())

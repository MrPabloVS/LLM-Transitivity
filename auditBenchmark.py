"""Audit HS templates as material propositional implications, preserving source labels."""
import argparse
from collections import Counter
import hashlib
from itertools import product
import json
from pathlib import Path
import re

from runBenchmark import PROJECT_ROOT, can_resume, result_name


def implication_validity(text):
    premises, conclusion = text.split('therefore if ', 1)
    first, second = re.split(r',\s*if ', premises, maxsplit=1)
    edges = [first.removeprefix('if ').strip().rstrip(',').split(' then ', 1),
             second.strip().rstrip(',').split(' then ', 1)]
    conclusion = conclusion.strip().split(' then ', 1)
    if any(len(edge) != 2 for edge in edges + [conclusion]):
        raise ValueError('Unsupported implication template')
    atoms = sorted({atom for edge in edges + [conclusion] for atom in edge})
    if len(atoms) > 6:
        raise ValueError('Too many atomic propositions for this HS template')
    for values in product((False, True), repeat=len(atoms)):
        interpretation = dict(zip(atoms, values))
        def holds(edge):
            return not interpretation[edge[0]] or interpretation[edge[1]]
        if all(holds(edge) for edge in edges) and not holds(conclusion):
            return False
    return True


def audit(dataset, system, models):
    source = PROJECT_ROOT / 'prompts/userPrompts' / f'{dataset}.json'
    prompts = json.loads(source.read_text(encoding='utf-8'))
    records = []
    for index, prompt in enumerate(prompts, 1):
        valid = implication_validity(prompt[2])
        records.append({'row': index, 'label': prompt[6], 'form': prompt[7],
                        'implication_valid': valid,
                        'label_matches': valid == (prompt[6] in ('valid', 'valido'))})
    system_prompt = json.loads((PROJECT_ROOT / 'prompts/systemPrompts' / f'{system}.json').read_text(encoding='utf-8'))[0]
    evaluations = []
    for model in models:
        name = model.replace('/', '_')
        directory = PROJECT_ROOT / 'data' / system / name / dataset
        saved = correct = unrecognized = filtered = 0
        groups = Counter()
        for prompt, record in zip(prompts, records):
            path = directory / result_name(name, prompt)
            if not can_resume(path, prompt, system_prompt, model):
                continue
            data = json.loads(path.read_text(encoding='utf-8'))
            saved += 1
            if data.get('response_status') == 'content_filter':
                filtered += 1
                continue
            answer = data['responses'].strip().lower().rstrip('.')
            matched = answer == ('yes' if record['implication_valid'] else 'no')
            unrecognized += answer not in ('yes', 'no')
            correct += matched
            groups[f'{prompt[6]} / {prompt[7]}'] += matched
        evaluations.append({'model': model, 'saved': saved, 'correct': correct,
                            'accuracy': correct / saved if saved else None,
                            'unrecognized': unrecognized,
                            'filtered': filtered,
                            'correct_by_source_variant': dict(groups)})
    return {'dataset': dataset, 'dataset_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'interpretation': 'Material propositional implication; each distinct clause is an independent atomic proposition',
            'method': 'Exhaustive truth tables: check every valuation satisfying both premises against the conclusion',
            'mismatches': sum(not row['label_matches'] for row in records),
            'mismatched_rows': [row['row'] for row in records if not row['label_matches']],
            'rows': records, 'evaluations': evaluations}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dataset')
    parser.add_argument('--system', default='zeroShot')
    parser.add_argument('--model', action='append', default=[])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.dataset, args.system, args.model)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(f'{args.dataset}: {len(result["rows"])} audited; {result["mismatches"]} labels disagree with propositional validity')
    for evaluation in result['evaluations']:
        print(f'{evaluation["model"]}: {evaluation["correct"]}/{evaluation["saved"]} agrees with audited validity')


if __name__ == '__main__':
    main()

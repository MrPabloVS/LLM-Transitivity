"""Build the offline report from the recorded present-tense experiment; no API calls."""
import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
from os.path import relpath
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


def confusion_matrix(observations):
    """Positive means valid/yes; filters and unresolved decisions are not negatives."""
    counts = Counter({key: 0 for key in ('tp', 'fp', 'tn', 'fn', 'filtered', 'unresolved', 'positiveTotal', 'negativeTotal')})
    for expected, response in observations:
        counts['positiveTotal' if expected else 'negativeTotal'] += 1
        if response['answer'] is None:
            counts['filtered' if response['status'] == 'filtered' else 'unresolved'] += 1
            continue
        predicted = response['answer'] == 'yes'
        counts['tp' if expected and predicted else 'fn' if expected else 'fp' if predicted else 'tn'] += 1
    return dict(counts)


def case_confusion(data, dataset, model, variant=None, reference='audited'):
    field = 'auditedValid' if reference == 'audited' else 'originalValid'
    return confusion_matrix((case[field], response) for case in data['cases']
                            if case['dataset'] == dataset and (variant is None or case['variant'] == variant)
                            for response in case['responses'] if response['model'] == model)


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



def render_markdown(data, html_name='presentes-2026-11-04.html'):
    integer = lambda n: f'{n:,}'.replace(',', '.')
    percent = lambda n, d: f'{n / d * 100:.2f}'.replace('.', ',') + ' %' if d else '—'
    usd = lambda n: 'USD ' + f'{n:.5f}'.replace('.', ',')
    grouped = {}
    for dataset in DATASETS:
        for model in range(3):
            grouped[dataset, model] = summarize_observations(
                r for case in data['cases'] if case['dataset'] == dataset
                for r in case['responses'] if r['model'] == model)
    totals = data['totals']
    lines = ['# Modelos, vocabulario y validez lógica', '',
             f'Informe de las ejecuciones del {data["date"]}. Sistema: `zeroShot`. Tres modelos y tres datasets de presente.', '',
             f'**{integer(totals["total"])} registros; {integer(totals["resolved"])} decisiones extraíbles; {totals["filtered"]} filtros del proveedor; {totals["historical"]} resultados históricos reutilizados.**', '',
             f'[Abrir la versión HTML interactiva]({html_name}). Incluye los argumentos y respuestas completos, filtros, búsqueda y evidencia de extracción.', '',
             '## Antes de comparar', '',
             'En cada dataset, las 500 filas etiquetadas como válidas no canónicas tienen premisas `Q → R`, `P → Q` y conclusión `R → P`. Esa conclusión es inválida bajo implicación material. Hay 1.500 etiquetas discrepantes en las 4.500 filas de origen de presente, equivalentes a 4.500 observaciones al considerar los tres modelos.', '',
             'La referencia principal de este informe es la validez auditada. Las etiquetas y los resultados originales no se modificaron. La respuesta extraída es una decisión explícita, no una evaluación de todos los pasos de la explicación.', '',
             '## Lectura de los resultados', '']
    g = [grouped[dataset, 0] for dataset in DATASETS]
    lines += [f'- GPT-4o mini obtiene {percent(g[1]["correct"], 1500)} en LF, frente a {percent(g[0]["correct"], 1500)} en HF y {percent(g[2]["correct"], 1500)} en NS. Son diferencias descriptivas; GPT/LF mezcla 211 resultados históricos con 1.289 nuevos.',
              '- DeepSeek responde correctamente los 4.500 casos auditados. Claude tiene 4.493 decisiones extraíbles correctas y siete filtros: 99,84 % sobre todos sus casos.',
              '- Claude incluye texto adicional en 4.101 respuestas. Separar extracción y formato cambia sustancialmente la interpretación de sus resultados.', '',
              '## Comparación principal', '',
              '**Denominador: todos los casos**, incluidos filtros y casos no interpretables. La última columna usa la etiqueta original, pero la misma decisión extraída; no es el evaluador estricto anterior.', '',
              '| Dataset | Modelo | Correctas auditadas / total | Corrección | Cobertura | Correctas según etiqueta original |',
              '| --- | --- | ---: | ---: | ---: | ---: |']
    for dataset in DATASETS:
        for model, name in enumerate(MODEL_NAMES):
            v = grouped[dataset, model]
            lines.append(f'| `{dataset}` | {name} | {v["correct"]} / {v["total"]} | {percent(v["correct"], v["total"])} | {percent(v["resolved"], v["total"])} | {v["originalCorrect"]} / {v["total"]} |')
    lines += ['', '## Falsos positivos y falsos negativos', '',
              '**Positivo = responder `yes`: aceptar el argumento como válido.** VP: válido aceptado; FP: inválido aceptado; FN: válido rechazado; VN: inválido rechazado. La referencia de estas tablas es la validez auditada.', '',
              'Tasa de falsos positivos = `FP / (FP + VN)`; tasa de falsos negativos = `FN / (FN + VP)`. Los filtros y las decisiones no resueltas quedan fuera de estas tasas y de la matriz; no se convierten en respuestas negativas. La cobertura por clase se muestra aparte. La corrección principal anterior mantiene todos los casos en su denominador.', '',
              '| Dataset | Modelo | VP | FP | FN | VN | Tasa FP | Tasa FN |',
              '| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    confusion_rows = []
    for dataset in DATASETS:
        for model, name in enumerate(MODEL_NAMES):
            v = case_confusion(data, dataset, model)
            confusion_rows.append((dataset, name, v))
            lines.append(f'| `{dataset}` | {name} | {v["tp"]} | {v["fp"]} | {v["fn"]} | {v["tn"]} | {v["fp"]}/{v["fp"] + v["tn"]} · {percent(v["fp"], v["fp"] + v["tn"])} | {v["fn"]}/{v["fn"] + v["tp"]} · {percent(v["fn"], v["fn"] + v["tp"])} |')
    lines += ['', '| Dataset | Modelo | Válidos interpretables / total válidos | Inválidos interpretables / total inválidos | Filtrados | Sin resolver |',
              '| --- | --- | ---: | ---: | ---: | ---: |']
    for dataset, name, v in confusion_rows:
        lines.append(f'| `{dataset}` | {name} | {v["tp"] + v["fn"]}/{v["positiveTotal"]} | {v["fp"] + v["tn"]}/{v["negativeTotal"]} | {v["filtered"]} | {v["unresolved"]} |')
    lines += ['', '### Falsos positivos según la variante inválida', '',
              'La variante originalmente llamada válida no canónica es inválida bajo la auditoría. Se compara por separado con la variante inválida canónica.', '',
              '| Dataset | Modelo | Variante de origen | FP | VN | Tasa FP | Cobertura de inválidos |',
              '| --- | --- | --- | ---: | ---: | ---: | ---: |']
    for dataset in DATASETS:
        for model, name in enumerate(MODEL_NAMES):
            for variant, label in [('invalid', 'Inválida canónica'), ('noncanonic', 'Válida no canónica (inválida auditada)')]:
                v = case_confusion(data, dataset, model, variant)
                n = v['fp'] + v['tn']
                lines.append(f'| `{dataset}` | {name} | {label} | {v["fp"]} | {v["tn"]} | {percent(v["fp"], n)} | {n}/{v["negativeTotal"]} |')
    lines += ['', '## Desglose por variante original', '',
              '“Válida no canónica” conserva el nombre de origen; su validez auditada es inválida en estos datos.', '',
              '| Dataset | Modelo | Variante original | Correctas auditadas / total |', '| --- | --- | --- | ---: |']
    for dataset in DATASETS:
        for model, name in enumerate(MODEL_NAMES):
            for variant, label in [('valid', 'Válida canónica'), ('invalid', 'Inválida canónica'), ('noncanonic', 'Válida no canónica')]:
                v = summarize_observations(r for case in data['cases'] if case['dataset'] == dataset and case['variant'] == variant for r in case['responses'] if r['model'] == model)
                lines.append(f'| `{dataset}` | {name} | {label} | {v["correct"]} / {v["total"]} |')
    lines += ['', '## Formato y respuesta explícita', '',
              'El formato estricto conserva el normalizador original: `strip().lower().rstrip(".")`. La extracción admite además una decisión explícita al inicio seguida de puntuación o una última línea formada por `yes`/`no`, con Markdown o `Answer:` opcionales. Señales contradictorias quedan como conflicto; ausencia de señales, sin resolver. No se infiere una respuesta de “yes or no” ni de la explicación completa.', '',
              '| Dataset | Modelo | Formato estricto / total | Decisión extraíble / total | Precisión sobre interpretables | Filtrados |',
              '| --- | --- | ---: | ---: | ---: | ---: |']
    for dataset in DATASETS:
        for model, name in enumerate(MODEL_NAMES):
            v = grouped[dataset, model]
            lines.append(f'| `{dataset}` | {name} | {v["format"]} / {v["total"]} | {v["resolved"]} / {v["total"]} | {percent(v["correct"], v["resolved"])} | {v["filtered"]} |')
    lines += ['', '## Costos registrados', '',
              f'Total nuevo registrado: **{usd(sum(c["newUsd"] for c in data["costs"]))}**. Suma `usage.cost` de los logs de las corridas del 4 de noviembre, incluidos una sola vez los siete últimos filtros recuperados.', '',
              'Quedan separados la prueba inicial de tres casos (USD 0,00003045), los logs históricos y los intentos fallidos o interrumpidos no registrados por completo. Este total no sustituye una conciliación de facturación. Los logs históricos pueden contener repeticiones y no determinan el costo exacto de los 211 resultados reutilizados.', '',
              '| Dataset | Modelo | USD nuevos | Tokens nuevos registrados | Registros nuevos en logs | USD históricos |',
              '| --- | --- | ---: | ---: | ---: | ---: |']
    for c in data['costs']:
        lines.append(f'| `{c["dataset"]}` | {MODEL_NAMES[c["model"]]} | {usd(c["newUsd"])} | {integer(c["newTokens"])} | {integer(c["newRecords"])} | {usd(c["historicalUsd"])} |')
    lines += ['', '## Filtros y procedencia', '',
              '- Claude/LF: filas 131, 148, 407, 631, 648, 725 y 1054, contadas desde 1. El proveedor devolvió `content_filter`; se preservó texto nulo. Ningún filtro se interpreta como `no`.',
              '- Los 211 resultados históricos pertenecen a GPT/LF. Se comprobaron prompt, sistema, modelo, ID, etiquetas y respuesta antes de reutilizarlos. No equivalen a una repetición nueva.',
              '- Cada caso se identifica por dataset y fila; los IDs de base están compartidos entre las tres variantes.', '',
              '## Método y límites', '',
              '- La auditoría enumera todas las asignaciones de verdad de las cláusulas, tratadas como proposiciones atómicas independientes. Busca si ambas premisas pueden ser verdaderas y la conclusión falsa.',
              '- Corrección principal = correctas / total. Cobertura = decisiones extraíbles / total. Precisión sobre interpretables = correctas / decisiones extraíbles. Cumplimiento de formato = respuestas directas normalizadas / total.',
              '- La corrección principal mantiene filtros y respuestas sin decisión en el denominador. El informe no juzga la validez de cada paso de las explicaciones.',
              '- No hubo repeticiones nuevas, temperatura ni semilla fijadas. Las variantes no son réplicas independientes. No se atribuye causalidad al vocabulario ni se realizan pruebas de significancia.',
              '- No se hicieron nuevas llamadas a modelos para producir este análisis.', '',
              '## Configuración y trazabilidad', '', f'Instrucción de sistema: `{data["systemPrompt"]}`.', '',
              '[Registro de comandos y corridas](../CORRIDAS.md) · [Pendientes](../PENDIENTES.md).', '']
    for src in data['sources']:
        lines += [f'- `{src["path"]}`: {src["rows"]} filas; SHA-256 `{src["sha256"]}`.']
    lines += ['', 'Logs utilizados para costos:', '']
    for path in dict.fromkeys(log['path'] for c in data['costs'] for log in c['logs']):
        lines.append(f'- `{path}`')
    lines += ['', f'Generado: {data["generatedAt"]} (hora de Buenos Aires).', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('reports/presentes-2026-11-04.html'))
    parser.add_argument('--markdown-output', type=Path, help='Defaults to the HTML output path with .md extension')
    args = parser.parse_args()
    markdown_path = args.markdown_output or args.output.with_suffix('.md')
    if markdown_path.resolve() == args.output.resolve():
        parser.error('HTML and Markdown outputs must be different paths')
    data = load_report()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_report(data), encoding='utf-8')
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    html_link = Path(relpath(args.output.resolve(), markdown_path.resolve().parent)).as_posix()
    markdown_path.write_text(render_markdown(data, html_link), encoding='utf-8')
    print(f'Markdown: {markdown_path}')
    totals = data['totals']
    print(f'{args.output}: {totals["total"]} records, {totals["resolved"]} extracted answers, {totals["filtered"]} filters')


if __name__ == '__main__':
    main()

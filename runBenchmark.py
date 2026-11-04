import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import json
import os
from pathlib import Path
import time

import requests
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent


class InvalidModelResponse(ValueError):
    def __init__(self, payload):
        super().__init__('Empty or non-text model response')
        self.payload = payload


def result_name(model, prompt):
    # Each case ID is shared by three variants.
    return f"{model}_{prompt[1]}_{prompt[0]}_{prompt[6]}_{prompt[7]}.json"


def save_json(path, data):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding='utf-8')
    temporary.replace(path)


def tags_for(prompt):
    return dict(zip(
        ('frecuency', 'verbal time', 'conectors', 'validity', 'cononic'),
        prompt[3:8],
    ))


def can_resume(path, prompt, system_prompt, model):
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (FileNotFoundError, json.JSONDecodeError):
        return False
    return (
        isinstance(data, dict)
        and data.get('userPrompt') == prompt[2]
        and data.get('system_prompt') == system_prompt
        and data.get('model') == model
        and data.get('id') == prompt[1]
        and data.get('tags') == tags_for(prompt)
        and (
            (isinstance(data.get('responses'), str) and bool(data['responses'].strip()))
            or (data.get('response_status') == 'content_filter' and data.get('responses') is None)
        )
    )


def call_model(prompt, system_prompt, model, api_key, retries):
    for attempt in range(retries + 1):
        try:
            response = requests.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers={'Authorization': f'Bearer {api_key}'},
                json={'model': model, 'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': prompt[2]},
                ]},
                timeout=(10, 120),
            )
            response.raise_for_status()
            raw = response.json()
            if raw['choices'][0].get('finish_reason') == 'content_filter':
                return None, raw
            answer = raw['choices'][0]['message']['content']
            if not isinstance(answer, str) or not answer.strip():
                raise InvalidModelResponse(raw)
            return answer, raw
        except requests.HTTPError as error:
            status = error.response.status_code
            if status not in (408, 429) and status < 500:
                raise
            if attempt == retries:
                raise
            # Respect rate-limit backoff when the API supplies seconds.
            retry_after = error.response.headers.get('Retry-After', '')
            delay = float(retry_after) if retry_after.isdigit() else 2 ** attempt
        except (requests.RequestException, ValueError, KeyError, IndexError):
            if attempt == retries:
                raise
            delay = 2 ** attempt
        time.sleep(delay)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('promptFile')
    parser.add_argument('--system', default='zeroShot')
    parser.add_argument('--model', default='openai/gpt-4o-mini')
    parser.add_argument('--workers', type=int, default=1, help='Maximum simultaneous API calls')
    parser.add_argument('--retries', type=int, default=3, help='Retries per transient failure')
    parser.add_argument('--resume', action='store_true', help='Skip matching saved responses')
    args = parser.parse_args()
    if args.workers < 1 or args.retries < 0:
        parser.error('--workers must be positive and --retries must be nonnegative')

    prompts = json.loads((PROJECT_ROOT / 'prompts' / 'userPrompts' / f'{args.promptFile}.json').read_text(encoding='utf-8'))
    systems = json.loads((PROJECT_ROOT / 'prompts' / 'systemPrompts' / f'{args.system}.json').read_text(encoding='utf-8'))
    if not isinstance(prompts, list) or not prompts:
        parser.error('Dataset must be a nonempty list')
    for index, prompt in enumerate(prompts, 1):
        if not isinstance(prompt, list) or len(prompt) != 8 or not isinstance(prompt[2], str):
            parser.error(f'Prompt {index} must contain the 8 benchmark fields')
    if not isinstance(systems, list) or not systems or not isinstance(systems[0], str):
        parser.error('System prompt must be a nonempty list of strings')
    system_prompt = systems[0]
    model_name = args.model.replace('/', '_')
    names = [result_name(model_name, prompt) for prompt in prompts]
    if len(set(names)) != len(names):
        parser.error('Dataset contains duplicate case IDs within the same variant')

    load_dotenv(PROJECT_ROOT / '.env')
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        parser.error('Set OPENROUTER_API_KEY before running this script')

    out_dir = PROJECT_ROOT / 'data' / args.system / model_name / args.promptFile
    out_dir.mkdir(parents=True, exist_ok=True)
    log_dir = PROJECT_ROOT / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    date = datetime.now().strftime('%Y-%m-%d_%H-%M-%S_%f')
    log_path = log_dir / f'{args.promptFile}_{model_name}_{args.system}_{date}.json'
    pending = [(index, prompt, out_dir / name) for index, (prompt, name) in enumerate(zip(prompts, names), 1)
               if not args.resume or not can_resume(out_dir / name, prompt, system_prompt, args.model)]
    completed = len(prompts) - len(pending)
    filtered = sum(json.loads((out_dir / name).read_text(encoding='utf-8')).get('response_status') == 'content_filter'
                   for prompt, name in zip(prompts, names)
                   if args.resume and can_resume(out_dir / name, prompt, system_prompt, args.model))
    print(f'Total: {len(prompts)}; saved: {completed}; pending: {len(pending)}; workers: {args.workers}', flush=True)
    results = []
    failed = 0
    # Workers only call the API. The main thread owns all file writes.
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(call_model, prompt, system_prompt, args.model, api_key, args.retries): (index, prompt, path)
                   for index, prompt, path in pending}
        for future in as_completed(futures):
            index, prompt, path = futures[future]
            try:
                answer, raw = future.result()
            except Exception as error:
                failed += 1
                payload = getattr(error, 'payload', None)
                if isinstance(error, requests.HTTPError):
                    try:
                        payload = error.response.json()
                    except ValueError:
                        pass
                error_dir = out_dir / 'errors'
                error_dir.mkdir(exist_ok=True)
                save_json(error_dir / f'{date}_{index}.json', {
                    'row': index, 'prompt': prompt, 'model': args.model,
                    'system_prompt': system_prompt, 'retry_budget': args.retries,
                    'error': str(error), 'last_api_response': payload,
                })
                print(f'Prompt {index} failed: {type(error).__name__}: {error}', flush=True)
                continue
            data = {'userPrompt': prompt[2], 'system_prompt': system_prompt,
                    'model': args.model, 'id': prompt[1], 'tags': tags_for(prompt),
                    'responses': answer}
            if raw['choices'][0].get('finish_reason') == 'content_filter':
                data['response_status'] = 'content_filter'
                data['api_response'] = raw
                filtered += 1
            raw['benchmark_input'] = {'row': index, **{key: value for key, value in data.items() if key not in ('responses', 'api_response')}}
            results.append(raw)
            save_json(log_path, results)
            save_json(path, data)
            completed += 1
            if completed % 25 == 0 or completed == len(prompts):
                print(f'Saved {completed}/{len(prompts)}; failed: {failed}', flush=True)
    print(f'Finished: {completed}/{len(prompts)} saved; {filtered} filtered; {failed} failed', flush=True)
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())

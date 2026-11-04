import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

import requests
import summarizeBenchmark
from auditBenchmark import implication_validity

spec = importlib.util.spec_from_file_location('benchmark', Path(__file__).resolve().parents[1] / 'runBenchmark.py')
benchmark = importlib.util.module_from_spec(spec)
spec.loader.exec_module(benchmark)


class BenchmarkTests(unittest.TestCase):
    def test_implication_validity(self):
        self.assertTrue(implication_validity('if P then Q, if Q then R, therefore if P then R'))
        self.assertTrue(implication_validity('if Q then R,if P then Q therefore if P then R'))
        self.assertFalse(implication_validity('if Q then R,if P then Q therefore if R then P'))
        self.assertFalse(implication_validity('if P then Q, if Q then R, therefore if R then P'))

    def test_concurrent_variants_and_resume(self):
        rows = [['HS', [['S1', 'V1', 'O1']], f'prompt {i}', 'HF', 'PR', 'if then / therefore', validity, form]
                for i, (validity, form) in enumerate([('valid', 'canonic'), ('invalid', 'canonic'), ('valid', 'non-canonic')])]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'prompts/userPrompts').mkdir(parents=True)
            (root / 'prompts/systemPrompts').mkdir(parents=True)
            (root / 'prompts/userPrompts/sample.json').write_text(json.dumps(rows))
            (root / 'prompts/systemPrompts/zeroShot.json').write_text(json.dumps(['yes or no']))
            active = 0
            maximum = 0
            lock = threading.Lock()

            def fake_call(*args):
                nonlocal active, maximum
                with lock:
                    active += 1
                    maximum = max(maximum, active)
                time.sleep(0.03)
                with lock:
                    active -= 1
                return 'yes', {'choices': [{'message': {'content': 'yes'}}]}

            argv = ['runBenchmark.py', 'sample', '--workers', '2', '--resume']
            with patch.object(benchmark, 'PROJECT_ROOT', root), patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test'}), patch('sys.argv', argv), contextlib.redirect_stdout(io.StringIO()):
                with patch.object(benchmark, 'call_model', side_effect=fake_call) as call:
                    self.assertEqual(benchmark.main(), 0)
                    self.assertEqual(call.call_count, 3)
                    self.assertEqual(maximum, 2)
                files = list((root / 'data/zeroShot/openai_gpt-4o-mini/sample').glob('*.json'))
                self.assertEqual(len(files), 3)
                saved = {p: p.read_bytes() for p in files}
                with patch.object(benchmark, 'call_model') as call:
                    self.assertEqual(benchmark.main(), 0)
                    call.assert_not_called()
                self.assertEqual(saved, {p: p.read_bytes() for p in files})
                for incomplete in ('{broken', '[]'):
                    files[0].write_text(incomplete)
                    with patch.object(benchmark, 'call_model', side_effect=fake_call) as call:
                        self.assertEqual(benchmark.main(), 0)
                        self.assertEqual(call.call_count, 1)
                for p in files:
                    self.assertEqual(json.loads(p.read_text())['responses'], 'yes')
                files[0].unlink()
                payload = {'choices': [{'message': {'content': None}}], 'usage': {'cost': 0.01}}
                with patch.object(benchmark, 'call_model', side_effect=benchmark.InvalidModelResponse(payload)):
                    self.assertEqual(benchmark.main(), 1)
                failures = list((files[0].parent / 'errors').glob('*.json'))
                self.assertEqual(len(failures), 1)
                self.assertEqual(json.loads(failures[0].read_text())['last_api_response'], payload)
                filtered = {'choices': [{'finish_reason': 'content_filter', 'message': {'content': None}}]}
                with patch.object(benchmark, 'call_model', return_value=(None, filtered)):
                    self.assertEqual(benchmark.main(), 0)
                self.assertEqual(json.loads(files[0].read_text())['response_status'], 'content_filter')
                with patch.object(benchmark, 'call_model') as call:
                    self.assertEqual(benchmark.main(), 0)
                    call.assert_not_called()
                with patch.object(summarizeBenchmark, 'PROJECT_ROOT', root):
                    summary = summarizeBenchmark.summarize('sample', 'zeroShot', 'openai/gpt-4o-mini')
                self.assertEqual(summary['saved'], 3)
                self.assertEqual(summary['filtered'], 1)

    def test_retry_rate_limit(self):
        limited = requests.Response()
        limited.status_code = 429
        limited.headers['Retry-After'] = '2'
        success = requests.Response()
        success.status_code = 200
        success._content = b'{"choices":[{"message":{"content":"yes"}}]}'
        with patch.object(benchmark.requests, 'post', side_effect=[limited, success]) as post, patch.object(benchmark.time, 'sleep') as sleep:
            answer, _ = benchmark.call_model(['HS', 1, 'prompt'], 'system', 'model', 'test', 3)
            self.assertEqual(answer, 'yes')
            self.assertEqual(post.call_count, 2)
            sleep.assert_called_once_with(2)

    def test_no_retry_auth_failure(self):
        response = requests.Response()
        response.status_code = 401
        with patch.object(benchmark.requests, 'post', return_value=response) as post:
            with self.assertRaises(requests.HTTPError):
                benchmark.call_model(['HS', 1, 'prompt'], 'system', 'model', 'test', 3)
            self.assertEqual(post.call_count, 1)

    def test_content_filter_is_terminal(self):
        response = requests.Response()
        response.status_code = 200
        response._content = b'{"choices":[{"finish_reason":"content_filter","message":{"content":null}}]}'
        with patch.object(benchmark.requests, 'post', return_value=response) as post:
            answer, raw = benchmark.call_model(['HS', 1, 'prompt'], 'system', 'model', 'test', 3)
            self.assertIsNone(answer)
            self.assertEqual(raw['choices'][0]['finish_reason'], 'content_filter')
            self.assertEqual(post.call_count, 1)


if __name__ == '__main__':
    unittest.main()

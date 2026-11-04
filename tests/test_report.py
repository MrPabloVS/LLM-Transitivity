import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

import buildReport as report


class ExtractionTests(unittest.TestCase):
    def test_direct_format_matches_existing_normalizer(self):
        for text, expected in [('yes', 'yes'), (' YES. ', 'yes'), ('No...', 'no')]:
            with self.subTest(text=text):
                result = report.extract_answer(text)
                self.assertEqual(result['answer'], expected)
                self.assertTrue(result['format'])
                self.assertEqual(result['method'], 'direct')

    def test_explanations_and_markdown(self):
        for text, expected in [('Yes.\nThe premises entail it.', 'yes'),
                               ('Analysis.\n**Answer: no.**', 'no'),
                               ('**Answer:** Yes.\nExplanation.', 'yes'),
                               ('No.\nExplanation.\n**No**', 'no')]:
            with self.subTest(text=text):
                result = report.extract_answer(text)
                self.assertEqual(result['answer'], expected)
                self.assertFalse(result['format'])
                self.assertTrue(result['evidence'])

    def test_conflict_and_nonanswers(self):
        result = report.extract_answer('Yes.\nAfter reconsideration:\nAnswer: no')
        self.assertIsNone(result['answer'])
        self.assertEqual(result['method'], 'conflict')
        for text in ['yes or no', 'No problem', 'It is invalid.', '', 'The question asks yes or no']:
            with self.subTest(text=text):
                self.assertEqual(report.extract_answer(text)['method'], 'unresolved')
        self.assertEqual(report.extract_answer(None)['method'], 'filtered')


class ReportIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch('requests.post', side_effect=AssertionError('No API calls')), patch('requests.get', side_effect=AssertionError('No network')):
            cls.data = report.load_report()
        cls.html = report.render_report(cls.data)

    def test_complete_matrix_and_denominators(self):
        self.assertEqual(len(self.data['cases']), 4500)
        self.assertEqual(len({case['key'] for case in self.data['cases']}), 4500)
        self.assertEqual(self.data['totals']['total'], 13500)
        self.assertEqual(self.data['totals']['resolved'], 13493)
        self.assertEqual(self.data['totals']['filtered'], 7)
        self.assertEqual(self.data['totals']['historical'], 211)
        self.assertEqual(sum(case['labelMismatch'] for case in self.data['cases']), 1500)
        expected = {
            'HS_HF_PR_500': (1480, 1500, 1500),
            'HS_LF_PR': (1258, 1500, 1493),
            'HS_NS_PR_500': (1482, 1500, 1500),
        }
        for dataset, scores in expected.items():
            for model, score in enumerate(scores):
                rows = [r for c in self.data['cases'] if c['dataset'] == dataset for r in c['responses'] if r['model'] == model]
                metrics = report.summarize_observations(rows)
                self.assertEqual(metrics['total'], 1500)
                self.assertEqual(metrics['correct'], score)
        claude = [r for c in self.data['cases'] for r in c['responses'] if r['model'] == 2]
        self.assertEqual(report.summarize_observations(claude)['resolved'], 4493)
        self.assertFalse(any(r['method'] in ('conflict', 'unresolved') for r in claude))
        self.assertEqual(sum(r['format'] for r in claude), 392)

    def test_costs_and_historical_scope(self):
        costs = self.data['costs']
        self.assertEqual(len(costs), 9)
        self.assertAlmostEqual(sum(c['newUsd'] for c in costs), 14.6510573536, places=9)
        self.assertAlmostEqual(sum(c['historicalUsd'] for c in costs), 0.0036459, places=9)
        self.assertEqual(sum(c['newRecords'] for c in costs), 13289)
        self.assertTrue(all(c['newUsd'] >= 0 for c in costs))

    def test_offline_embedding_and_allowlisted_data(self):
        match = re.search(r'<script id="report-data" type="application/json">(.*?)</script>', self.html, re.S)
        self.assertIsNotNone(match)
        self.assertEqual(json.loads(match[1])['totals'], self.data['totals'])
        self.assertNotRegex(self.html, r'<(?:script|link|img)\b[^>]*(?:src|href)=[\"\x27](?:https?:)?//')
        self.assertNotIn('fetch(', self.html)
        self.assertNotIn('XMLHttpRequest', self.html)
        self.assertNotIn('innerHTML', self.html)
        self.assertNotIn('api_response', match[1])
        self.assertNotIn('Authorization', match[1])
        self.assertNotIn('OPENROUTER_API_KEY', match[1])
        self.assertNotRegex(self.html, r'sk-or-v1-[a-zA-Z0-9]{20,}')

    def test_hostile_text_stays_inert(self):
        payload = {'text': '</script><img src=x onerror=alert(1)> & <b>hello</b>'}
        html = report.render_report(payload)
        match = re.search(r'<script id="report-data" type="application/json">(.*?)</script>', html, re.S)
        self.assertNotIn('<img', match[1])
        self.assertNotIn('</script', match[1])
        self.assertEqual(json.loads(match[1]), payload)

    def test_markdown_uses_same_metrics(self):
        markdown = report.render_markdown(self.data)
        self.assertIn('13.500 registros; 13.493 decisiones extraíbles; 7 filtros', markdown)
        self.assertIn('1258 / 1500 | 83,87 %', markdown)
        self.assertIn('1493 / 1500 | 99,53 %', markdown)
        self.assertIn('USD 14,65106', markdown)
        self.assertIn('[Abrir la versión HTML interactiva](presentes-2026-11-04.html)', markdown)
        self.assertEqual(sum(line.startswith('| `HS_') for line in markdown.splitlines()), 90)
        self.assertIn('241/1000 · 24,10 %', markdown)

    def test_confusion_matrices_and_reference_switch(self):
        for dataset, expected in {
            'HS_HF_PR_500': (498, 18, 2, 982),
            'HS_LF_PR': (499, 241, 1, 759),
            'HS_NS_PR_500': (484, 2, 16, 998),
        }.items():
            v = report.case_confusion(self.data, dataset, 0)
            self.assertEqual(tuple(v[key] for key in ('tp', 'fp', 'fn', 'tn')), expected)
            self.assertEqual(v['positiveTotal'], 500)
            self.assertEqual(v['negativeTotal'], 1000)
        original = report.case_confusion(self.data, 'HS_LF_PR', 0, reference='original')
        self.assertEqual(tuple(original[key] for key in ('tp', 'fp', 'fn', 'tn')), (673, 67, 327, 433))
        canonical = report.case_confusion(self.data, 'HS_LF_PR', 0, variant='invalid')
        noncanonical = report.case_confusion(self.data, 'HS_LF_PR', 0, variant='noncanonic')
        self.assertEqual((canonical['fp'], noncanonical['fp']), (67, 174))

    def test_filtered_and_unresolved_do_not_enter_confusion_cells(self):
        v = report.case_confusion(self.data, 'HS_LF_PR', 2)
        self.assertEqual(tuple(v[key] for key in ('tp', 'fp', 'fn', 'tn', 'filtered')), (497, 0, 0, 996, 7))
        self.assertEqual(v['tp'] + v['fn'], 497)
        self.assertEqual(v['fp'] + v['tn'], 996)
        empty = report.confusion_matrix([(True, {'answer': None, 'status': 'conflict'}),
                                         (False, {'answer': None, 'status': 'filtered'})])
        self.assertEqual(sum(empty[key] for key in ('tp', 'fp', 'fn', 'tn')), 0)
        self.assertEqual((empty['filtered'], empty['unresolved']), (1, 1))

    def test_stale_audit_fails_before_building(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'prompts/systemPrompts').mkdir(parents=True)
            (root / 'prompts/userPrompts').mkdir(parents=True)
            (root / 'summaries').mkdir()
            (root / 'prompts/systemPrompts/zeroShot.json').write_text('["system"]')
            (root / 'summaries/HS_LF_PR_legacy_migration.json').write_text('{"records":[]}')
            (root / 'prompts/userPrompts/HS_HF_PR_500.json').write_text('[]')
            (root / 'summaries/HS_HF_PR_500_label_audit.json').write_text('{"dataset_sha256":"wrong","rows":[]}')
            with self.assertRaisesRegex(ValueError, 'Audit does not match'):
                report.load_report(root)


if __name__ == '__main__':
    unittest.main()

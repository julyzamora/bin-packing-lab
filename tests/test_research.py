import tempfile
import unittest
from unittest.mock import patch
from bin_packing_lab.research import exact_bins, decision, evaluate
from bin_packing_lab.problem import lower_bound

class ResearchTests(unittest.TestCase):
    def test_exact_gap_and_large_integers(self):
        case = {'capacity': [10], 'items': [[6], [6], [6]]}
        self.assertEqual(lower_bound(case), 2)
        self.assertEqual(exact_bins(case), 3)
        self.assertEqual(lower_bound({'capacity': [10**30], 'items': [[10**30], [1]]}), 2)

    def test_acceptance_requires_all_splits(self):
        def row(split, bins):
            return dict(split=split, bins=bins, status='valid',
                        baselines={'first_fit_decreasing': 5, 'best_fit_decreasing': 4})
        self.assertEqual(decision([row('development', 3), row('validation', 5)]), 'rejected-regression')
        self.assertEqual(decision([row('development', 3), row('validation', 4)]), 'eligible-for-review')
        self.assertEqual(decision([row('development', 4)]), 'tie')
        self.assertEqual(decision([{'status': 'timeout'}]), 'rejected-invalid')

    def test_invalid_candidate_and_infrastructure_evidence(self):
        tiny = {'development': {'cases': [{'id': 'x', 'capacity': [10], 'items': [[6], [6]]}]}}
        with tempfile.TemporaryDirectory() as tmp, patch('bin_packing_lab.research.suites', return_value=tiny):
            record, _ = evaluate(b'x', 'bad', tmp, trial=lambda *a: [0, 0])
            self.assertEqual(record['status'], 'rejected-invalid')
            def failure(*args):
                raise RuntimeError('runtime missing')
            with self.assertRaises(RuntimeError):
                evaluate(b'x', 'infra', tmp, trial=failure)
            import json
            from pathlib import Path
            states = [json.loads(p.read_text())['status'] for p in Path(tmp).glob('*.json')]
            self.assertIn('infrastructure-error', states)

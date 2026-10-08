import copy
import itertools
import unittest
from bin_packing_lab.problem import validate, lower_bound
from bin_packing_lab.solvers import solve, NAMES
from bin_packing_lab.leaderboard import entries


class ValidationTests(unittest.TestCase):
    def test_rejects_bad_assignments(self):
        case = {'capacity': [10, 10], 'items': [[6, 2], [6, 2]]}
        for bad in ([0], [0, 0], [False, 1], [-1, 0], [0.0, 1]):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate(case, bad)
        self.assertEqual(validate(case, [8, 9])['bins'], 2)

    def test_moves_preserve_physical_bin_ids(self):
        case = {'capacity': [10], 'items': [[4], [4]]}
        self.assertEqual(validate(case, [0, 0], [0, 1], 1)['moves'], 1)
        with self.assertRaises(ValueError):
            validate(case, [0, 0], [0, 1], 0)
        with self.assertRaises(ValueError):
            validate(case, [0, 0], max_moves=1)

    def test_capacity_bound_on_small_exhaustive_cases(self):
        for sizes in itertools.product((2, 4, 6), repeat=4):
            case = {'capacity': [10], 'items': [[x] for x in sizes]}
            optimum = 4
            for assignment in itertools.product(range(4), repeat=4):
                try:
                    optimum = min(optimum, validate(case, list(assignment))['bins'])
                except ValueError:
                    pass
            self.assertLessEqual(lower_bound(case), optimum)
            for solver in NAMES:
                result = validate(case, solve(case, solver))
                self.assertGreaterEqual(result['bins'], optimum)
                self.assertLessEqual(result['bins'], 4)

    def test_multidimensional_conflicts(self):
        case = {'capacity': [10, 10], 'items': [[8, 2], [2, 8], [8, 2], [2, 8]]}
        for solver in NAMES:
            self.assertEqual(validate(case, solve(case, solver))['bins'], 2)

    def test_failure_and_partial_run_never_rank(self):
        base = {'run_id':'x', 'comparison_group':'g', 'source_sha256':'s', 'commit':None,
                'dirty':False, 'evidence':'local-development', 'expected_cases_per_solver':2,
                'rows':[{'solver':'a', 'case':'1', 'seed':0, 'status':'valid',
                         'bins':2, 'lower_bound':1, 'wall_seconds':1}]}
        self.assertEqual(entries([base])[0]['status'], 'ineligible')
        failed = copy.deepcopy(base)
        failed['rows'].append({'solver':'a', 'case':'2', 'seed':0, 'status':'timeout',
                               'wall_seconds':2})
        self.assertIsNone(entries([failed])[0]['bins'])


if __name__ == '__main__':
    unittest.main()

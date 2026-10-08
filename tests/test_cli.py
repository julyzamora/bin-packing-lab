import argparse
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from bin_packing_lab import cli

class CLITests(unittest.TestCase):
    def test_submission_scope(self):
        self.assertEqual(cli.submission_paths(['candidates/beam/solver.py', 'research/experiments/beam.md']),
                         ['candidates/beam/solver.py'])
        for paths in ([], ['bin_packing_lab/problem.py'],
                      ['candidates/beam/solver.py', '.github/workflows/ci.yml']):
            with self.assertRaises(ValueError):
                cli.submission_paths(paths)

    def test_run_uses_checkout_and_runtime_provenance(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            p = root/'candidates/beam/solver.py'; p.parent.mkdir(parents=True); p.write_text('')
            commands = []
            def call(command, **kwargs):
                commands.append((command, kwargs))
                if command[:3] == ['docker', 'image', 'inspect']:
                    return 'sha256:test'
                if 'bin_packing_lab.research' in command:
                    import json
                    queue = json.loads(Path(command[command.index('--queue')+1]).read_text())
                    self.assertEqual(queue['experiments'][0]['candidate'], 'beam')
                    self.assertEqual(kwargs['env']['EVALUATOR_IMAGE_ID'], 'sha256:test')
            with patch.object(cli, 'checkout', return_value=root), patch.object(cli, 'call', side_effect=call):
                cli.main(['run', 'beam'])
            self.assertEqual(commands[0][0][:2], ['docker', 'build'])
            self.assertIn('--report-only', commands[-1][0])

    def test_submit_dry_run_never_pushes_or_creates_pr(self):
        commands = []
        def call(command, **kwargs):
            commands.append(command)
            if command[1:3] == ['status', '--porcelain']: return ''
            if command[1:3] == ['branch', '--show-current']: return 'candidate/beam'
            if command[1:3] == ['rev-parse', 'FETCH_HEAD']: return 'a'*40
            if command[1:3] == ['diff', '--name-only']: return 'candidates/beam/solver.py'
            if command[1:3] == ['remote', 'get-url']: return 'git@github.com:contributor/bin-packing-lab.git'
            return ''
        with patch.object(cli, 'checkout', return_value=Path('/tmp')), patch.object(cli, 'call', side_effect=call):
            cli.main(['submit', '--dry-run'])
        self.assertFalse(any(c[:2] == ['git', 'push'] or c[:3] == ['gh', 'pr', 'create'] for c in commands))

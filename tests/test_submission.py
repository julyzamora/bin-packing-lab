import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/prepare_candidates.py'

class SubmissionTests(unittest.TestCase):
    def test_extracts_source_without_execution_and_rejects_evaluator_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            def git(*args):
                return subprocess.check_output(['git', '-C', tmp, *args], stderr=subprocess.DEVNULL).decode().strip()
            git('init'); git('config', 'user.email', 'test@example.invalid'); git('config', 'user.name', 'Test')
            (root/'README').write_text('base'); git('add', '.'); git('commit', '-m', 'base')
            base = git('rev-parse', 'HEAD')
            p = root/'candidates/example/solver.py'; p.parent.mkdir(parents=True)
            p.write_text('raise RuntimeError("must not execute during extraction")')
            git('add', '.'); git('commit', '-m', 'candidate')
            env = dict(os.environ, BASE_SHA=base, HEAD_SHA=git('rev-parse', 'HEAD'))
            result = subprocess.run(['python', str(SCRIPT)], cwd=tmp, env=env, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((root/'incoming/example/solver.py').read_text(), p.read_text())
            (root/'README').write_text('tampered')
            git('add', 'README'); git('commit', '-m', 'protected change')
            env['HEAD_SHA'] = git('rev-parse', 'HEAD')
            result = subprocess.run(['python', str(SCRIPT)], cwd=tmp, env=env, capture_output=True)
            self.assertNotEqual(result.returncode, 0)

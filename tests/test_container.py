import os
import shutil
import unittest
from bin_packing_lab.research import container_trial

@unittest.skipUnless(shutil.which('docker') and os.environ.get('RUN_CONTAINER_TESTS') == '1', 'Docker unavailable; isolation tests require CI')
class ContainerTests(unittest.TestCase):
    case = {'capacity': [10], 'items': [[6], [6]]}
    def test_valid_and_isolation(self):
        source = b"""import os, socket
from pathlib import Path
def solve(instance, seed):
    assert os.getuid() != 0
    assert 'GITHUB_TOKEN' not in os.environ
    assert not Path('/var/run/docker.sock').exists()
    try:
        Path('/forbidden').write_text('x')
    except OSError:
        pass
    else:
        raise AssertionError('writable root')
    s = socket.socket(); s.settimeout(0.2)
    try:
        s.connect(('1.1.1.1', 80))
    except OSError:
        pass
    else:
        raise AssertionError('network enabled')
    return [0, 1]
"""
        self.assertEqual(container_trial(source, self.case, 0), [0, 1])
    def test_timeout_and_output_limit(self):
        with self.assertRaises(TimeoutError):
            container_trial(b'def solve(i,s):\n while True: pass', self.case, 0, timeout=1)
        with self.assertRaises(ValueError):
            container_trial(b'def solve(i,s):\n print("x"*100000)\n return [0,1]', self.case, 0)

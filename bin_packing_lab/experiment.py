import hashlib
import json
import platform
import random
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from .problem import validate, lower_bound, check_instance
from .solvers import NAMES

ROOT = Path(__file__).resolve().parents[1]


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def suite(path, seed=17, count=8):
    if count < 1:
        raise ValueError('count must be positive')
    rng, cases = random.Random(seed), []
    for dims in (1, 2, 3):
        for family in ('uniform', 'complementary', 'conflicting'):
            for index in range(count):
                items = []
                for _ in range(16):
                    if family == 'complementary':
                        x = [rng.randint(15, 85) for _ in range(dims)]
                        items.extend([x, [100-v for v in x]])
                    elif family == 'conflicting':
                        axis = rng.randrange(dims)
                        items.append([rng.randint(55, 85) if d == axis else rng.randint(1, 15)
                                      for d in range(dims)])
                    else:
                        items.append([rng.randint(1, 70) for _ in range(dims)])
                rng.shuffle(items)
                cases.append({'id': f'{dims}d-{family}-{index}', 'family': family,
                              'capacity': [100]*dims, 'items': items})
    data = {'schema': 1, 'track': 'fresh-packing', 'split': 'development',
            'generator': 'synthetic-v1', 'seed': seed, 'cases': cases}
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, indent=2)+'\n')
    return data


def source_state():
    files = {str(p.relative_to(ROOT)): p.read_text()
             for p in sorted(list((ROOT/'bin_packing_lab').glob('*.py')) +
                             list((ROOT/'evaluation').glob('*'))) if p.is_file()}
    def git(*args):
        r = subprocess.run(['git', '-C', str(ROOT), *args], capture_output=True, text=True)
        return r.stdout.strip() if r.returncode == 0 else None
    return {'source_sha256': digest(files), 'commit': git('rev-parse', 'HEAD'),
            'dirty': bool(git('status', '--porcelain', '--', 'bin_packing_lab'))}


def benchmark(suite_path, output, solvers=NAMES, timeout=2.0, seeds=(0, 1, 2)):
    if timeout <= 0 or not seeds or len(set(seeds)) != len(seeds):
        raise ValueError('positive timeout and distinct seeds required')
    data = json.loads(Path(suite_path).read_text())
    if data.get('track') != 'fresh-packing' or not data['cases']:
        raise ValueError('nonempty fresh-packing suite required')
    if len({c['id'] for c in data['cases']}) != len(data['cases']):
        raise ValueError('duplicate case IDs')
    for case in data['cases']:
        check_instance(case)
    rows = []
    environment = {'python': platform.python_version(), 'platform': platform.platform(),
                   'machine': platform.machine(), 'processor': platform.processor()}
    protocol = {'suite_sha256': digest(data), 'timeout_seconds': timeout,
                'seeds': list(seeds), 'environment': environment, 'evaluation_version': 1}
    record = {'schema': 1, 'run_id': uuid.uuid4().hex,
              'created_at': datetime.now(timezone.utc).isoformat(),
              'evidence': 'local-development', 'track': data['track'],
              **source_state(), **protocol, 'comparison_group': digest(protocol), 'rows': rows}
    destination = Path(output)
    destination.mkdir(parents=True, exist_ok=True)
    for solver in solvers:
        if solver not in NAMES:
            raise ValueError(f'unknown solver {solver}')
        for case in data['cases']:
            for seed in seeds:
                row = {'solver': solver, 'case': case['id'], 'family': case['family'],
                       'dimensions': len(case['capacity']), 'seed': seed,
                       'lower_bound': lower_bound(case)}
                start = time.perf_counter()
                try:
                    result = subprocess.run([sys.executable, '-m', 'bin_packing_lab.worker'],
                        input=json.dumps({'instance': case, 'solver': solver, 'seed': seed}),
                        text=True, capture_output=True, cwd=ROOT, timeout=timeout, check=True)
                    reply = json.loads(result.stdout)
                    row.update(validate(case, reply['assignment']))
                    row.update(status='valid', assignment=reply['assignment'])
                except subprocess.TimeoutExpired:
                    row.update(status='timeout')
                except (subprocess.CalledProcessError, ValueError, KeyError, TypeError) as exc:
                    row.update(status='invalid', error=str(exc)[:1000])
                row['wall_seconds'] = time.perf_counter()-start
                rows.append(row)
    record['expected_cases_per_solver'] = len(data['cases'])*len(seeds)
    path = destination / (record['run_id']+'.json')
    with path.open('x') as f:
        json.dump(record, f, indent=2)
        f.write('\n')
    return path

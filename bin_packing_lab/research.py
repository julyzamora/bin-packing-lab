"""Bounded, resumable evaluation of submitted hypotheses. No code generation."""
import argparse
import hashlib
import json
import os
import platform
from datetime import datetime, timezone
import re
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from .experiment import ROOT, digest, source_state, suite
from .problem import validate, lower_bound
from .solvers import solve

IMAGE = 'bin-packing-evaluator:1'
PROTOCOL = 2


def runtime():
    return {'image_id': os.environ.get('EVALUATOR_IMAGE_ID', 'unrecorded'),
            'python': platform.python_version(), 'platform': platform.platform()}


def exact_bins(case):
    """Exhaustive branch-and-bound oracle, restricted to <= 10 items."""
    if len(case['items']) > 10:
        raise ValueError('exact oracle limited to 10 items')
    cap, items = case['capacity'], case['items']
    best, loads = len(items), []
    def search(i):
        nonlocal best
        if i == len(items):
            best = min(best, len(loads)); return
        if len(loads) >= best:
            return
        seen = set()
        for b, load in enumerate(loads):
            key = tuple(load)
            if key in seen or any(a + v > c for a, v, c in zip(load, items[i], cap)):
                continue
            seen.add(key)
            loads[b] = [a + v for a, v in zip(load, items[i])]
            search(i + 1)
            loads[b] = load
        loads.append(list(items[i])); search(i + 1); loads.pop()
    search(0)
    return best


def suites():
    with tempfile.TemporaryDirectory() as tmp:
        result = {}
        for split, seed in [('development', 17), ('validation', 104729)]:
            data = suite(Path(tmp)/'suite.json', seed=seed, count=2)
            data['split'] = split
            # Larger public synthetic cases stress ordering beyond the original 16 items.
            for dims in (1, 2, 3):
                items = [[1 + ((i * 37 + d * 19 + seed) % 70) for d in range(dims)]
                         for i in range(128)]
                data['cases'].append({'id': f'{dims}d-large-{split}', 'family': 'large',
                                      'capacity': [100]*dims, 'items': items})
            result[split] = data
        result['exact'] = {'schema': 1, 'track': 'fresh-packing', 'split': 'exact', 'cases': [
            {'id': 'tiny-pairs', 'family': 'exact', 'capacity': [10],
             'items': [[6], [4], [7], [3], [5], [5]]},
            {'id': 'tiny-vector', 'family': 'exact', 'capacity': [10, 10],
             'items': [[7, 2], [2, 7], [3, 8], [8, 3], [5, 5], [5, 5]]},
            {'id': 'tiny-bound-gap', 'family': 'exact', 'capacity': [10],
             'items': [[6], [6], [6]]}]}
        return result


def container_trial(source, case, seed, timeout=5):
    """No credentials/repo mounts/network. Bounded stdout, processes, RAM and wall time."""
    name = 'packing-' + uuid.uuid4().hex
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp)/'solver.py'
        path.write_bytes(source); path.chmod(0o444)
        cmd = ['docker', 'run', '--rm', '-i', '--name', name, '--network=none',
               '--read-only', '--cap-drop=ALL', '--security-opt=no-new-privileges',
               '--pids-limit=32', '--memory=256m', '--memory-swap=256m', '--cpus=1',
               '--log-driver=none', '--tmpfs=/tmp:rw,noexec,nosuid,size=16m',
               '--mount', f'type=bind,src={path},dst=/candidate/solver.py,readonly', IMAGE]
        start = time.monotonic()
        # Poll a file rather than accumulating arbitrary candidate output in host RAM.
        with tempfile.TemporaryFile() as output:
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=output,
                                       stderr=subprocess.DEVNULL)
            try:
                process.stdin.write(json.dumps({'instance': case, 'seed': seed}).encode())
                process.stdin.close()
                while process.poll() is None:
                    if os.fstat(output.fileno()).st_size > 65536:
                        raise ValueError('candidate output exceeded 64 KiB')
                    if time.monotonic() - start > timeout:
                        raise TimeoutError('container wall-time budget exceeded')
                    time.sleep(0.02)
                if process.returncode == 125:
                    raise RuntimeError('Docker infrastructure failure')
                if process.returncode or os.fstat(output.fileno()).st_size > 65536:
                    raise ValueError('candidate execution failed or output exceeded limit')
                output.seek(0)
                return json.load(output)['assignment']
            finally:
                if process.poll() is None:
                    subprocess.run(['docker', 'rm', '-f', name], stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL, timeout=15)
                    process.kill()
                process.wait(timeout=15)


def decision(rows):
    if not rows or any(r['status'] != 'valid' for r in rows):
        return 'rejected-invalid'
    totals = {}
    for split in {r['split'] for r in rows}:
        group = [r for r in rows if r['split'] == split]
        totals[split] = (sum(r['bins'] for r in group),
                        min(sum(r['baselines'][b] for r in group)
                            for b in ('first_fit_decreasing', 'best_fit_decreasing')))
    if any(a > b for a, b in totals.values()):
        return 'rejected-regression'
    if any(a < b for a, b in totals.values()):
        return 'eligible-for-review'
    return 'tie'


def evaluate(source, candidate, output, hypothesis='', trial=container_trial):
    data = suites()
    protocol = {'evaluation_version': PROTOCOL, 'suite_sha256': digest(data),
                'timeout_seconds': 5, 'seeds': [0, 1], 'image': IMAGE, 'runtime': runtime()}
    rows = []
    record = {'schema': 1, 'run_id': uuid.uuid4().hex,
              'candidate': candidate, 'hypothesis': hypothesis,
              'created_at': datetime.now(timezone.utc).isoformat(),
              'runtime_image_id': os.environ.get('EVALUATOR_IMAGE_ID', 'unrecorded'),
              'environment': {'python': platform.python_version(), 'platform': platform.platform()},
              'expected_trials': sum(len(s['cases']) for s in data.values()) * 2,
              'candidate_sha256': hashlib.sha256(source).hexdigest(),
              **source_state(), **protocol, 'comparison_group': digest(protocol),
              'status': 'running', 'rows': rows}
    path = Path(output)/(record['run_id'] + '.json')
    path.parent.mkdir(parents=True, exist_ok=True)
    def save():
        temp = path.with_suffix('.tmp')
        temp.write_text(json.dumps(record, indent=2)+'\n'); temp.replace(path)
    save()
    try:
        for split, suite_data in data.items():
            for case in suite_data['cases']:
                baselines = {b: validate(case, solve(case, b))['bins']
                             for b in ('first_fit_decreasing', 'best_fit_decreasing')}
                optimum = exact_bins(case) if split == 'exact' else None
                for seed in protocol['seeds']:
                    row = {'case': case['id'], 'split': split, 'seed': seed,
                           'baselines': baselines, 'lower_bound': lower_bound(case),
                           'optimum': optimum}
                    start = time.monotonic()
                    try:
                        assignment = trial(source, case, seed)
                        row.update(validate(case, assignment), assignment=assignment, status='valid')
                    except TimeoutError:
                        row['status'] = 'timeout'
                    except (ValueError, KeyError, TypeError, RecursionError) as error:
                        row.update(status='invalid', error=str(error)[:500])
                    row['wall_seconds'] = time.monotonic() - start
                    rows.append(row); save()
        record['status'] = decision(rows)
    except Exception as error:
        record.update(status='infrastructure-error', error=str(error)[:500])
        raise
    finally:
        save()
    return record, path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--queue', default='research/queue.json')
    parser.add_argument('--candidates', default='candidates')
    parser.add_argument('--state', default='runs/candidates')
    parser.add_argument('--max-experiments', type=int, default=1)
    parser.add_argument('--require-improvement', action='store_true')
    parser.add_argument('--report-only', action='store_true')
    args = parser.parse_args()
    if not 1 <= args.max_experiments <= 10:
        parser.error('max-experiments must be 1..10')
    queue = json.loads(Path(args.queue).read_text())['experiments']
    seen, count, failures = set(), 0, False
    for task in queue:
        name = task['candidate']
        if not re.fullmatch(r'[a-z][a-z0-9_-]{0,63}', name) or task['id'] in seen:
            raise ValueError('invalid candidate or duplicate experiment id')
        seen.add(task['id'])
        path = Path(args.candidates)/name/'solver.py'
        if path.is_symlink() or path.parent.is_symlink() or path.stat().st_size > 65536:
            raise ValueError('candidate must be a regular source file <=64 KiB')
        source = path.read_bytes()
        key = digest({'source': source.hex(), 'task': task, 'evaluator': source_state()['source_sha256'],
                      'protocol': PROTOCOL, 'suites': suites(), 'runtime': runtime()})
        marker = Path(args.state)/(key+'.done')
        if marker.exists():
            status = json.loads(Path(marker.read_text()).read_text())['status']
        else:
            if count >= args.max_experiments:
                break
            record, result_path = evaluate(source, name, args.state, task['hypothesis'])
            status = record['status']
            marker.write_text(str(result_path.resolve())); count += 1
        print(f"{task['id']}: {status}")
        failures |= status.startswith('rejected') or (args.require_improvement and status != 'eligible-for-review')
    if failures and not args.report_only:
        raise SystemExit(1)


if __name__ == '__main__':
    main()

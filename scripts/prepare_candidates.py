"""Extract only regular candidate blobs; never check out or execute the PR tree."""
import json
import os
import re
import subprocess
from pathlib import Path

base, head = os.environ['BASE_SHA'], os.environ['HEAD_SHA']
for sha in (base, head):
    if not re.fullmatch('[0-9a-f]{40}', sha):
        raise ValueError('invalid commit SHA')
def git(*args):
    return subprocess.check_output(['git', *args])
changes = git('diff', '--name-only', '-z', base, head).decode().split('\0')
tasks = []
for path in filter(None, changes):
    match = re.fullmatch(r'candidates/([a-z][a-z0-9_-]{0,63})/solver\.py', path)
    if not match:
        if path.startswith('research/experiments/') and path.endswith('.md'):
            continue
        raise ValueError('Candidate submissions may change only candidates/<name>/solver.py and research/experiments/*.md. Submit infrastructure changes separately.')
    mode = git('ls-tree', head, '--', path).decode().split()[0]
    if mode != '100644':
        raise ValueError('candidate must be a non-executable regular blob')
    if int(git('cat-file', '-s', f'{head}:{path}')) > 65536:
        raise ValueError('candidate exceeds 64 KiB')
    target = Path('incoming')/match[1]/'solver.py'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(git('show', f'{head}:{path}'))
    tasks.append({'id': match[1], 'candidate': match[1],
                  'hypothesis': f'PR candidate at {head}; see research/experiments notes'})
if not 1 <= len(tasks) <= 3:
    raise ValueError('submit 1..3 candidate files per PR')
Path('incoming-queue.json').write_text(json.dumps({'schema': 1, 'experiments': tasks}))

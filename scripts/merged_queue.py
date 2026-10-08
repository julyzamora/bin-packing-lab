"""Build a deterministic queue of merged candidates, with a hard CI budget."""
import json
from pathlib import Path
paths = sorted(Path('candidates').glob('*/solver.py'))
if len(paths) > 10:
    raise ValueError('More than ten candidates: increase/shard the reviewed CI budget before publishing')
queue = {'schema': 1, 'experiments': [
    {'id': p.parent.name, 'candidate': p.parent.name,
     'hypothesis': 'Re-evaluate merged candidate on the current protocol'} for p in paths]}
Path('runs').mkdir(exist_ok=True)
Path('runs/merged-queue.json').write_text(json.dumps(queue))

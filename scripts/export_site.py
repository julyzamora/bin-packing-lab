"""Export actual benchmark records to the website; preserve every trial status."""
import argparse
import gzip
import json
import os
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]


def export(state, output, archive=False):
    records = {}
    paths = list((ROOT/'docs/experiments').rglob('*run*.json.gz'))
    paths += list(Path(state).glob('*.json'))
    for path in paths:
        raw = gzip.decompress(path.read_bytes()) if path.suffix == '.gz' else path.read_bytes()
        record = json.loads(raw)
        if 'rows' not in record:
            continue
        records[record['run_id']] = record
        if archive and path.suffix == '.json':
            target = ROOT/'docs/experiments/runs'/('run-'+record['run_id']+'.json.gz')
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                target.write_bytes(gzip.compress(raw, mtime=0))
    result = []
    for record in sorted(records.values(), key=lambda r: r['created_at']):
        item = {k: v for k, v in record.items() if k != 'rows'}
        item['rows'] = [{k: v for k, v in row.items() if k != 'assignment'} for row in record['rows']]
        result.append(item)
    data = {'schema':1, 'repository':'julyzamora/bin-packing-lab',
            'generated_at':datetime.now(timezone.utc).isoformat(), 'runs':result}
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(json.dumps(data, separators=(',', ':'))+'\n')
    return data


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--state', default='runs/research')
    p.add_argument('--output', default='website/data.json')
    p.add_argument('--archive', action='store_true')
    a = p.parse_args()
    d = export(a.state, a.output, a.archive)
    print(f"Exported {len(d['runs'])} real benchmark runs")

import json
import os
from pathlib import Path
lines = ['## Candidate evaluation', '', '| Candidate | Decision | Valid trials | Source |',
         '| --- | --- | --- | --- |']
for path in sorted(Path('runs/candidates').glob('*.json')):
    data = json.loads(path.read_text())
    valid = sum(r['status'] == 'valid' for r in data['rows'])
    lines.append(f"| {data['candidate']} | {data['status']} | {valid}/{len(data['rows'])} | {data['candidate_sha256'][:12]} |")
lines += ['', 'Eligible means ready for independent review, not automatically merged. Full assignments and failures are in the candidate-evidence artifact.']
text = '\n'.join(lines) + '\n'
print(text)
if os.environ.get('GITHUB_STEP_SUMMARY'):
    with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as stream:
        stream.write(text)

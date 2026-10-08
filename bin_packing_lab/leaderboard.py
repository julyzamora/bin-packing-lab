import html
import json
from collections import defaultdict
from pathlib import Path


def entries(records):
    result = []
    for record in records:
        grouped = defaultdict(list)
        for row in record['rows']:
            grouped[row['solver']].append(row)
        for solver, rows in grouped.items():
            complete = (len(rows) == record['expected_cases_per_solver'] and
                        len({(r['case'], r['seed']) for r in rows}) == len(rows))
            valid = complete and all(r['status'] == 'valid' for r in rows)
            result.append({'solver': solver, 'run': record['run_id'],
                'group': record['comparison_group'], 'source': record['source_sha256'],
                'commit': record['commit'], 'dirty': record['dirty'],
                'status': 'valid' if valid else 'ineligible', 'cases': len(rows),
                'bins': sum(r['bins'] for r in rows) if valid else None,
                'bound': sum(r['lower_bound'] for r in rows) if valid else None,
                'seconds': sum(r['wall_seconds'] for r in rows),
                'evidence': record['evidence']})
    return sorted(result, key=lambda e: (e['group'], e['status'] != 'valid',
                                         e['bins'] if e['bins'] is not None else float('inf'),
                                         e['solver'], e['run']))


def render(runs, output):
    records = [json.loads(p.read_text()) for p in sorted(Path(runs).glob('*.json'))]
    data = entries(records)
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    (out/'leaderboard.json').write_text(json.dumps(data, indent=2)+'\n')
    note = ('Synthetic development results only. Rank by total bins within a comparison group; '
            'time is reported, not used to break quality ties. The volume bound is not a proven optimum. '
            'A local validator pass is not independent CI certification. All repeated runs remain visible.')
    md = ['# Bin Packing Lab leaderboard', '', note, '']
    tables = []
    groups = defaultdict(list)
    for e in data:
        groups[e['group']].append(e)
    for group, rows in groups.items():
        md += [f'## Comparison group `{group[:12]}`', '',
               '| Rank | Algorithm | Bins | Volume bound | Wall seconds | Cases | Status | Source |',
               '| --- | --- | --- | --- | --- | --- | --- | --- |']
        trs = []
        last_bins, rank, count = None, None, 0
        for e in rows:
            if e['status'] == 'valid':
                count += 1
                if e['bins'] != last_bins:
                    rank, last_bins = count, e['bins']
                place = rank
            else:
                place = '—'
            values = [place, e['solver'], e['bins'] if e['bins'] is not None else '—',
                      e['bound'] if e['bound'] is not None else '—', f"{e['seconds']:.3f}",
                      e['cases'], e['status'], e['source'][:12]]
            md.append('| '+' | '.join(map(str, values))+' |')
            trs.append('<tr>'+''.join('<td>'+html.escape(str(v))+'</td>' for v in values)+'</tr>')
        tables.append('<h2>Comparison '+html.escape(group[:12])+'</h2><div class="scroll"><table>'
                      '<thead><tr>'+''.join('<th>'+x+'</th>' for x in
                      ('Rank','Algorithm','Bins','Volume bound','Wall seconds','Cases','Status','Source'))+
                      '</tr></thead><tbody>'+''.join(trs)+'</tbody></table></div>')
        md.append('')
    (out/'LEADERBOARD.md').write_text('\n'.join(md)+'\n')
    page = '''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bin Packing Lab · Leaderboard</title><style>
body{font:16px system-ui;background:#101827;color:#e6edf5;max-width:1100px;margin:48px auto;padding:0 24px}
h1{font-size:40px;margin-bottom:8px}h2{font-size:18px;margin-top:36px;color:#82dbc6}
p{line-height:1.7;max-width:850px;color:#adbdd1}table{border-collapse:collapse;width:100%;background:#172236}
td,th{text-align:left;padding:15px;border-bottom:1px solid #304056;font-variant-numeric:tabular-nums}
th{font-size:12px;text-transform:uppercase;color:#82dbc6}.scroll{overflow:auto}
.tag{color:#82dbc6;text-transform:uppercase;letter-spacing:2px;font-size:12px}a{color:#82dbc6}
</style><main><div class="tag">Algorithm research / Development track</div><h1>Bin Packing Lab</h1>
<p>Reproducible experiments. Feasible solutions. Visible trade-offs.</p><p>'''
    page += html.escape(note)+'</p>'+''.join(tables)+'<p>Full provenance: leaderboard.json and runs/ records.</p></main></html>'
    (out/'index.html').write_text(page)
    return data

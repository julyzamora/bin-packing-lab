# Research website

Static research dashboard inspired by ECDSA.fail: comparison metrics, bins-used chart,
quality/time chart, progress for identical comparison groups, leaderboard, and run details.

The site reads `website/data.json` from this public repository on load and refresh.
If that fetch fails, it labels and uses the bundled snapshot. No credentials are embedded.

`python scripts/export_site.py --archive` exports actual experiment records and saves
compressed raw evidence. CI runs this after benchmarking and publishes the data from a
separate job; the candidate execution job has read-only repository permissions. Old runs
remain archived. Publishing is skipped if main advances during the run; artifacts still exist.

Ranking requires complete feasible results for every instance/seed. Progress never mixes
comparison groups. A single run is shown as one observation, not fabricated history.

The deployed website has its own hosting checkout; its product source is mirrored here.
Data-only updates do not require redeploying the website. UI changes require deployment.
The website is initially owner-private; the GitHub repository and result feed are public.

There is no login, public submission endpoint, or automatic research-agent dispatcher.
Contributions currently go through repository pull requests.

# Initial development comparison

Source commit: `ce60f6b212903decc67824e485fb4ee7ad6900f6` (clean).
72 synthetic instances, three seeds, four solvers: 864 attempted case runs.
862 feasible completions and two timeouts. Randomized best fit is ineligible in this
local comparison because two cases timed out. No failures were removed or rerun.

First fit decreasing used 2,517 bins across its 216 case/seed runs; best fit decreasing
used 2,520, and first fit used 2,826. These are sums over seeds, not distinct instance counts.
The aggregate volume bound was 2,274; it is not a proven optimum. This is development
plumbing and a baseline comparison, not a new algorithm or generalization claim.

Raw assignments, timing, environment and source/suite hashes are retained in
[initial-run.json.gz](initial-run.json.gz). Inputs are in
[initial-suite.json.gz](initial-suite.json.gz). Decompress these with Python's `gzip`
or `gunzip -c`. The original run ID is retained inside the record.

The same source also passed tests and the benchmark workflow on GitHub Actions:
https://github.com/julyzamora/bin-packing-lab/actions/runs/37732505159
That run has its own artifacts and environment; this leaderboard reports the local run,
not substituted CI scores. The original CI artifacts have 30-day retention.

See [leaderboard](../../leaderboard/LEADERBOARD.md). Future independent evaluation
should use matched hardware, fresh instances, and archived permanent run evidence.

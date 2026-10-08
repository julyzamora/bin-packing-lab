# Bin Packing Lab

A separate algorithm-research repository with reproducible benchmarks and a generated leaderboard.
Organized like CoW Solver Lab, with a problem-specific evaluator and an ECDSA.fail-style
submit → validate → compare → retain loop. No CoW code or private research records are copied.

**[View leaderboard](leaderboard/LEADERBOARD.md)** · [Website source](website/) · [Research protocol](docs/research/RESEARCH_LOOP.md)
· [Architecture](docs/ARCHITECTURE.md) · [Evaluation](docs/EVALUATION.md)

## Run

Python 3.11+, standard library only:

```bash
python -m unittest discover -s tests -v
python -m bin_packing_lab synthetic data/development.json --count 8 --seed 17
python -m bin_packing_lab benchmark data/development.json --state runs/research
python -m bin_packing_lab leaderboard --state runs/research --output leaderboard
```

Open `leaderboard/index.html` directly in a browser. The dashboard is self-contained;
it needs no server, API key, or external JavaScript. Markdown works directly on GitHub.

## Included

| Component | Implemented |
| --- | --- |
| Problem | Fresh integer vector bin packing in one, two, and three dimensions |
| Baselines | First fit, first fit decreasing, best fit decreasing, randomized best fit |
| Validator | Independent assignment completeness and capacity checks; movement-cap primitive |
| Benchmarks | Uniform, complementary, and conflicting-resource synthetic instance families |
| Experiments | Fixed seeds, per-case subprocess timeout, measured end-to-end wall time, full assignments |
| Provenance | Source and suite SHA-256, commit, environment, timestamp, run identity |
| Leaderboard | All-case feasibility gate; bins under a fixed time budget; preserved failures and ties |
| CI | Read-only PR tests; benchmark artifacts on main and manual dispatch |
| Research | Direction definitions, hypothesis template, review and promotion protocol |

## Honest scope

The first leaderboard contains actual **local synthetic development runs**, not established
benchmark records or independently certified improvements. A dimension-wise volume lower
bound is reported, not called an optimal solution. Different suite hashes, budgets, seeds,
or environments get separate comparison groups. Repeated runs are never silently dropped.

The CLI executes reviewed built-in solvers. Its worker subprocess is **not a security sandbox**.
Do not run arbitrary model-generated code using this runner. Container/VM isolation,
a model-provider adapter, hidden evaluation service, and automated research-agent dispatch
are future work. No paid model calls or recurring schedules are enabled.

Initial tracks are fresh packing. The validator supports physical bin movement accounting,
but rearrangement solvers, movement-aware rankings, affinity constraints and exact/MIP
baselines are not implemented yet. See [roadmap](docs/ROADMAP.md).

## New candidate workflow

1. Start a branch/worktree and write a hypothesis in `research/experiments/`.
2. Add a solver in `bin_packing_lab/solvers.py`; preserve the evaluator contract.
3. Run feasibility tests and the identical development suite against all baselines.
4. Open a PR with source hashes, full run records, limitations, and negative results.
5. Review the exact commit and rerun on an independent runner before promotion.

The GitHub Actions workflow uploads a downloadable HTML/Markdown/JSON leaderboard.
The research website loads `website/data.json` from GitHub on open or refresh. Main-branch CI publishes updated data and compressed raw evidence automatically. A public submission API remains a separate future step.

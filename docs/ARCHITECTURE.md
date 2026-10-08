# Architecture

| CoW Solver Lab role | Bin Packing Lab path |
| --- | --- |
| Solver implementation | `bin_packing_lab/solvers.py` |
| Independent validator | `bin_packing_lab/problem.py` |
| Replay/evaluation | `bin_packing_lab/experiment.py` |
| Experiment memory | `runs/research/*.json` |
| Research agenda | `research/directions.json`, `docs/research/` |
| Competitive results | `leaderboard/` |
| CI | `.github/workflows/ci.yml` |

The current runnable loop is a bounded benchmark portfolio, not an autonomous LLM loop.
It generates assignments in child processes, measures wall time in the parent, checks
assignments independently and writes one unique run record. The dashboard reads records;
it does not accept scores from solver output.

The generalized future controller will assign hypotheses to isolated worktrees and pass
training/development feedback to a configurable coding-agent adapter. Evaluator and hidden
suite ownership remain outside candidate processes. A candidate must not control its own
test suite, promotion decision, or reported score.

Parallel workers should coordinate only experiment ownership and promotion. A worker doing
local search must not hold a global lock that prevents a beam-search experiment from running.
Keep hypothesis state and evaluation state separate. Store immutable evidence even when a
worker crashes, a candidate is invalid, or a direction fails to improve.

The current development ledger is append-only by convention on disk, not tamper-proof storage.
Public acceptance will require CI-owned provenance, evaluator hashes and a service identity.

## Candidate evaluation v2

See [submission protocol](research/SUBMISSIONS.md) for the implemented pre-merge evaluation path, restricted containers, public validation split, exact tiny-case diagnostics, bounded queue controller, and remaining repository-settings requirements. This supersedes earlier descriptions of candidate evaluation as entirely planned.

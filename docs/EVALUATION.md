# Evaluation contract v1

An instance has integer positive `capacity` and a list of nonzero nonnegative integer item
vectors. Each item must individually fit a bin. Output assigns every item index to one
nonnegative integer bin ID. All capacities are hard limits, checked with integer arithmetic.

Current track: fresh-packing. Objective: minimum total bins over the full suite under a
fixed per-instance wall-time limit. Every random seed counts; never select only lucky seeds.
All instances and seeds must complete feasibly to receive a rank. Bins tie regardless of noisy
runtime measurements. Wall time includes Python process startup and is diagnostic.

Comparison groups bind suite content, seed list, timeout, evaluator version and environment.
The source hash covers every Python source file in the package. The hardware fingerprint
is descriptive and not enough for fair cross-machine latency rankings. Use one controlled
runner for official comparisons. Changing a checker or ranking rule requires a reviewed
evaluation version bump and rerunning candidates.

The synthetic suite is fully exposed development data. It is not a holdout. Before claiming
generalization, add established instance collections with license/provenance records, reserve
fresh private test data, freeze the candidate, and evaluate outside the agent's workspace.
Do not repeatedly query a hidden test set and continue calling it held out.

The volume bound is `max_d ceil(sum_i demand[i,d] / capacity[d])`; it is generally weak
and is not necessarily achievable. Exact reference optimization is still on the roadmap.

Movement primitive: moves count changed physical bin IDs relative to a validated initial
assignment. Bin labels cannot be freely normalized in this track. Movement-aware solvers
and leaderboards are pending; v1 rejects non-fresh-packing suites.

Threat model: local reviewed Python baselines only. Process timeouts are resource controls,
not hostile-code isolation. A public submission service must use a locked evaluator, separate
build and scoring privileges, restricted candidate files, a disposable sandbox and externally
recorded results. PR CI is read-only and does not publish leaderboard rankings.

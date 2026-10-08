# Research loop

1. Select one direction and exact baseline commit.
2. State a falsifiable mechanism, expected benefit and bounded experiment.
3. Implement in a dedicated worktree. Keep exploratory branches independent.
4. Reject infeasible candidates with small counterexamples before full benchmarks.
5. Compare all candidates on matched instances, seeds and budgets.
6. Preserve assignment outputs, source/suite hashes, timeouts and negative findings.
7. Independently review and rerun the exact candidate before accepting it.
8. Retain useful quality/runtime/movement trade-offs; do not erase alternative designs.

Each task ends with evidence and a next action. A failed result can close a hypothesis;
a build failure is an infrastructure outcome, not a negative algorithm result. Distinguish
these in notes. A bounded queue evaluator is implemented; coding-agent dispatch remains unimplemented. See [submission protocol](SUBMISSIONS.md).

Suggested roles: researcher identifies a mechanism and cheap falsifier; implementer supplies
code; independent evaluator checks feasibility and matched performance. One agent may do
research and implementation, but its assertion is not independent validation.

No schedules or paid inference are configured by this repository. Add a provider adapter
and bounded controller only after the baseline evaluator is reproducible on its execution host.

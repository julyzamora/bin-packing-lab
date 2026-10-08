# Candidate research protocol

Create `candidates/<name>/solver.py` with `solve(instance, seed) -> list[int]`.
Use Python's standard library only. Each input contains integer `capacity` and
`items`; return one nonnegative bin ID per input item. Scores are computed by the
base-commit evaluator, never accepted from the candidate.

Include the mechanism and falsifier in `research/experiments/<name>.md`. Open a
candidate-only PR. Up to three candidate files (64 KiB each) plus experiment notes
are accepted per submission. Changes to workflows, validators, datasets or site
code require a separate infrastructure PR and owner review. Do not modify the
old built-in baselines to submit an algorithm.

The `Candidate evaluation / evaluate` check extracts regular source blobs from
the exact PR head SHA. It executes the evaluator and Dockerfile from the PR base
commit. Candidate code executes as an unprivileged user in a read-only container
with no network, no credentials, no Docker socket, one CPU, 256 MiB memory,
32 processes, a 16 MiB temporary filesystem and a five-second per-trial deadline.
Only one source file is mounted. Output is limited to 64 KiB. Containers share
the runner kernel: this is defense in depth, not VM-grade hostile-code isolation.
Use GitHub-hosted disposable runners, never a privileged self-hosted runner.

The matched suite has 21 development cases, 21 validation cases, and three tiny
exact-oracle cases, each evaluated with seeds 0 and 1 (90 trials per candidate).
The separate validation seed is PUBLIC, not a hidden holdout. Larger 128-item
cases supplement the original synthetic families. These are still synthetic;
standard external benchmark corpora and private final evaluation remain future work.

Eligibility requires every trial to be feasible, total bins no worse than the
better complete FFD/BFD baseline on EACH split, and a strict improvement on at
least one split. Ties are retained but do not pass the improvement gate. Tiny
exact optima are diagnostic, not a requirement to solve every tiny case optimally.
Runtime includes container startup and is diagnostic only. A passing check means
eligible for independent review; it does not merge or promote automatically.

Run locally (Docker required):

```sh
docker build -t bin-packing-evaluator:1 evaluation
python -m bin_packing_lab.research --max-experiments 1
```

The bounded controller reads `research/queue.json`, evaluates at most the requested
number of experiments, atomically saves each trial, retains failures, and resumes
completed experiments using source/task/evaluator/suite hashes. Interrupted runs
remain visible; restarting starts a fresh complete run for that experiment.
Infrastructure errors are not scientific rejections. There is no coding-agent
provider, paid inference or schedule; authors supply candidate implementations.

CI retains PR evidence for 90 days and writes a job summary. After a reviewed
candidate is merged, main CI evaluates all candidates and publishes their records
alongside the original baseline leaderboard. PR artifacts are never promoted by a
privileged `workflow_run` consumer.

Repository settings required: protect `main`, require owner code review and the
candidate evaluation check for candidate PRs. CODEOWNERS alone does not enforce
review. Branch rules must allow separate infrastructure PRs, where this
path-filtered check does not run. Prefer a ruleset scoped to candidate changes if
available; otherwise require maintainer review and explicitly verify the check.
The PR workflow definition itself is reviewable PR content, so review protection
is essential; base-checkout alone cannot enforce repository policy.

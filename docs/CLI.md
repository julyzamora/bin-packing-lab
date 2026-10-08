# binpack commands

Requires Python 3.11+, Git, and Docker for evaluation. Install GitHub CLI (`gh`)
for login and submission. Docker must be running; Linux is the CI reference host.

Install directly from this repository (the package is not published to PyPI):

```sh
pipx install 'git+https://github.com/julyzamora/bin-packing-lab.git'
binpack clone
cd bin-packing-lab
binpack run
binpack leaderboard
```

Alternatively, inside an existing clone, use a Python virtual environment and
`python -m pip install -e .`. `python -m bin_packing_lab.cli` also works without
installing the console command. The existing `python -m bin_packing_lab` commands
remain supported.

| Command | Behavior |
| --- | --- |
| `binpack clone [directory]` | Clone the public challenge repository. |
| `binpack login` | Sign in through `gh auth login`; no separate service/API key. |
| `binpack run` | Build the runtime and evaluate one queued experiment. |
| `binpack run beam` | Evaluate `candidates/beam/solver.py` with the standard protocol. |
| `binpack run --max-experiments 3` | Evaluate up to three queued experiments. |
| `binpack run beam --require-improvement` | Return a failing exit code on rejection or tie. |
| `binpack leaderboard` | Fetch published baseline and candidate results from GitHub. |
| `binpack leaderboard --local` | Read the checkout's published snapshot offline. |
| `binpack leaderboard --json` | Print complete published metrics as JSON. |
| `binpack submit --dry-run` | Validate the committed branch and preview submission; no push/PR. |
| `binpack submit` | Push the candidate branch and open or update its PR. |

`run` saves assignments and evidence under `runs/candidates/`; the existing
controller resumes matching completed experiments. Use `--no-build` only to reuse
an already-built image. Default runs report scientific rejections without treating
them as CLI failures; infrastructure errors still fail. Local runs are not CI certification.

## Submit an algorithm

Create a branch, write a candidate and research notes, then commit them:

```sh
git switch -c candidate/beam
# Implement candidates/beam/solver.py and research/experiments/beam.md
binpack run beam
git add candidates/beam/solver.py research/experiments/beam.md
git commit -m 'Evaluate beam packing candidate'
binpack login
binpack submit --dry-run
binpack submit --title 'Candidate: beam packing' --body-file research/experiments/beam.md
```

You need a writable GitHub remote. Repository collaborators can use `origin`;
external contributors should create a fork, add it as a remote, and use
`binpack submit --remote my-fork`. The command does not create forks, commits,
or merge PRs automatically. It requires a clean tree and a non-main branch with
one to three candidate files plus optional experiment notes. Existing open PRs
for that head branch are updated rather than duplicated. `--draft` opens a draft.
The dry run still checks GitHub authentication and fetches upstream main.

Submission CI uses the trusted base evaluator and determines eligibility. See
[submission protocol](research/SUBMISSIONS.md) for limits and acceptance rules.

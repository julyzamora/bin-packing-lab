# Research website on GitHub Pages

The dashboard is served from this repository's `website/` directory.
GitHub Actions performs benchmarking and publishes result data; GitHub Pages serves HTML, CSS, JavaScript and JSON.

## One-time activation

In repository Settings → Pages → Build and deployment, select **GitHub Actions** as the source.
Then run **Deploy research website** from Actions (or re-run the failed deployment).
This setting needs repository administration access and cannot be enabled by the workflow's default token.
The expected address after a successful deployment is https://julyzamora.github.io/bin-packing-lab/.

## Updates

- Website changes on main deploy directly.
- After the benchmark workflow finishes successfully, `workflow_run` deploys the latest committed data.
- This completion trigger is necessary because commits made with `GITHUB_TOKEN` do not trigger ordinary push workflows.
- PRs cannot deploy. The privileged deployment workflow checks out main, not untrusted PR artifacts, and serves static files without executing candidate code.
- Data is loaded from relative `./data.json`, so it travels with each deployment and works under the repository URL prefix.
- Benchmark evidence remains in `docs/experiments/runs/`; scores are not stored in a separate database.

The older owner-private hosted copy stays available during migration. This Pages site will be public, matching the public repository.
No secrets or private inputs are present in the website bundle. There is no submission API or agent dispatcher.

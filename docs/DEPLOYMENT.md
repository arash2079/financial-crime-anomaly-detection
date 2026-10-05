# GitHub Pages deployment

Public URL: https://arash2079.github.io/financial-crime-anomaly-detection/

1. In repository Settings → Pages → Build and deployment, select **GitHub Actions** as Source.
2. The `Deploy GitHub Pages` workflow runs on pushes to `main`, or manually from Actions.
3. Research tests, worker tests, inference parity and asset checks must pass before deployment.
4. The `github-pages` environment records the deployed URL. A successful deployment run is the release evidence; the expected URL alone does not establish availability.

All assets use relative paths so the repository subdirectory works. The published artifact is `dist/`; it contains no build credentials, server code or remote inference service. Uploaded CSVs stay in browser memory.

To roll back, revert the relevant commit on main and let the same workflow redeploy. Git history preserves earlier revisions and is separate from the current published source.

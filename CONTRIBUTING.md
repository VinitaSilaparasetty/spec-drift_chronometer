# Contributing

Thank you for your interest in the Spec-Drift Chronometer. Contributions of any size are welcome: bug reports, ideas, documentation, tests and code.

## Where to start

- **Roadmap items** are tracked as [GitHub issues](https://github.com/VinitaSilaparasetty/spec-drift_chronometer/issues). Comment on one before you start larger work, so we can agree on the approach.
- **Especially welcome:** integrations with other agent frameworks, new failure-mode tests for the benchmark, and real-world intent-file examples from public-sector or non-profit use cases.
- **Security problems** should not be reported in public issues. See [SECURITY.md](SECURITY.md).

## Running it locally

Requirements: Python 3.12+, Node.js 18+.

```bash
DEMO_MODE=true ./dev.sh          # backend on :8000, dashboard on :3000
```

Run the tests before opening a pull request:

```bash
pip install -r backend/requirements.txt pytest httpx
pytest
```

The frontend must still build:

```bash
cd frontend && npm ci && npm run build
```

Both run automatically on every pull request.

## Pull requests

- Keep each pull request focused on one change and explain why it is needed.
- Add or update tests for behaviour you change.
- Do not commit secrets, API keys or `.env` files.
- Results in `test_research/results/` back a research paper. Do not edit them by hand; regenerate them with the scripts in `test_research/` and say so in the pull request.

## Licence

By contributing, you agree that your contribution is licensed under the [Apache License 2.0](LICENSE), the licence of this project.

## Conduct

Everyone taking part is expected to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

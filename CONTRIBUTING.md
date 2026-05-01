# Contributing

Thanks for considering a contribution. This project is small and
opinionated — please skim this file and [PROGRESS.md](PROGRESS.md)
before opening a PR.

## Local setup

```bash
git clone https://github.com/CaptchaAI/captchaai-workflow-doctor.git
cd captchaai-workflow-doctor
python -m venv .venv
. .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m playwright install chromium
```

## Quality gates (must be green before pushing)

```bash
ruff check --fix .
ruff format .
mypy
pytest -m "not e2e"          # fast tier (no browser)
pytest -m e2e                # full e2e (Chromium required)
```

CI runs the same on every PR.

## Conventional commits

Use [conventional commits](https://www.conventionalcommits.org/):

```
feat(report): add HTML writer
fix(client): coerce integer captcha_id
docs: add token-lifecycle doc
test(detector): cover iframe edge case
```

The PR title becomes the merge-commit title — keep it sharp.

## Tests are non-negotiable

- Pure modules: 100% lines covered or have a documented reason not to be.
- Anything that hits Playwright belongs under `@pytest.mark.e2e` and
  must work against a fresh Chromium.
- Anything that hits the live CaptchaAI API must be gated by both
  `DOCTOR_ALLOW_REAL_API=1` and (for solves) `DOCTOR_ALLOW_REAL_SOLVE=1`.

## Secrets

Never check anything that looks like a key into git. The `gitleaks`
secrets-scan workflow will block the PR. Local `.secrets/` is
git-ignored and is the only place real keys belong.

## Profiles

New profiles must be **generic**. Site-specific profiles are kept
private. See [`docs/responsible-use.md`](docs/responsible-use.md).

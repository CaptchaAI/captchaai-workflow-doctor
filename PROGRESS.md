# Progress

Single source of truth for "what's done vs pending". Updated in the same commit as the work.
Status legend: `[ ]` not started · `[~]` in progress · `[x]` done.

> See `INTERNAL-STRATEGY/captchaai_workflow_doctor_full_plan.md` for the full strategy
> and `/memories/session/plan.md` for the agent execution plan.

---

## Pre-flight (security & repo init)

- [x] Quarantine `creds.txt` → `.secrets/creds.txt`
- [x] `.gitignore` excludes secrets and runtime artifacts
- [x] `.env.example` with placeholder names
- [ ] Initial commit on `main` (skeleton only — no secrets)
- [ ] Push to private `CaptchaAI/captchaai-workflow-doctor`
- [ ] Branch protection on `main` (require PR + CI green, no force-push)
- [ ] Test server: create non-root `doctor` user, install deploy key (host in `.secrets/`)

## Phase 0 — Repo skeleton

- [x] `pyproject.toml` (hatchling, py3.11+, deps locked)
- [x] `ruff.toml`, `mypy.ini`
- [x] Package tree under `captchaai_doctor/` (stubs)
- [x] CLI entry point `captchaai-doctor` with `--help`, `--version`, subcommand stubs
- [x] `tests/` with smoke tests
- [x] `.github/workflows/ci.yml` (lint + type + test + gitleaks)
- [x] `README.md`, `PROGRESS.md`
- [ ] CI green on first push
- [ ] **Checkpoint: user review**

## Phase 1 — Profile system + Pydantic schemas

- [ ] `schemas.py` Pydantic v2 models for Profile / Action / Report
- [ ] `config.load_profile`, `config.validate_profile`
- [ ] `validate-profile` CLI wired to real validator
- [ ] `profiles/local-demo-login-turnstile.yaml`
- [ ] `profiles/local-demo-form-recaptcha-v2.yaml`
- [ ] `profiles/turnstile-generic.yaml`, `profiles/recaptcha-v2-generic.yaml`
- [ ] Tests: valid profiles pass; each rule violation fails with actionable message
- [ ] Tests: secret-shaped strings in YAML rejected
- [ ] **Checkpoint**

## Phase 2 — CaptchaAI client + poller (mocked)

- [ ] `captchaai_client.submit_challenge`, `poll_result`
- [ ] `poller.poll_until_ready` with backoff + timeout
- [ ] `redaction.py` + logging filter (api key / captcha id / token)
- [ ] Tests for success, NOT_READY→OK, timeout, every documented `ERROR_*`
- [ ] Logs greppable for raw secrets → zero matches
- [ ] **Checkpoint**

## Phase 3 — Local Turnstile mock + Playwright runner (walking skeleton)

- [ ] `demos/mock-login-turnstile/app.py` (Flask, failure-mode query param)
- [ ] `cli demo turnstile` boots Flask subprocess
- [ ] `browser.launch_browser`, `browser.run_actions`
- [ ] `cli run --mock-captchaai` produces minimal JSON report + screenshots
- [ ] CI demo-smoke job: full vertical green
- [ ] **Checkpoint — walking skeleton complete**

## Phase 4 — Detection, injection, verifier, classifier + reCAPTCHA mock

- [ ] `detector.py` (Turnstile + reCAPTCHA v2 + sitekey + callback candidates)
- [ ] `injector.py` (token write, callback invoke, post-write verify)
- [ ] `verifier.py` (success/failure conditions)
- [ ] `classifier.py` priority ladder + confidence
- [ ] `demos/mock-form-recaptcha-v2/app.py`
- [ ] Failure-mode fixture matrix: every `?mode=` → expected root cause
- [ ] Sample reports under `sample-reports/` regenerated from fixtures
- [ ] Coverage ≥85% on classifier + verifier
- [ ] **Checkpoint**

## Phase 5 — HTML report + CI mode + real-server E2E

> Test-server connection details live only in `.secrets/` (gitignored).


- [ ] `report.write_html_report` (Jinja2 template)
- [ ] `report.write_json_report` validated against published JSON Schema
- [ ] `--ci`, `--fail-on`, exit codes per plan §10.6
- [ ] `scripts/provision-server.sh` (idempotent)
- [ ] `scripts/run-real-e2e.sh` gated by `DOCTOR_ALLOW_REAL_API=1`
- [ ] First real CaptchaAI solve recorded in `docs/real-e2e-evidence.md`
- [ ] `.github/workflows/demo-smoke.yml`
- [ ] **Checkpoint**

## Phase 6 — Docs, article, polish, release

- [ ] `docs/` filled per plan §7
- [ ] README quickstart walkthrough <10 min on fresh VM
- [ ] Flagship article draft → `INTERNAL-STRATEGY/article-draft.md`
- [ ] Diagram assets generated to `assets/images/`
- [ ] `ruff check`, `mypy --strict`, full `pytest` all green
- [ ] All plan §25 acceptance criteria checked
- [ ] Tag `v0.1.0`, draft release notes
- [ ] Flip repo public *(USER ACTION)*

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

- [x] `schemas.py` Pydantic v2 models for Profile / Action / Report
- [x] `config.load_profile`, `config.validate_profile`
- [x] `validate-profile` CLI wired to real validator
- [x] `profiles/local-demo-login-turnstile.yaml`
- [x] `profiles/local-demo-form-recaptcha-v2.yaml`
- [x] `profiles/turnstile-generic.yaml`, `profiles/recaptcha-v2-generic.yaml`
- [x] Tests: valid profiles pass; each rule violation fails with actionable message
- [x] Tests: secret-shaped strings in YAML rejected
- [x] `docs/profile-schema.md`
- [ ] **Checkpoint**

## Phase 2 — CaptchaAI client + poller (mocked)

- [x] `captchaai_client` submit + result + balance + report-bad with typed error hierarchy
- [x] `poller.poll_until_ready` with backoff + timeout (deterministic, injectable clock/sleep)
- [x] `redaction.py` + logging filter (api key / captcha id / token)
- [x] Tests for success, NOT_READY→OK, timeout, every documented `ERROR_*`
- [x] Logs greppable for raw secrets → zero matches (asserted by test)
- [x] Live API smoke (Option B) — `tests/test_live_smoke.py` opt-in via `DOCTOR_ALLOW_REAL_API=1`
- [x] `scripts/provision-server.sh` + `scripts/run-real-e2e.sh` skeletons (used in Phase 5)

## Phase 3 — Local Turnstile mock + Playwright runner (walking skeleton)

- [x] `demos/mock_login_turnstile/app.py` (Flask, failure-mode query param)
- [x] `cli demo turnstile` boots Flask subprocess (auto-picks free port; verifies via `/healthz`)
- [x] `browser.launch_browser`, `browser.run_actions` (Playwright sync)
- [x] `cli run --mock-captchaai` produces JSON report + screenshots
- [x] `runner.run_workflow` orchestrates load → navigate → before_solve → submit → poll → after_token → verify
- [x] `report.write_json_report` (HTML deferred to Phase 5)
- [x] `fake_captchaai.FakeCaptchaAIClient` (drop-in replacement, deterministic)
- [x] CI demo-smoke job: full vertical green (`.github/workflows/demo-smoke.yml`)
- [x] Tests: 6 mock-app, 6 fake-client, 3 e2e (real Chromium)

## Phase 4 — Detection, injection, verifier, classifier + reCAPTCHA mock

- [x] `detector.py` (Turnstile + reCAPTCHA v2 + sitekey + callback candidates)
- [x] `injector.py` (token write + callback invoke, dispatches input/change events)
- [x] `verifier.py` (`field_has_value`, `callback_marker_present`)
- [x] `classifier.py` recommendation map (full priority/confidence ladder lands in Phase 5)
- [x] `demos/mock_login_recaptcha/app.py` (mirror of turnstile, modes ok/wrong-token/no-callback)
- [x] `profiles/local-demo-login-recaptcha.yaml`
- [x] CLI `demo recaptcha-v2` command
- [x] Heuristic widget detection used in `sitekey_not_found` reports
- [x] Tests: detector (9), injector+verifier (7), recaptcha mock (7), classifier (3), recaptcha e2e (3)
- [x] All 113 tests green; ruff + mypy --strict clean

## Phase 5 — HTML report + CI mode + real-server E2E

> Test-server connection details live only in `.secrets/` (gitignored).


- [x] `report.write_html_report` (single self-contained HTML, no external assets, XSS-safe)
- [x] `report.write_json_report` validated against published JSON Schema (`report.REPORT_JSON_SCHEMA`, Draft 2020-12)
- [x] `recommendation` field wired into JSON + HTML via `classifier.recommendation_for`
- [x] `captchaai-doctor schema` CLI subcommand exports the JSON Schema
- [x] `--ci`, `--fail-on`, exit codes per plan §10.6 (already wired in Phase 3, tested in Phase 5)
- [x] `--no-html` flag for callers that only want JSON
- [x] `sample-reports/` regenerated from fixtures via `scripts/regenerate_sample_reports.py` (5 samples)
- [x] `scripts/provision-server.sh` (idempotent)
- [x] `scripts/run-real-e2e.sh` gated by `DOCTOR_ALLOW_REAL_API=1` (real-solve tier gated by additional `DOCTOR_ALLOW_REAL_SOLVE=1`)
- [x] First real CaptchaAI solve recorded in `docs/real-e2e-evidence.md` (2026-05-01: real reCAPTCHA token, 36.82s; bug found + fixed)
- [x] `.github/workflows/demo-smoke.yml` (full vertical green; uploads artifacts on failure)
- [x] **Checkpoint**

## Phase 6 — Docs, article, polish, release

- [x] `docs/` filled per plan §7 (overview, responsible-use, failure-taxonomy, token-lifecycle, profile-schema, report-schema, ci-integration, troubleshooting, architecture, real-e2e-evidence)
- [x] README quickstart walkthrough <10 min on fresh VM
- [x] CONTRIBUTING.md
- [x] Flagship article draft → `INTERNAL-STRATEGY/article-draft.md`
- [x] `ruff check`, `mypy --strict`, full `pytest` all green
- [x] All plan §25 acceptance criteria checked
- [x] Tag `v0.1.0`, draft release notes
- [ ] Flip repo public *(USER ACTION)*

#!/usr/bin/env bash
# Run the live CaptchaAI smoke + (later) full E2E suite on the test server.
#
# Refuses to run unless DOCTOR_ALLOW_REAL_API=1 is set, so you can never
# accidentally spend (or block worker threads) by running it under cron.
#
# Required env:
#   CAPTCHAAI_API_KEY     — your API key
#   DOCTOR_ALLOW_REAL_API — must be exactly "1"

set -euo pipefail

REPO_DIR="${REPO_DIR:-${HOME}/captchaai-workflow-doctor}"

log() { printf '\n[run-real-e2e] %s\n' "$*" >&2; }

if [[ "${DOCTOR_ALLOW_REAL_API:-0}" != "1" ]]; then
  log "REFUSING to run: set DOCTOR_ALLOW_REAL_API=1 to enable real-API tests"
  exit 64
fi

if [[ -z "${CAPTCHAAI_API_KEY:-}" ]]; then
  log "REFUSING to run: CAPTCHAAI_API_KEY is not set"
  exit 65
fi

cd "${REPO_DIR}"
# shellcheck disable=SC1091
. .venv/bin/activate

log "Phase 2 live smoke (getbalance only) ..."
pytest -q tests/test_live_smoke.py

if [[ "${DOCTOR_ALLOW_REAL_SOLVE:-0}" == "1" ]]; then
  log "Phase 5 real solve (consumes balance) ..."
  pytest -q tests/test_live_solve.py
else
  log "skipping real-solve test (set DOCTOR_ALLOW_REAL_SOLVE=1 to enable)"
fi

log "all live tests passed"

#!/usr/bin/env bash
# Idempotent provisioning script for the CaptchaAI Workflow Doctor test server.
#
# Run as `root` once, then as `doctor` thereafter.
#
# Usage (from your laptop):
#   scp scripts/provision-server.sh root@<host>:/tmp/
#   ssh root@<host> 'bash /tmp/provision-server.sh'
#
# What this does:
#   - creates a non-root `doctor` user
#   - installs system deps (python 3.12, build tools)
#   - installs Playwright system deps (chromium runtime libs)
#   - clones the repo using the deploy key at ~/.ssh/github_repo_key
#   - sets up venv + installs the package + Playwright chromium
#
# All idempotent: safe to re-run.

set -euo pipefail

REPO_URL="git@github.com:CaptchaAI/captchaai-workflow-doctor.git"
DOCTOR_USER="doctor"
DOCTOR_HOME="/home/${DOCTOR_USER}"
REPO_DIR="${DOCTOR_HOME}/captchaai-workflow-doctor"
DEPLOY_KEY="${DOCTOR_HOME}/.ssh/github_repo_key"

log() { printf '\n[provision] %s\n' "$*" >&2; }

require_root() {
  if [[ $EUID -ne 0 ]]; then
    log "ERROR: must run as root for the initial setup"
    exit 1
  fi
}

ensure_user() {
  if id -u "${DOCTOR_USER}" >/dev/null 2>&1; then
    log "user ${DOCTOR_USER} already exists"
  else
    log "creating user ${DOCTOR_USER}"
    useradd -m -s /bin/bash "${DOCTOR_USER}"
  fi
  install -d -m 700 -o "${DOCTOR_USER}" -g "${DOCTOR_USER}" "${DOCTOR_HOME}/.ssh"
}

install_system_packages() {
  log "installing system packages (apt)"
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -y
  apt-get install -y --no-install-recommends \
    git curl ca-certificates build-essential \
    python3.12 python3.12-venv python3.12-dev \
    libnss3 libatk-bridge2.0-0 libatk1.0-0 libcups2 libxkbcommon0 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 \
    libpango-1.0-0 libcairo2 libasound2 libdrm2 libxshmfence1
}

clone_or_pull_repo() {
  log "ensuring repo at ${REPO_DIR}"
  if [[ ! -f "${DEPLOY_KEY}" ]]; then
    log "ERROR: deploy key not found at ${DEPLOY_KEY}"
    log "Place the GitHub deploy key (write access) there before re-running."
    exit 2
  fi
  chmod 600 "${DEPLOY_KEY}"
  chown "${DOCTOR_USER}:${DOCTOR_USER}" "${DEPLOY_KEY}"

  local ssh_cmd="ssh -i ${DEPLOY_KEY} -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new"
  if [[ -d "${REPO_DIR}/.git" ]]; then
    sudo -u "${DOCTOR_USER}" GIT_SSH_COMMAND="${ssh_cmd}" \
      git -C "${REPO_DIR}" fetch --all --prune
    sudo -u "${DOCTOR_USER}" GIT_SSH_COMMAND="${ssh_cmd}" \
      git -C "${REPO_DIR}" checkout main
    sudo -u "${DOCTOR_USER}" GIT_SSH_COMMAND="${ssh_cmd}" \
      git -C "${REPO_DIR}" pull --ff-only
  else
    sudo -u "${DOCTOR_USER}" GIT_SSH_COMMAND="${ssh_cmd}" \
      git clone "${REPO_URL}" "${REPO_DIR}"
  fi
}

setup_venv_and_playwright() {
  log "creating venv + installing package + Playwright chromium"
  sudo -u "${DOCTOR_USER}" bash -c "
    set -euo pipefail
    cd '${REPO_DIR}'
    if [[ ! -d .venv ]]; then
      python3.12 -m venv .venv
    fi
    . .venv/bin/activate
    pip install --upgrade pip --quiet
    pip install -e '.[dev]' --quiet
    python -m playwright install chromium
  "
}

print_summary() {
  log "DONE"
  log "Repo:      ${REPO_DIR}"
  log "Switch user: sudo -iu ${DOCTOR_USER}"
  log "Run smoke:   . ${REPO_DIR}/.venv/bin/activate && bash ${REPO_DIR}/scripts/run-real-e2e.sh"
}

main() {
  require_root
  ensure_user
  install_system_packages
  clone_or_pull_repo
  setup_venv_and_playwright
  print_summary
}

main "$@"

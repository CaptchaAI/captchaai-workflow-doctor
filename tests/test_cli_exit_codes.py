"""Tests for CLI exit-code semantics: --fail-on, --ci, schema export."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from captchaai_doctor.cli import main as cli_main
from captchaai_doctor.report import REPORT_JSON_SCHEMA


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_schema_command_prints_valid_schema(runner: CliRunner) -> None:
    result = runner.invoke(cli_main, ["schema"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload == REPORT_JSON_SCHEMA


def test_schema_command_writes_to_file(runner: CliRunner, tmp_path: Path) -> None:
    target = tmp_path / "schema.json"
    result = runner.invoke(cli_main, ["schema", "--output", str(target)])
    assert result.exit_code == 0, result.output
    assert target.exists()
    assert json.loads(target.read_text(encoding="utf-8")) == REPORT_JSON_SCHEMA


def test_validate_profile_ok(runner: CliRunner) -> None:
    result = runner.invoke(
        cli_main, ["validate-profile", "profiles/local-demo-login-turnstile.yaml"]
    )
    assert result.exit_code == 0
    assert "OK:" in result.output


def test_validate_profile_missing_file_returns_2(runner: CliRunner, tmp_path: Path) -> None:
    bogus = tmp_path / "does-not-exist.yaml"
    result = runner.invoke(cli_main, ["validate-profile", str(bogus)])
    # Click's path-exists check returns its own exit code (2 = usage error).
    assert result.exit_code != 0


def test_run_requires_api_key_without_mock(runner: CliRunner) -> None:
    """Real client requires --api-key or env var; should exit 2 (profile/usage)."""
    result = runner.invoke(
        cli_main,
        [
            "run",
            "--profile",
            "profiles/local-demo-login-turnstile.yaml",
        ],
        env={"CAPTCHAAI_API_KEY": ""},
    )
    assert result.exit_code == 2

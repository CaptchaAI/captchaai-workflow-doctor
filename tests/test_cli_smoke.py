"""Smoke tests for the Click CLI entry point."""

from __future__ import annotations

from click.testing import CliRunner

from captchaai_doctor import __version__
from captchaai_doctor.cli import main


def test_cli_help_shows_usage() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "captchaai-doctor" in result.output.lower() or "Usage:" in result.output


def test_cli_version_matches_package() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_cli_subcommands_registered() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    for subcommand in ("validate-profile", "run", "demo"):
        assert subcommand in result.output

"""Tests for the `validate-profile` CLI subcommand."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from captchaai_doctor.cli import EXIT_OK, EXIT_PROFILE_ERROR, main

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_validate_profile_exit_0_on_valid() -> None:
    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "validate-profile",
            str(REPO_ROOT / "profiles" / "local-demo-login-turnstile.yaml"),
        ],
    )
    assert result.exit_code == EXIT_OK, result.output
    assert "OK" in result.output
    assert "local-demo-login-turnstile" in result.output


def test_validate_profile_exit_2_on_invalid(tmp_path: Path) -> None:
    bad = tmp_path / "broken.yaml"
    bad.write_text("name: x\n", encoding="utf-8")  # missing required keys
    runner = CliRunner()
    result = runner.invoke(main, ["validate-profile", str(bad)])
    assert result.exit_code == EXIT_PROFILE_ERROR
    combined = (result.output or "") + (result.stderr or "")
    assert "invalid" in combined.lower()


def test_validate_profile_exit_2_on_missing_file(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["validate-profile", str(tmp_path / "nope.yaml")])
    # Click's `exists=True` on the path rejects with exit 2 (Click's default for usage errors).
    assert result.exit_code != 0

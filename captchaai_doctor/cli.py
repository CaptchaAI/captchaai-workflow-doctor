"""Command-line entry point for `captchaai-doctor`."""

from __future__ import annotations

import click

from captchaai_doctor import __version__


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=__version__, prog_name="captchaai-doctor")
def main() -> None:
    """Diagnose CAPTCHA-solving workflows from API request to browser acceptance."""


@main.command("validate-profile")
@click.argument("profile_path", type=click.Path(exists=True, dir_okay=False))
def validate_profile(profile_path: str) -> None:
    """Validate a workflow profile YAML against the schema. (stub — Phase 1)"""
    click.echo(f"validate-profile: {profile_path} (not implemented yet)")
    raise click.exceptions.Exit(0)


@main.command("run")
@click.option(
    "--profile", "profile_path", required=True, type=click.Path(exists=True, dir_okay=False)
)
@click.option("--api-key", envvar="CAPTCHAAI_API_KEY", default=None)
@click.option("--output", "output_path", type=click.Path(dir_okay=False), default=None)
@click.option("--json", "json_path", type=click.Path(dir_okay=False), default=None)
@click.option("--headed", is_flag=True, default=False)
@click.option(
    "--mock-captchaai",
    is_flag=True,
    default=False,
    help="Use a mocked CaptchaAI client (no real API hits).",
)
@click.option("--ci", is_flag=True, default=False)
@click.option(
    "--fail-on", "fail_on", default="", help="Comma-separated root causes that should fail CI."
)
def run(
    profile_path: str,
    api_key: str | None,
    output_path: str | None,
    json_path: str | None,
    headed: bool,
    mock_captchaai: bool,
    ci: bool,
    fail_on: str,
) -> None:
    """Run the diagnostic workflow against a profile. (stub — Phase 3)"""
    _ = (api_key, output_path, json_path, headed, mock_captchaai, ci, fail_on)
    click.echo(f"run: {profile_path} (not implemented yet)")
    raise click.exceptions.Exit(0)


@main.group("demo")
def demo() -> None:
    """Run a local demo target (stub — Phase 3)."""


@demo.command("turnstile")
def demo_turnstile() -> None:
    """Start the local Turnstile-like mock app. (stub — Phase 3)"""
    click.echo("demo turnstile (not implemented yet)")


@demo.command("recaptcha-v2")
def demo_recaptcha_v2() -> None:
    """Start the local reCAPTCHA-v2-like mock app. (stub — Phase 4)"""
    click.echo("demo recaptcha-v2 (not implemented yet)")


if __name__ == "__main__":  # pragma: no cover
    main()

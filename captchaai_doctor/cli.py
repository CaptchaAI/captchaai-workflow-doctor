"""Command-line entry point for `captchaai-doctor`."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import click
from rich.console import Console

from captchaai_doctor import __version__
from captchaai_doctor.config import ProfileError, load_profile

# Exit codes per docs/profile-schema.md (mirrors plan §10.6).
EXIT_OK = 0
EXIT_WORKFLOW_FAILED = 1
EXIT_PROFILE_ERROR = 2

_err_console = Console(stderr=True)


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=__version__, prog_name="captchaai-doctor")
def main() -> None:
    """Diagnose CAPTCHA-solving workflows from API request to browser acceptance."""


@main.command("validate-profile")
@click.argument("profile_path", type=click.Path(exists=True, dir_okay=False))
def validate_profile(profile_path: str) -> None:
    """Validate a workflow profile YAML against the schema."""
    try:
        profile = load_profile(profile_path)
    except ProfileError as exc:
        _err_console.print(f"[red]profile invalid:[/red]\n{exc}")
        raise click.exceptions.Exit(EXIT_PROFILE_ERROR) from exc
    click.echo(f"OK: {profile.name} ({profile.captcha_type}) -> {profile.target.url}")


@main.command("schema")
@click.option(
    "--output",
    "output_path",
    type=click.Path(dir_okay=False),
    default=None,
    help="Write schema to this file instead of stdout.",
)
def schema(output_path: str | None) -> None:
    """Print the JSON Schema for the run report (machine-consumable)."""
    import json

    from captchaai_doctor.report import REPORT_JSON_SCHEMA, write_schema

    if output_path:
        path = write_schema(output_path)
        click.echo(str(path))
    else:
        click.echo(json.dumps(REPORT_JSON_SCHEMA, indent=2, sort_keys=True))


@main.command("run")
@click.option(
    "--profile", "profile_path", required=True, type=click.Path(exists=True, dir_okay=False)
)
@click.option("--api-key", envvar="CAPTCHAAI_API_KEY", default=None)
@click.option(
    "--artifact-dir",
    "artifact_dir",
    type=click.Path(file_okay=False),
    default="run-artifacts",
    show_default=True,
)
@click.option(
    "--json",
    "json_path",
    type=click.Path(dir_okay=False),
    default=None,
    help="Write the JSON report to this path (defaults to <artifact-dir>/report.json).",
)
@click.option(
    "--html",
    "html_path",
    type=click.Path(dir_okay=False),
    default=None,
    help="Write a self-contained HTML report to this path (defaults to <artifact-dir>/report.html).",
)
@click.option("--no-html", is_flag=True, default=False, help="Skip HTML report generation.")
@click.option("--headed", is_flag=True, default=False)
@click.option(
    "--mock-captchaai",
    is_flag=True,
    default=False,
    help="Use a mocked CaptchaAI client (no real API hits, no spend).",
)
@click.option("--ci", is_flag=True, default=False, help="Machine-readable output for CI.")
@click.option(
    "--fail-on",
    "fail_on",
    default="",
    help="Comma-separated root causes that should exit non-zero (default: any failure).",
)
def run(
    profile_path: str,
    api_key: str | None,
    artifact_dir: str,
    json_path: str | None,
    html_path: str | None,
    no_html: bool,
    headed: bool,
    mock_captchaai: bool,
    ci: bool,
    fail_on: str,
) -> None:
    """Run the diagnostic workflow against a profile."""
    # Imports kept local so `--help` and `validate-profile` don't pull in
    # Playwright (which is heavy and not always installed in CI lint jobs).
    import contextlib

    from captchaai_doctor.captchaai_client import CaptchaAIClient
    from captchaai_doctor.fake_captchaai import FakeCaptchaAIClient, make_fake_client
    from captchaai_doctor.report import write_html_report, write_json_report
    from captchaai_doctor.runner import run_workflow

    try:
        profile = load_profile(profile_path)
    except ProfileError as exc:
        _err_console.print(f"[red]profile invalid:[/red]\n{exc}")
        raise click.exceptions.Exit(EXIT_PROFILE_ERROR) from exc

    if mock_captchaai:
        client: CaptchaAIClient | FakeCaptchaAIClient = make_fake_client()
    else:
        if not api_key:
            _err_console.print(
                "[red]--api-key (or CAPTCHAAI_API_KEY env) is required unless --mock-captchaai is set[/red]"
            )
            raise click.exceptions.Exit(EXIT_PROFILE_ERROR)
        client = CaptchaAIClient(api_key=api_key, config=profile.captchaai)

    artifacts = Path(artifact_dir)
    json_target = Path(json_path) if json_path else artifacts / "report.json"

    try:
        result = run_workflow(profile, client=client, artifact_dir=artifacts, headed=headed)
    finally:
        if hasattr(client, "close"):
            with contextlib.suppress(Exception):
                client.close()

    write_json_report(result, json_target)
    html_target: Path | None = None
    if not no_html:
        html_target = Path(html_path) if html_path else artifacts / "report.html"
        write_html_report(result, html_target)

    if ci:
        line = (
            f"status={result.status} root_cause={result.root_cause} "
            f"duration={result.duration_seconds}s report={json_target}"
        )
        if html_target is not None:
            line += f" html={html_target}"
        click.echo(line)
    else:
        click.echo(f"\nReport: {json_target}")
        if html_target is not None:
            click.echo(f"HTML:   {html_target}")
        click.echo(f"Status: {result.status}  Root cause: {result.root_cause}")
        if result.detail:
            click.echo(f"Detail: {result.detail}")

    fail_on_set = {x.strip() for x in fail_on.split(",") if x.strip()}
    if result.status == "success":
        raise click.exceptions.Exit(EXIT_OK)
    if fail_on_set and result.root_cause not in fail_on_set:
        raise click.exceptions.Exit(EXIT_OK)
    raise click.exceptions.Exit(EXIT_WORKFLOW_FAILED)


@main.group("demo")
def demo() -> None:
    """Run a local demo target end-to-end with a mocked CAPTCHA solver."""


@demo.command("turnstile")
@click.option(
    "--profile",
    "profile_path",
    type=click.Path(exists=True, dir_okay=False),
    default="profiles/local-demo-login-turnstile.yaml",
    show_default=True,
)
@click.option(
    "--port",
    type=int,
    default=0,
    help="Bind the mock app to this port (0 = pick a free one).",
)
@click.option("--headed", is_flag=True, default=False)
@click.option(
    "--artifact-dir", type=click.Path(file_okay=False), default="run-artifacts/demo-turnstile"
)
def demo_turnstile(profile_path: str, port: int, headed: bool, artifact_dir: str) -> None:
    """Boot the local mock Turnstile login app and run the workflow against it."""
    _run_demo(
        app_module="demos.mock_login_turnstile.app",
        profile_path=profile_path,
        port=port,
        headed=headed,
        artifact_dir=artifact_dir,
    )


@demo.command("turnstile-invisible")
@click.option(
    "--profile",
    "profile_path",
    type=click.Path(exists=True, dir_okay=False),
    default="profiles/local-demo-login-turnstile-invisible.yaml",
    show_default=True,
)
@click.option(
    "--port",
    type=int,
    default=0,
    help="Bind the mock app to this port (0 = pick a free one).",
)
@click.option("--headed", is_flag=True, default=False)
@click.option(
    "--artifact-dir",
    type=click.Path(file_okay=False),
    default="run-artifacts/demo-turnstile-invisible",
)
def demo_turnstile_invisible(profile_path: str, port: int, headed: bool, artifact_dir: str) -> None:
    """Boot the local mock Turnstile login app in invisible mode and run the workflow."""
    _run_demo(
        app_module="demos.mock_login_turnstile.app",
        profile_path=profile_path,
        port=port,
        headed=headed,
        artifact_dir=artifact_dir,
        demo_path="/login?widget=invisible",
    )


@demo.command("recaptcha-v2")
@click.option(
    "--profile",
    "profile_path",
    type=click.Path(exists=True, dir_okay=False),
    default="profiles/local-demo-login-recaptcha.yaml",
    show_default=True,
)
@click.option(
    "--port",
    type=int,
    default=0,
    help="Bind the mock app to this port (0 = pick a free one).",
)
@click.option("--headed", is_flag=True, default=False)
@click.option(
    "--artifact-dir", type=click.Path(file_okay=False), default="run-artifacts/demo-recaptcha"
)
def demo_recaptcha_v2(profile_path: str, port: int, headed: bool, artifact_dir: str) -> None:
    """Boot the local mock reCAPTCHA-v2-like login app and run the workflow against it."""
    _run_demo(
        app_module="demos.mock_login_recaptcha.app",
        profile_path=profile_path,
        port=port,
        headed=headed,
        artifact_dir=artifact_dir,
    )


@demo.command("recaptcha-v3")
@click.option(
    "--profile",
    "profile_path",
    type=click.Path(exists=True, dir_okay=False),
    default="profiles/local-demo-form-recaptcha-v3.yaml",
    show_default=True,
)
@click.option(
    "--port",
    type=int,
    default=0,
    help="Bind the mock app to this port (0 = pick a free one).",
)
@click.option("--headed", is_flag=True, default=False)
@click.option(
    "--artifact-dir", type=click.Path(file_okay=False), default="run-artifacts/demo-recaptcha-v3"
)
def demo_recaptcha_v3(profile_path: str, port: int, headed: bool, artifact_dir: str) -> None:
    """Boot the local mock reCAPTCHA-v3 contact form and run the workflow against it."""
    _run_demo(
        app_module="demos.mock_form_recaptcha_v3.app",
        profile_path=profile_path,
        port=port,
        headed=headed,
        artifact_dir=artifact_dir,
        demo_path="/contact",
        env_overrides={"QA_NAME": "demo-user", "QA_MESSAGE": "hello from doctor"},
    )


@demo.command("cloudflare-challenge")
@click.option(
    "--profile",
    "profile_path",
    type=click.Path(exists=True, dir_okay=False),
    default="profiles/local-demo-cloudflare-challenge.yaml",
    show_default=True,
)
@click.option(
    "--port",
    type=int,
    default=0,
    help="Bind the mock app to this port (0 = pick a free one).",
)
@click.option("--headed", is_flag=True, default=False)
@click.option(
    "--artifact-dir",
    type=click.Path(file_okay=False),
    default="run-artifacts/demo-cloudflare-challenge",
)
def demo_cloudflare_challenge(
    profile_path: str, port: int, headed: bool, artifact_dir: str
) -> None:
    """Boot the local mock Cloudflare-challenge target and run the workflow against it.

    Uses the in-process fake CaptchaAI client; the fake returns a JSON
    clearance payload (cf_clearance cookie + matching User-Agent) that the
    runner replays via the ``apply_clearance_cookie`` action.
    """
    from captchaai_doctor.fake_captchaai import fake_cf_clearance_payload

    _run_demo(
        app_module="demos.mock_cloudflare_challenge.app",
        profile_path=profile_path,
        port=port,
        headed=headed,
        artifact_dir=artifact_dir,
        demo_path="/protected",
        fake_client_token=fake_cf_clearance_payload(),
    )


def _run_demo(
    *,
    app_module: str,
    profile_path: str,
    port: int,
    headed: bool,
    artifact_dir: str,
    demo_path: str = "/login",
    env_overrides: dict[str, str] | None = None,
    fake_client_token: str | None = None,
) -> None:
    """Shared runner for ``demo turnstile`` and ``demo recaptcha-v2``."""
    if port == 0:
        port = _pick_free_port()
    elif not _port_is_free("127.0.0.1", port):
        _err_console.print(
            f"[red]port 127.0.0.1:{port} is already in use; pick another or pass --port 0[/red]"
        )
        raise click.exceptions.Exit(EXIT_WORKFLOW_FAILED)

    proc = _spawn_demo_app(app_module, port=port)
    try:
        if not _wait_for_healthz("127.0.0.1", port, timeout_seconds=10):
            _err_console.print(
                f"[red]demo app did not respond on /healthz at 127.0.0.1:{port}[/red]"
            )
            raise click.exceptions.Exit(EXIT_WORKFLOW_FAILED)
        os.environ.setdefault("QA_EMAIL", "demo@example.com")
        os.environ.setdefault("QA_PASSWORD", "demo-pass")
        for k, v in (env_overrides or {}).items():
            os.environ.setdefault(k, v)

        try:
            profile = load_profile(profile_path)
        except ProfileError as exc:
            _err_console.print(f"[red]profile invalid:[/red]\n{exc}")
            raise click.exceptions.Exit(EXIT_PROFILE_ERROR) from exc
        new_url = f"http://127.0.0.1:{port}{demo_path}"
        profile = profile.model_copy(
            update={"target": profile.target.model_copy(update={"url": new_url})}
        )

        from captchaai_doctor.fake_captchaai import FAKE_OK_TOKEN, make_fake_client
        from captchaai_doctor.report import write_html_report, write_json_report
        from captchaai_doctor.runner import run_workflow

        artifacts = Path(artifact_dir)
        client = make_fake_client(token=fake_client_token or FAKE_OK_TOKEN)
        result = run_workflow(profile, client=client, artifact_dir=artifacts, headed=headed)
        write_json_report(result, artifacts / "report.json")
        write_html_report(result, artifacts / "report.html")
        click.echo(f"\nReport: {artifacts / 'report.json'}")
        click.echo(f"HTML:   {artifacts / 'report.html'}")
        click.echo(f"Status: {result.status}  Root cause: {result.root_cause}")
        if result.detail:
            click.echo(f"Detail: {result.detail}")
        if result.status != "success":
            raise click.exceptions.Exit(EXIT_WORKFLOW_FAILED)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:  # pragma: no cover
            proc.kill()


def _spawn_demo_app(module: str, *, port: int) -> subprocess.Popen[bytes]:
    """Spawn the demo Flask app as a child process bound to ``port``."""
    env = os.environ.copy()
    env["FLASK_APP"] = module
    cmd = [
        sys.executable,
        "-m",
        "flask",
        "--app",
        module,
        "run",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
    ]
    return subprocess.Popen(cmd, env=env)


def _wait_for_port(host: str, port: int, *, timeout_seconds: float) -> bool:
    """Poll ``host:port`` until the TCP port accepts connections or timeout."""
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.2)
    return False


def _pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _port_is_free(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.3):
            return False
    except OSError:
        return True


def _wait_for_healthz(host: str, port: int, *, timeout_seconds: float) -> bool:
    """Confirm our mock app (and not some other service) is on host:port."""
    import http.client

    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            conn = http.client.HTTPConnection(host, port, timeout=0.5)
            conn.request("GET", "/healthz")
            resp = conn.getresponse()
            body = resp.read()
            conn.close()
            if resp.status == 200 and body == b"ok":
                return True
        except Exception:
            pass
        time.sleep(0.2)
    return False


if __name__ == "__main__":  # pragma: no cover
    main()

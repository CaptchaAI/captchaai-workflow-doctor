"""Tests for the report writers — JSON, HTML, JSON Schema."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from captchaai_doctor.classifier import recommendation_for
from captchaai_doctor.report import (
    REPORT_JSON_SCHEMA,
    write_html_report,
    write_json_report,
    write_schema,
)
from captchaai_doctor.runner import RunResult


def _result(**overrides: object) -> RunResult:
    base = dict(
        profile_name="test-profile",
        captcha_type="turnstile",
        target_url="http://127.0.0.1:8765/login",
        started_at="2026-04-30T21:00:00Z",
        ended_at="2026-04-30T21:00:10Z",
        duration_seconds=10.0,
        status="success",
        root_cause="ok",
        detail=None,
        captcha_id_redacted="abcd****",
        poll_attempts=2,
        poll_seconds=4.0,
        sitekey_found="0xABC",
        screenshots=[],
        action_steps=[
            {"type": "fill", "selector": "input[name='email']", "succeeded": True, "detail": None}
        ],
    )
    base.update(overrides)
    return RunResult(**base)  # type: ignore[arg-type]


def test_schema_is_valid_draft_2020_12() -> None:
    Draft202012Validator.check_schema(REPORT_JSON_SCHEMA)


def test_json_report_validates_against_schema(tmp_path: Path) -> None:
    out = write_json_report(_result(), tmp_path / "report.json")
    payload = json.loads(out.read_text(encoding="utf-8"))
    Draft202012Validator(REPORT_JSON_SCHEMA).validate(payload)


def test_json_report_includes_recommendation(tmp_path: Path) -> None:
    out = write_json_report(_result(), tmp_path / "report.json")
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["recommendation"] == recommendation_for("ok")


def test_json_report_failure_validates(tmp_path: Path) -> None:
    out = write_json_report(
        _result(status="failure", root_cause="sitekey_not_found", detail="boom"),
        tmp_path / "report.json",
    )
    payload = json.loads(out.read_text(encoding="utf-8"))
    Draft202012Validator(REPORT_JSON_SCHEMA).validate(payload)
    assert payload["root_cause"] == "sitekey_not_found"
    assert "sitekey" in payload["recommendation"].lower()


def test_html_report_self_contained(tmp_path: Path) -> None:
    """No external CSS/JS/font references."""
    out = write_html_report(_result(), tmp_path / "report.html")
    text = out.read_text(encoding="utf-8")
    assert "<html" in text
    assert "test-profile" in text
    assert "SUCCESS" in text  # badge text
    # No remote URLs that would break offline viewing.
    for forbidden in ("https://fonts.googleapis", "https://cdn.", "<script src="):
        assert forbidden not in text, f"found external resource {forbidden!r}"


def test_html_report_renders_recommendation(tmp_path: Path) -> None:
    out = write_html_report(
        _result(status="failure", root_cause="callback_not_invoked"),
        tmp_path / "report.html",
    )
    text = out.read_text(encoding="utf-8")
    assert "callback" in text.lower()
    assert "FAILURE" in text


def test_html_report_links_screenshots_relative(tmp_path: Path) -> None:
    # Place a fake screenshot under the same dir as the HTML.
    shot = tmp_path / "shot.png"
    shot.write_bytes(b"\x89PNG\r\n\x1a\nfakebytes")
    out = write_html_report(_result(screenshots=[str(shot)]), tmp_path / "report.html")
    text = out.read_text(encoding="utf-8")
    assert 'src="shot.png"' in text


def test_html_report_escapes_user_strings(tmp_path: Path) -> None:
    """HTML escaping defends against XSS-by-detail-string."""
    out = write_html_report(
        _result(detail="<img src=x onerror=alert(1)>"), tmp_path / "report.html"
    )
    text = out.read_text(encoding="utf-8")
    assert "<img src=x" not in text
    assert "&lt;img src=x" in text


def test_write_schema_matches_inline_schema(tmp_path: Path) -> None:
    out = write_schema(tmp_path / "schema.json")
    on_disk = json.loads(out.read_text(encoding="utf-8"))
    assert on_disk == REPORT_JSON_SCHEMA


def test_action_step_with_null_selector_validates(tmp_path: Path) -> None:
    out = write_json_report(
        _result(
            action_steps=[{"type": "wait", "selector": None, "succeeded": True, "detail": None}]
        ),
        tmp_path / "report.json",
    )
    payload = json.loads(out.read_text(encoding="utf-8"))
    Draft202012Validator(REPORT_JSON_SCHEMA).validate(payload)


@pytest.mark.parametrize(
    "bad_status",
    ["pending", "OK", "Success", ""],
)
def test_invalid_status_fails_schema(bad_status: str, tmp_path: Path) -> None:
    """Schema must reject unknown status enums."""
    payload = _result().to_dict()
    payload["recommendation"] = recommendation_for("ok")
    payload["status"] = bad_status
    validator = Draft202012Validator(REPORT_JSON_SCHEMA)
    errors = list(validator.iter_errors(payload))
    assert errors, "schema should have rejected status=" + repr(bad_status)

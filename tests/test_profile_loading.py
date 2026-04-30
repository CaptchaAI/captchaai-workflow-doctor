"""Tests for `captchaai_doctor.config.load_profile` + Pydantic schema."""

from __future__ import annotations

from pathlib import Path

import pytest

from captchaai_doctor.config import ProfileError, load_profile

REPO_ROOT = Path(__file__).resolve().parents[1]
PROFILES_DIR = REPO_ROOT / "profiles"

VALID_TURNSTILE_YAML = """
name: my-test
captcha_type: turnstile
target:
  url: "http://127.0.0.1:8765/login"
  allowed_domains: ["127.0.0.1"]
detection:
  response_field_selector: "textarea[name='cf-turnstile-response']"
actions:
  before_solve:
    - type: fill
      selector: "input[name='email']"
      value_env: "QA_EMAIL"
  after_token:
    - type: inject_token
      selector: "textarea[name='cf-turnstile-response']"
    - type: click
      selector: "button[type='submit']"
success:
  url_contains: ["/dashboard"]
failure:
  any_text: ["captcha verification failed"]
"""


def _write(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "profile.yaml"
    p.write_text(content, encoding="utf-8")
    return p


# --- Happy path ------------------------------------------------------------


def test_shipped_profiles_all_load() -> None:
    """Every YAML under profiles/ must parse + validate."""
    files = sorted(PROFILES_DIR.glob("*.yaml"))
    assert files, "no profiles found in profiles/ — broken test setup"
    for f in files:
        profile = load_profile(f)
        assert profile.name
        assert profile.captcha_type in (
            "turnstile",
            "recaptcha_v2",
            "recaptcha_v3",
            "cloudflare_challenge",
        )


def test_minimal_valid_profile(tmp_path: Path) -> None:
    p = _write(tmp_path, VALID_TURNSTILE_YAML)
    profile = load_profile(p)
    assert profile.name == "my-test"
    assert profile.captcha_type == "turnstile"
    assert str(profile.target.url).startswith("http://127.0.0.1")
    assert len(profile.actions.after_token) == 2


# --- File-level errors -----------------------------------------------------


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ProfileError, match="not found"):
        load_profile(tmp_path / "does-not-exist.yaml")


def test_invalid_yaml(tmp_path: Path) -> None:
    p = _write(tmp_path, "name: [unclosed\n")
    with pytest.raises(ProfileError, match="invalid YAML"):
        load_profile(p)


def test_top_level_must_be_mapping(tmp_path: Path) -> None:
    p = _write(tmp_path, "- just\n- a\n- list\n")
    with pytest.raises(ProfileError, match="mapping"):
        load_profile(p)


def test_empty_file(tmp_path: Path) -> None:
    p = _write(tmp_path, "")
    with pytest.raises(ProfileError, match="mapping"):
        load_profile(p)


# --- Schema-rule violations ------------------------------------------------


def test_target_host_must_be_in_allowed_domains(tmp_path: Path) -> None:
    bad = VALID_TURNSTILE_YAML.replace("127.0.0.1", "evil.example.com", 1)
    p = _write(tmp_path, bad)
    with pytest.raises(ProfileError, match="allowed_domains"):
        load_profile(p)


def test_unsupported_captcha_type(tmp_path: Path) -> None:
    bad = VALID_TURNSTILE_YAML.replace("captcha_type: turnstile", "captcha_type: friendly_captcha")
    p = _write(tmp_path, bad)
    with pytest.raises(ProfileError, match="captcha_type"):
        load_profile(p)


def test_extra_unknown_field_rejected(tmp_path: Path) -> None:
    bad = VALID_TURNSTILE_YAML + "\nextra_unknown_field: 42\n"
    p = _write(tmp_path, bad)
    with pytest.raises(ProfileError, match="extra"):
        load_profile(p)


def test_invalid_css_selector_rejected(tmp_path: Path) -> None:
    bad = VALID_TURNSTILE_YAML.replace(
        "selector: \"input[name='email']\"",
        'selector: "!!not a selector"',
    )
    p = _write(tmp_path, bad)
    with pytest.raises(ProfileError, match="CSS selector"):
        load_profile(p)


def test_fill_requires_exactly_one_value_source(tmp_path: Path) -> None:
    bad = VALID_TURNSTILE_YAML.replace(
        'value_env: "QA_EMAIL"',
        'value_env: "QA_EMAIL"\n      value: "oops"',
    )
    p = _write(tmp_path, bad)
    with pytest.raises(ProfileError, match="exactly one"):
        load_profile(p)


def test_success_must_have_at_least_one_condition(tmp_path: Path) -> None:
    bad = VALID_TURNSTILE_YAML.replace(
        'success:\n  url_contains: ["/dashboard"]',
        "success: {}",
    )
    p = _write(tmp_path, bad)
    with pytest.raises(ProfileError, match="success"):
        load_profile(p)


def test_polling_interval_out_of_range(tmp_path: Path) -> None:
    bad = VALID_TURNSTILE_YAML.replace(
        'success:\n  url_contains: ["/dashboard"]',
        'captchaai:\n  polling_interval_seconds: 999\nsuccess:\n  url_contains: ["/dashboard"]',
    )
    p = _write(tmp_path, bad)
    with pytest.raises(ProfileError, match="polling_interval_seconds"):
        load_profile(p)


def test_name_pattern_enforced(tmp_path: Path) -> None:
    bad = VALID_TURNSTILE_YAML.replace("name: my-test", 'name: "my test with spaces"')
    p = _write(tmp_path, bad)
    with pytest.raises(ProfileError, match="name"):
        load_profile(p)


# --- Secret detection ------------------------------------------------------


def test_secret_shaped_hex_string_in_value_rejected(tmp_path: Path) -> None:
    """A 32-char hex string in `value` (looks like an API key) must fail."""
    bad = VALID_TURNSTILE_YAML.replace(
        'value_env: "QA_EMAIL"',
        'value: "deadbeefcafebabe1234567890abcdef"',
    )
    p = _write(tmp_path, bad)
    with pytest.raises(ProfileError, match="secret"):
        load_profile(p)


def test_value_env_name_not_flagged_even_if_long(tmp_path: Path) -> None:
    """`value_env` holds an env var NAME, never a value — no secret scan."""
    long_name = "MY_VERY_LONG_AND_DESCRIPTIVE_ENV_VAR_NAME_FOR_THE_TEST_USER"
    good = VALID_TURNSTILE_YAML.replace('value_env: "QA_EMAIL"', f'value_env: "{long_name}"')
    p = _write(tmp_path, good)
    profile = load_profile(p)
    assert profile.name == "my-test"


def test_secret_in_arbitrary_field_rejected(tmp_path: Path) -> None:
    """A long hex/opaque string anywhere in the profile is rejected."""
    fake_keylike = "f" * 32 + "0123456789abcdef"  # synthetic, not a real secret
    bad = VALID_TURNSTILE_YAML.replace(
        "name: my-test",
        f'name: my-test\n_note: "key={fake_keylike}"',
    )
    p = _write(tmp_path, bad)
    with pytest.raises(ProfileError):
        load_profile(p)

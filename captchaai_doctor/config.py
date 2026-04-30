"""Profile loading and validation.

Two-stage validation:
1. Secret scan on the raw YAML (before Pydantic, so we catch leaks even when
   the schema would also reject).
2. Pydantic schema validation (structural + semantic invariants).

Both stages raise `ProfileError` with an actionable message on failure.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from captchaai_doctor.schemas import _SECRET_LIKE_PATTERN, Profile


class ProfileError(Exception):
    """Raised for any profile loading or validation failure."""


def _walk_strings(node: Any, path: str = "$") -> Iterator[tuple[str, str]]:
    """Yield (json-pointer-ish path, string value) for every string in the YAML."""
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _walk_strings(value, f"{path}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _walk_strings(value, f"{path}[{index}]")
    elif isinstance(node, str):
        yield path, node


def _format_pydantic_errors(exc: ValidationError) -> str:
    lines = []
    for err in exc.errors():
        loc = ".".join(str(part) for part in err["loc"])
        lines.append(f"  - {loc}: {err['msg']}")
    return "\n".join(lines)


def _scan_for_secrets(raw: Any) -> list[str]:
    """Return a list of human-readable warnings for secret-shaped strings."""
    warnings: list[str] = []
    for path, value in _walk_strings(raw):
        # Allow the documented `value_env` field — it stores a NAME, not a value.
        if path.endswith(".value_env"):
            continue
        if _SECRET_LIKE_PATTERN.search(value):
            warnings.append(
                f"{path}: looks like a secret (long opaque string). "
                "Use environment variables (e.g. `value_env: MY_SECRET`) instead."
            )
    return warnings


def load_profile(path: str | Path) -> Profile:
    """Load and validate a profile YAML from disk.

    Raises:
        ProfileError: if the file is missing, the YAML is invalid, the schema
            does not match, or the profile contains secret-shaped values.
    """
    p = Path(path)
    if not p.exists():
        raise ProfileError(f"profile file not found: {p}")
    if not p.is_file():
        raise ProfileError(f"profile path is not a file: {p}")

    try:
        raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ProfileError(f"invalid YAML in {p}: {exc}") from exc

    if raw is None or not isinstance(raw, dict):
        raise ProfileError(f"profile {p} must be a YAML mapping at the top level")

    secret_warnings = _scan_for_secrets(raw)
    if secret_warnings:
        joined = "\n".join(f"  - {w}" for w in secret_warnings)
        raise ProfileError(
            f"profile {p} appears to contain secrets:\n{joined}\n"
            "Profiles must never store secrets. Use `value_env: NAME` and set NAME in your env."
        )

    try:
        profile = Profile.model_validate(raw)
    except ValidationError as exc:
        raise ProfileError(
            f"profile {p} failed schema validation:\n{_format_pydantic_errors(exc)}"
        ) from exc

    return profile


def validate_profile(path: str | Path) -> Profile:
    """Public alias for :func:`load_profile` — kept for CLI symmetry."""
    return load_profile(path)


__all__ = ["ProfileError", "load_profile", "validate_profile"]

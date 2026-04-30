"""Log redaction helpers.

Strips secret-shaped substrings out of any text that flows through Python
logging. Mounted as a `logging.Filter` so call sites don't need to think
about it.

Heuristics, conservative on the side of redacting too much:
- 32-char hex (typical API key): keep first 4 + last 4
- 40+ char opaque (jwt-ish, captcha tokens): keep first 6 + length marker
- captcha_id-style integers >= 7 digits: keep first 4
- query-string `key=...&` and `id=...&`: keep first 4 of the value
"""

from __future__ import annotations

import logging
import re

_HEX_KEY = re.compile(r"\b([a-fA-F0-9]{32})\b")
_OPAQUE_TOKEN = re.compile(r"\b([A-Za-z0-9_\-]{40,})\b")
_QUERY_KEY = re.compile(r"(?i)\b(key|id|api_?key|token)=([^&\s\"']+)")
_NUMERIC_ID = re.compile(r"(?<![\w])(\d{7,})(?![\w])")


def _mask_hex(match: re.Match[str]) -> str:
    v = match.group(1)
    return f"{v[:4]}...{v[-4:]}"


def _mask_opaque(match: re.Match[str]) -> str:
    v = match.group(1)
    return f"{v[:6]}...<len={len(v)}>"


def _mask_query(match: re.Match[str]) -> str:
    name = match.group(1)
    value = match.group(2)
    if len(value) <= 4:
        return f"{name}=****"
    return f"{name}={value[:4]}****"


def _mask_numeric_id(match: re.Match[str]) -> str:
    v = match.group(1)
    return f"{v[:4]}****"


def redact(text: str) -> str:
    """Return ``text`` with secret-shaped substrings masked.

    Order matters: query-string masking runs first because it greedily eats
    the value before the hex/opaque rules would over-mask the surrounding
    URL.
    """
    out = _QUERY_KEY.sub(_mask_query, text)
    out = _HEX_KEY.sub(_mask_hex, out)
    out = _OPAQUE_TOKEN.sub(_mask_opaque, out)
    out = _NUMERIC_ID.sub(_mask_numeric_id, out)
    return out


class RedactingFilter(logging.Filter):
    """Logging filter that runs :func:`redact` on the formatted message + args."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            if record.args:
                # Render args first, then redact, then clear args so the handler
                # doesn't try to re-format.
                record.msg = redact(record.getMessage())
                record.args = ()
            else:
                record.msg = redact(str(record.msg))
        except Exception:  # pragma: no cover — never block logging
            pass
        return True


def install_global_redaction() -> RedactingFilter:
    """Attach :class:`RedactingFilter` to the root logger and every existing handler.

    Idempotent — re-running won't add duplicates. Note: handlers added
    *after* this call must opt in themselves; for that reason production
    code should configure logging handlers first, then call this.
    """
    root = logging.getLogger()
    flt: RedactingFilter | None = next(
        (f for f in root.filters if isinstance(f, RedactingFilter)), None
    )
    if flt is None:
        flt = RedactingFilter()
        root.addFilter(flt)
    for handler in root.handlers:
        if not any(isinstance(f, RedactingFilter) for f in handler.filters):
            handler.addFilter(flt)
    return flt


__all__ = ["RedactingFilter", "install_global_redaction", "redact"]

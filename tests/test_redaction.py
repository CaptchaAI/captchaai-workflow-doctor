"""Tests for `captchaai_doctor.redaction`."""

from __future__ import annotations

import logging

from captchaai_doctor.redaction import RedactingFilter, install_global_redaction, redact


def test_redact_hex_api_key() -> None:
    text = "calling api with key=deadbeefcafebabe1234567890abcdef sending..."
    out = redact(text)
    assert "deadbeefcafebabe1234567890abcdef" not in out
    assert "dead" in out  # query-key form keeps first 4


def test_redact_query_string_key() -> None:
    # Synthetic 32-char hex — low-entropy repeating pattern, not a real key.
    synthetic = "deadbeef" * 4
    out = redact(f"https://api.example.com/in.php?key={synthetic}&id=12345678")
    assert synthetic not in out
    assert "key=dead****" in out
    assert "id=1234****" in out


def test_redact_long_opaque_token() -> None:
    token = "ABCDEFG" + "x" * 200
    out = redact(f"received token {token} done")
    assert token not in out
    assert "ABCDEF...<len=" in out


def test_redact_short_strings_untouched() -> None:
    msg = "short value=hello world"
    assert redact(msg) == msg


def test_logging_filter_masks_via_root_logger(caplog) -> None:
    flt = install_global_redaction()
    # caplog installs its own handler on the root logger; attach our filter to
    # it explicitly so messages logged on child loggers get redacted before
    # they reach the capture.
    caplog.handler.addFilter(flt)
    log = logging.getLogger("test.redaction")
    synthetic_key = "deadbeef" * 4  # low-entropy 32-char hex — not a real key
    with caplog.at_level(logging.INFO):
        log.info("api call key=%s done", synthetic_key)
    combined = " ".join(rec.getMessage() for rec in caplog.records)
    assert synthetic_key not in combined


def test_filter_handles_args_safely() -> None:
    flt = RedactingFilter()
    synthetic_key = "deadbeef" * 4
    rec = logging.LogRecord(
        name="x",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="key=%s",
        args=(synthetic_key,),
        exc_info=None,
    )
    flt.filter(rec)
    assert rec.args == ()
    assert synthetic_key not in rec.getMessage()

"""Tests for the (Phase-5-bound) recommendation map."""

from __future__ import annotations

import pytest

from captchaai_doctor.classifier import RECOMMENDATIONS, recommendation_for
from captchaai_doctor.runner import RootCause


def test_every_root_cause_has_a_recommendation() -> None:
    # RootCause is a Literal[...] alias; pull the literal members out of
    # its __args__ to make sure the map covers every case the runner can
    # produce.
    members = set(RootCause.__args__)  # type: ignore[attr-defined]
    missing = members - set(RECOMMENDATIONS)
    assert not missing, f"missing recommendations for: {sorted(missing)}"


@pytest.mark.parametrize("cause", list(RECOMMENDATIONS))
def test_recommendation_is_non_empty_string(cause: str) -> None:
    rec = recommendation_for(cause)
    assert isinstance(rec, str)
    assert rec.strip()


def test_unknown_cause_falls_back_to_unknown() -> None:
    assert recommendation_for("not-a-real-cause") == RECOMMENDATIONS["unknown"]

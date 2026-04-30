"""Report writers.

Phase 3 ships only the JSON report (HTML lands in Phase 5). The JSON
shape is stable and intended to be consumed by CI / downstream tooling.
"""

from __future__ import annotations

import json
from pathlib import Path

from captchaai_doctor.runner import RunResult


def write_json_report(result: RunResult, path: str | Path) -> Path:
    """Write the run result to ``path`` as pretty-printed JSON. Returns the path."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return out


__all__ = ["write_json_report"]

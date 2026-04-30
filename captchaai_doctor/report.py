"""Report writers — JSON, HTML, and JSON Schema.

Two stable artifacts are produced per workflow run:

- ``report.json``  — machine readable, validates against
  :data:`REPORT_JSON_SCHEMA` so downstream CI / dashboards can rely on
  the shape.
- ``report.html``  — a single self-contained file (no external CSS/JS,
  no remote fonts) that opens cleanly from disk and is suitable for
  attaching to a CI artifact.

Both writers are pure functions of a :class:`~captchaai_doctor.runner.RunResult`
plus the on-disk ``screenshots`` it references (relative paths are
preserved as-is).

The recommendation text comes from
:mod:`captchaai_doctor.classifier`, so JSON consumers and humans see
the same "what to do next" message.
"""

from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Any

from captchaai_doctor.classifier import recommendation_for
from captchaai_doctor.runner import RunResult

# ---------------------------------------------------------------------------
# JSON Schema (Draft 2020-12)
# ---------------------------------------------------------------------------

REPORT_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://captchaai.com/schemas/captchaai-doctor-report-1.json",
    "title": "CaptchaAIDoctorReport",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "profile_name",
        "captcha_type",
        "target_url",
        "started_at",
        "ended_at",
        "duration_seconds",
        "status",
        "root_cause",
        "recommendation",
        "detail",
        "captcha_id_redacted",
        "poll_attempts",
        "poll_seconds",
        "sitekey_found",
        "screenshots",
        "action_steps",
    ],
    "properties": {
        "profile_name": {"type": "string", "minLength": 1},
        "captcha_type": {
            "type": "string",
            "enum": ["turnstile", "recaptcha_v2", "recaptcha_v3"],
        },
        "target_url": {"type": "string", "format": "uri"},
        "started_at": {"type": "string"},
        "ended_at": {"type": "string"},
        "duration_seconds": {"type": "number", "minimum": 0},
        "status": {"type": "string", "enum": ["success", "failure", "error"]},
        "root_cause": {"type": "string", "minLength": 1},
        "recommendation": {"type": "string", "minLength": 1},
        "detail": {"type": ["string", "null"]},
        "captcha_id_redacted": {"type": ["string", "null"]},
        "poll_attempts": {"type": "integer", "minimum": 0},
        "poll_seconds": {"type": "number", "minimum": 0},
        "sitekey_found": {"type": ["string", "null"]},
        "screenshots": {"type": "array", "items": {"type": "string"}},
        "action_steps": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["type", "selector", "succeeded", "detail"],
                "properties": {
                    "type": {"type": "string"},
                    "selector": {"type": ["string", "null"]},
                    "succeeded": {"type": "boolean"},
                    "detail": {"type": ["string", "null"]},
                },
            },
        },
    },
}


def _enrich(result: RunResult) -> dict[str, Any]:
    """Augment the result dict with the recommendation field."""
    payload = result.to_dict()
    payload["recommendation"] = recommendation_for(result.root_cause)
    return payload


def write_json_report(result: RunResult, path: str | Path) -> Path:
    """Write the run result to ``path`` as pretty-printed JSON."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(_enrich(result), indent=2, sort_keys=True), encoding="utf-8")
    return out


def write_schema(path: str | Path) -> Path:
    """Write :data:`REPORT_JSON_SCHEMA` to ``path``."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(REPORT_JSON_SCHEMA, indent=2, sort_keys=True), encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# HTML report (single self-contained file, no external assets)
# ---------------------------------------------------------------------------

_BADGE_COLORS: dict[str, str] = {
    "success": "#1e7f3b",
    "failure": "#b3261e",
    "error": "#a06000",
}


def _badge(status: str) -> str:
    color = _BADGE_COLORS.get(status, "#444")
    return f'<span class="badge" style="background:{color}">{escape(status.upper())}</span>'


def _render_steps(steps: list[dict[str, Any]]) -> str:
    if not steps:
        return "<p><em>No action steps recorded.</em></p>"
    rows: list[str] = []
    for s in steps:
        ok = "OK" if s.get("succeeded") else "FAIL"
        ok_color = "#1e7f3b" if s.get("succeeded") else "#b3261e"
        rows.append(
            "<tr>"
            f'<td style="color:{ok_color};font-weight:bold">{ok}</td>'
            f"<td>{escape(str(s.get('type', '')))}</td>"
            f"<td><code>{escape(str(s.get('selector') or ''))}</code></td>"
            f"<td>{escape(str(s.get('detail') or ''))}</td>"
            "</tr>"
        )
    return (
        '<table class="steps">'
        "<thead><tr><th></th><th>type</th><th>selector</th><th>detail</th></tr></thead>"
        "<tbody>" + "".join(rows) + "</tbody></table>"
    )


def _render_screenshots(screenshots: list[str], html_dir: Path) -> str:
    if not screenshots:
        return "<p><em>No screenshots were captured.</em></p>"
    items: list[str] = []
    for shot in screenshots:
        if not shot:
            continue
        path = Path(shot)
        try:
            href = str(path.resolve().relative_to(html_dir.resolve()))
        except ValueError:
            href = path.as_posix()
        items.append(
            f'<figure><a href="{escape(href)}"><img src="{escape(href)}" alt=""></a>'
            f"<figcaption>{escape(path.name)}</figcaption></figure>"
        )
    return '<div class="shots">' + "".join(items) + "</div>"


_HTML_TEMPLATE = """\
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>CaptchaAI Doctor &mdash; {profile_name}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial,
            sans-serif; max-width: 960px; margin: 2rem auto; padding: 0 1rem;
            color: #222; }}
    h1 {{ margin-bottom: 0.25rem; }}
    .meta {{ color: #555; margin-top: 0; }}
    .badge {{ color: #fff; padding: 0.15rem 0.6rem; border-radius: 0.4rem;
              font-size: 0.85rem; letter-spacing: 0.05em; }}
    .grid {{ display: grid; grid-template-columns: max-content 1fr; gap: 0.4rem 1rem;
             margin: 1rem 0; }}
    .grid dt {{ font-weight: 600; color: #444; }}
    .grid dd {{ margin: 0; }}
    .recommendation {{ background: #fff8e6; border-left: 4px solid #f0ad4e;
                       padding: 0.75rem 1rem; border-radius: 0 0.4rem 0.4rem 0; }}
    .steps {{ width: 100%; border-collapse: collapse; margin: 1rem 0; }}
    .steps th, .steps td {{ border-bottom: 1px solid #eee; padding: 0.4rem 0.6rem;
                            text-align: left; vertical-align: top; }}
    .shots {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
              gap: 1rem; }}
    .shots figure {{ margin: 0; }}
    .shots img {{ max-width: 100%; border: 1px solid #ddd; border-radius: 0.3rem; }}
    .shots figcaption {{ font-size: 0.85rem; color: #666; }}
    code {{ background: #f4f4f4; padding: 0.05rem 0.3rem; border-radius: 0.25rem; }}
    section {{ margin-top: 2rem; }}
    h2 {{ border-bottom: 1px solid #eee; padding-bottom: 0.25rem; }}
  </style>
</head>
<body>
  <h1>{profile_name} {badge}</h1>
  <p class="meta">{captcha_type} &middot; <code>{target_url}</code></p>

  <section>
    <h2>Summary</h2>
    <dl class="grid">
      <dt>Status</dt><dd>{status}</dd>
      <dt>Root cause</dt><dd><code>{root_cause}</code></dd>
      <dt>Detail</dt><dd>{detail}</dd>
      <dt>Started</dt><dd>{started_at}</dd>
      <dt>Ended</dt><dd>{ended_at}</dd>
      <dt>Duration</dt><dd>{duration_seconds:.3f} s</dd>
      <dt>Sitekey found</dt><dd><code>{sitekey_found}</code></dd>
      <dt>Captcha ID</dt><dd><code>{captcha_id_redacted}</code> (redacted)</dd>
      <dt>Poll attempts</dt><dd>{poll_attempts}</dd>
      <dt>Poll seconds</dt><dd>{poll_seconds:.3f}</dd>
    </dl>
  </section>

  <section>
    <h2>Recommendation</h2>
    <p class="recommendation">{recommendation}</p>
  </section>

  <section>
    <h2>Action timeline</h2>
    {steps_table}
  </section>

  <section>
    <h2>Screenshots</h2>
    {shots_block}
  </section>

  <section>
    <h2>Raw JSON</h2>
    <pre><code>{raw_json}</code></pre>
  </section>
</body>
</html>
"""


def write_html_report(result: RunResult, path: str | Path) -> Path:
    """Render a single self-contained HTML report to ``path``."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = _enrich(result)

    html = _HTML_TEMPLATE.format(
        profile_name=escape(result.profile_name),
        captcha_type=escape(result.captcha_type),
        target_url=escape(result.target_url),
        badge=_badge(result.status),
        status=escape(result.status),
        root_cause=escape(result.root_cause),
        detail=escape(result.detail or "—"),
        started_at=escape(result.started_at),
        ended_at=escape(result.ended_at),
        duration_seconds=result.duration_seconds,
        sitekey_found=escape(result.sitekey_found or "—"),
        captcha_id_redacted=escape(result.captcha_id_redacted or "—"),
        poll_attempts=result.poll_attempts,
        poll_seconds=result.poll_seconds,
        recommendation=escape(payload["recommendation"]),
        steps_table=_render_steps(result.action_steps),
        shots_block=_render_screenshots(result.screenshots, out.parent),
        raw_json=escape(json.dumps(payload, indent=2, sort_keys=True)),
    )
    out.write_text(html, encoding="utf-8")
    return out


__all__ = [
    "REPORT_JSON_SCHEMA",
    "write_html_report",
    "write_json_report",
    "write_schema",
]

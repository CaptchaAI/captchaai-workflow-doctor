"""Capture a publishable PNG screenshot of a sample HTML report.

Used to generate the article / landing-page asset
``captchaai-workflow-doctor-report-screenshot.png``.

Usage::

    python scripts/capture-report-screenshot.py \\
        --report sample-reports/callback-not-invoked.html \\
        --out /tmp/report-screenshot.png \\
        --width 1600 --height 1000

If ``--report`` is omitted, the script picks the
``callback-not-invoked.html`` fixture from ``sample-reports/`` because
that is the most visually informative failure case for marketing
material.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = REPO_ROOT / "sample-reports" / "callback-not-invoked.html"


def capture(report: Path, out: Path, width: int, height: int) -> None:
    report = report.resolve()
    out = out.resolve()
    if not report.exists():
        raise SystemExit(f"report not found: {report}")
    out.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            context = browser.new_context(
                viewport={"width": width, "height": height},
                device_scale_factor=2,  # retina-quality PNG
            )
            page = context.new_page()
            page.goto(report.as_uri())
            page.wait_for_load_state("networkidle")
            page.screenshot(path=str(out), full_page=False)
        finally:
            browser.close()
    print(f"wrote {out}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "report-screenshot.png")
    ap.add_argument("--width", type=int, default=1600)
    ap.add_argument("--height", type=int, default=1000)
    args = ap.parse_args()
    capture(args.report, args.out, args.width, args.height)


if __name__ == "__main__":
    main()

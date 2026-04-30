"""Local Cloudflare-challenge-like demo target.

A real Cloudflare interstitial ("Just a moment...") page does not have a
sitekey or a token-injection field. Instead it serves a small JS challenge
that, on success, sets a ``cf_clearance`` cookie bound to:

- the IP that solved the challenge, and
- the User-Agent that requested the page.

Subsequent navigations carrying that cookie + matching UA bypass the
challenge and serve the protected content.

This mock mirrors that contract:

- ``GET /protected`` without a valid ``cf_clearance`` cookie / matching UA
  serves a CF-style interstitial.
- ``GET /protected`` with cookie ``cf_clearance=FAKE_OK_CLEARANCE`` AND
  the Chrome UA we hand back from the fake CaptchaAI client serves the
  protected page (``data-testid="protected"``).

Failure modes (selected via ``?mode=`` query string):

- ``ok``           - happy path; clearance cookie + UA pair lets you in.
- ``wrong-cookie`` - server always rejects the cookie (covers the case
                     where the worker minted a cookie for a different IP
                     than your browser is replaying from).

No external network or real Cloudflare is involved.
"""

from __future__ import annotations

from typing import Final

from flask import Flask, make_response, redirect, render_template_string, request, url_for

FAKE_OK_CLEARANCE: Final[str] = "FAKE_OK_CLEARANCE"
EXPECTED_USER_AGENT_FRAGMENT: Final[str] = "Chrome/124"

VALID_MODES: Final[frozenset[str]] = frozenset({"ok", "wrong-cookie"})


_CHALLENGE_HTML = """\
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Just a moment...</title>
  </head>
  <body>
    <div id="cf-challenge-running" data-testid="cf-interstitial">
      <h1>Just a moment...</h1>
      <p>Checking your browser before accessing the site.</p>
    </div>
    <!-- The detector keys off this script src exactly like a real CF page. -->
    <script src="https://challenges.cloudflare.com/cdn-cgi/challenge-platform/h/g/orchestrate/chl_page/v1?mock=1"></script>
  </body>
</html>
"""

_PROTECTED_HTML = """\
<!doctype html>
<html lang="en">
  <head><meta charset="utf-8"><title>Protected</title></head>
  <body>
    <div data-testid="protected">
      <h1>Welcome past the wall</h1>
      <p>Mode: {{ mode }}</p>
    </div>
  </body>
</html>
"""


def _resolve_mode() -> str:
    mode = (request.args.get("mode") or "ok").strip().lower()
    return mode if mode in VALID_MODES else "ok"


def create_app() -> Flask:
    """Build the Flask app instance. Safe to call multiple times in tests."""
    app = Flask(__name__)
    app.config.update(TESTING=False, SECRET_KEY="mock-cf-challenge-app-not-a-real-secret")

    @app.get("/")
    def index() -> str:
        return redirect(url_for("protected"))  # type: ignore[return-value]

    @app.get("/protected")
    def protected() -> object:
        mode = _resolve_mode()
        cookie = request.cookies.get("cf_clearance") or ""
        ua = request.headers.get("User-Agent") or ""

        cookie_ok = cookie == FAKE_OK_CLEARANCE
        ua_ok = EXPECTED_USER_AGENT_FRAGMENT in ua

        cleared = mode == "ok" and cookie_ok and ua_ok
        if cleared:
            return render_template_string(_PROTECTED_HTML, mode=mode)
        # Serve interstitial with a 403 like the real CF page so a future
        # success-by-status check would also flip; tests use the DOM marker.
        resp = make_response(render_template_string(_CHALLENGE_HTML), 403)
        resp.headers["X-Mock-Cf-Cookie-Match"] = "1" if cookie_ok else "0"
        resp.headers["X-Mock-Cf-Ua-Match"] = "1" if ua_ok else "0"
        return resp

    @app.get("/healthz")
    def healthz() -> tuple[str, int]:
        return "ok", 200

    return app


def main() -> None:  # pragma: no cover - manual launch only
    """Run the dev server. Used by ``captchaai-doctor demo cloudflare-challenge``."""
    create_app().run(host="127.0.0.1", port=8769, debug=False, use_reloader=False)


if __name__ == "__main__":  # pragma: no cover
    main()

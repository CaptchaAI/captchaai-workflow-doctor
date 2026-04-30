"""Local Turnstile-like demo target.

A self-contained Flask app that mimics the *integration shape* of a
Cloudflare Turnstile login page so the workflow doctor can be exercised
end-to-end with no network and no real CAPTCHA solver.

Failure modes (selected via the `?mode=` query string on `/login`):

- ``ok``           — happy path; the JS widget exposes
                     ``window.onTurnstileSuccess(token)`` and the form
                     accepts ``FAKE_TOKEN_OK``.
- ``wrong-token``  — the form rejects every token (renders the
                     "captcha verification failed" failure-marker).
- ``no-callback``  — the widget does not expose any callback name from
                     the profile's ``callback_candidates``.

The widget itself is fake (no real Turnstile script). It just renders a
``<div data-sitekey="...">`` and a hidden ``<textarea
name="cf-turnstile-response">`` that the doctor can locate.
"""

from __future__ import annotations

from typing import Final

from flask import Flask, redirect, render_template_string, request, url_for

# Default credentials for the demo. Profiles that exercise this app pass
# these via env (QA_EMAIL/QA_PASSWORD).
DEMO_EMAIL: Final[str] = "demo@example.com"
DEMO_PASSWORD: Final[str] = "demo-pass"

# Token the fake CAPTCHA solver always returns.
FAKE_OK_TOKEN: Final[str] = "FAKE_TOKEN_OK"

# Synthetic site key — fixed so profiles can pin to it if they want.
DEMO_SITEKEY: Final[str] = "0xMOCK_SITEKEY_DEMO"

VALID_MODES: Final[frozenset[str]] = frozenset({"ok", "wrong-token", "no-callback"})


_LOGIN_HTML = """\
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Mock Turnstile Login</title>
  </head>
  <body>
    <h1>Mock Login</h1>
    {% if error %}<p class="error">{{ error }}</p>{% endif %}
    <form method="post" action="{{ url_for('login') }}?mode={{ mode }}">
      <label>Email <input name="email" type="email" required></label><br>
      <label>Password <input name="password" type="password" required></label><br>
      <div id="cf-turnstile" data-sitekey="{{ sitekey }}"></div>
      <textarea name="cf-turnstile-response" hidden></textarea>
      <button type="submit">Sign in</button>
    </form>

    <script>
      // Mock widget. In `ok` and `wrong-token` modes we expose the
      // callback the profile is configured to invoke. In `no-callback`
      // mode we deliberately do NOT \u2014 simulating a misconfigured
      // integration.
      {% if mode != "no-callback" %}
      window.onTurnstileSuccess = function (token) {
        var el = document.querySelector('textarea[name="cf-turnstile-response"]');
        if (el) { el.value = token; }
      };
      {% endif %}
    </script>
  </body>
</html>
"""

_DASHBOARD_HTML = """\
<!doctype html>
<html lang="en">
  <head><meta charset="utf-8"><title>Dashboard</title></head>
  <body>
    <div data-testid="dashboard">
      <h1>Welcome, {{ email }}</h1>
      <p>You are signed in.</p>
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
    app.config.update(TESTING=False, SECRET_KEY="mock-app-not-a-real-secret")

    @app.get("/")
    def index() -> str:
        return redirect(url_for("login"))  # type: ignore[return-value]

    @app.route("/login", methods=["GET", "POST"])
    def login() -> str:
        mode = _resolve_mode()
        if request.method == "GET":
            return render_template_string(_LOGIN_HTML, error=None, sitekey=DEMO_SITEKEY, mode=mode)

        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""
        token = request.form.get("cf-turnstile-response") or ""

        # Mode-specific failure injection.
        if mode == "wrong-token" or token != FAKE_OK_TOKEN:
            return render_template_string(
                _LOGIN_HTML,
                error="captcha verification failed",
                sitekey=DEMO_SITEKEY,
                mode=mode,
            )

        if email != DEMO_EMAIL or password != DEMO_PASSWORD:
            return render_template_string(
                _LOGIN_HTML,
                error="invalid credentials",
                sitekey=DEMO_SITEKEY,
                mode=mode,
            )

        return render_template_string(_DASHBOARD_HTML, email=email)

    @app.get("/dashboard")
    def dashboard() -> str:
        # Direct landing for tests; in real flow user arrives via POST.
        return render_template_string(_DASHBOARD_HTML, email=DEMO_EMAIL)

    @app.get("/healthz")
    def healthz() -> tuple[str, int]:
        return "ok", 200

    return app


def main() -> None:  # pragma: no cover - manual launch only
    """Run the dev server. Used by ``captchaai-doctor demo turnstile``."""
    create_app().run(host="127.0.0.1", port=8765, debug=False, use_reloader=False)


if __name__ == "__main__":  # pragma: no cover
    main()

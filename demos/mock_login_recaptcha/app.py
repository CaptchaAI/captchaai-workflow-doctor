"""Local reCAPTCHA-v2-like demo target.

Mirrors :mod:`demos.mock_login_turnstile.app` but uses the Google
reCAPTCHA v2 *integration shape* — ``g-recaptcha`` div, ``data-sitekey``
attribute, ``g-recaptcha-response`` hidden textarea, and a
``window.onRecaptchaSuccess(token)`` global callback.

Failure modes (selected via the ``?mode=`` query string on ``/login``):

- ``ok``           — happy path; the form accepts ``FAKE_TOKEN_OK``.
- ``wrong-token``  — every token is rejected.
- ``no-callback``  — the callback global is not defined.

No external network or real reCAPTCHA script is involved.
"""

from __future__ import annotations

from typing import Final

from flask import Flask, redirect, render_template_string, request, url_for

DEMO_EMAIL: Final[str] = "demo@example.com"
DEMO_PASSWORD: Final[str] = "demo-pass"
FAKE_OK_TOKEN: Final[str] = "FAKE_TOKEN_OK"
DEMO_SITEKEY: Final[str] = "6LcMOCK_RECAPTCHA_SITEKEY_DEMO"

VALID_MODES: Final[frozenset[str]] = frozenset({"ok", "wrong-token", "no-callback"})


_LOGIN_HTML = """\
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Mock reCAPTCHA Login</title>
  </head>
  <body>
    <h1>Mock reCAPTCHA Login</h1>
    {% if error %}<p class="error">{{ error }}</p>{% endif %}
    <form method="post" action="{{ url_for('login') }}?mode={{ mode }}">
      <label>Email <input name="email" type="email" required></label><br>
      <label>Password <input name="password" type="password" required></label><br>
      <div class="g-recaptcha" data-sitekey="{{ sitekey }}"
           {% if mode != "no-callback" %}data-callback="onRecaptchaSuccess"{% endif %}></div>
      <textarea name="g-recaptcha-response" hidden></textarea>
      <button type="submit">Sign in</button>
    </form>

    <script>
      {% if mode != "no-callback" %}
      window.onRecaptchaSuccess = function (token) {
        var el = document.querySelector('textarea[name="g-recaptcha-response"]');
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
      <p>You are signed in (reCAPTCHA flow).</p>
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
    app.config.update(TESTING=False, SECRET_KEY="mock-recaptcha-app-not-a-real-secret")

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
        token = request.form.get("g-recaptcha-response") or ""

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
        return render_template_string(_DASHBOARD_HTML, email=DEMO_EMAIL)

    @app.get("/healthz")
    def healthz() -> tuple[str, int]:
        return "ok", 200

    return app


def main() -> None:  # pragma: no cover - manual launch only
    """Run the dev server. Used by ``captchaai-doctor demo recaptcha-v2``."""
    create_app().run(host="127.0.0.1", port=8766, debug=False, use_reloader=False)


if __name__ == "__main__":  # pragma: no cover
    main()

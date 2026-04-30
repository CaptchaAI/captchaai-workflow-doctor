"""Local reCAPTCHA-v3-like demo target.

reCAPTCHA v3 has no widget UX. The page loads a script with
``?render=SITEKEY`` and calls ``grecaptcha.execute(sitekey, {action})``
to obtain a token, then submits it as a hidden ``g-recaptcha-response``
form field.

This mock mirrors that integration shape so the doctor can exercise:

- detection of the v3 sitekey from a script tag,
- submission with a profile-supplied ``action``,
- token injection into the hidden response field,
- form submit + server validation.

Failure modes (selected via the ``?mode=`` query string on ``/contact``):

- ``ok``          - happy path; the form accepts ``FAKE_TOKEN_OK``.
- ``wrong-token`` - every token is rejected.

No external network or real reCAPTCHA script is involved.
"""

from __future__ import annotations

from typing import Final

from flask import Flask, redirect, render_template_string, request, url_for

DEMO_NAME: Final[str] = "demo-user"
FAKE_OK_TOKEN: Final[str] = "FAKE_TOKEN_OK"
DEMO_SITEKEY: Final[str] = "6LcMOCK_RECAPTCHA_V3_SITEKEY_DEMO"
DEMO_ACTION: Final[str] = "submit_contact"

VALID_MODES: Final[frozenset[str]] = frozenset({"ok", "wrong-token"})


_CONTACT_HTML = """\
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Mock reCAPTCHA v3 Contact</title>
  </head>
  <body>
    <h1>Mock reCAPTCHA v3 Contact</h1>
    {% if error %}<p class="error">{{ error }}</p>{% endif %}
    <form method="post" action="{{ url_for('contact') }}?mode={{ mode }}">
      <label>Name <input name="name" type="text" required></label><br>
      <label>Message <textarea name="message" required></textarea></label><br>
      <input name="g-recaptcha-response" type="hidden" value="">
      <input name="action" type="hidden" value="{{ action }}">
      <button type="submit">Send</button>
    </form>

    <!-- v3 integration shape: a script tag with ?render=SITEKEY -->
    <script src="https://www.google.com/recaptcha/api.js?render={{ sitekey }}"
            data-mock-sitekey="{{ sitekey }}"></script>
  </body>
</html>
"""

_THANKS_HTML = """\
<!doctype html>
<html lang="en">
  <head><meta charset="utf-8"><title>Thanks</title></head>
  <body>
    <div data-testid="thanks">
      <h1>Thanks, {{ name }}</h1>
      <p>Your message was accepted (reCAPTCHA v3).</p>
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
    app.config.update(TESTING=False, SECRET_KEY="mock-recaptcha-v3-app-not-a-real-secret")

    @app.get("/")
    def index() -> str:
        return redirect(url_for("contact"))  # type: ignore[return-value]

    @app.route("/contact", methods=["GET", "POST"])
    def contact() -> str:
        mode = _resolve_mode()
        if request.method == "GET":
            return render_template_string(
                _CONTACT_HTML,
                error=None,
                sitekey=DEMO_SITEKEY,
                action=DEMO_ACTION,
                mode=mode,
            )

        name = (request.form.get("name") or "").strip()
        message = (request.form.get("message") or "").strip()
        token = request.form.get("g-recaptcha-response") or ""

        if mode == "wrong-token" or token != FAKE_OK_TOKEN:
            return render_template_string(
                _CONTACT_HTML,
                error="captcha verification failed",
                sitekey=DEMO_SITEKEY,
                action=DEMO_ACTION,
                mode=mode,
            )

        if not name or not message:
            return render_template_string(
                _CONTACT_HTML,
                error="name and message required",
                sitekey=DEMO_SITEKEY,
                action=DEMO_ACTION,
                mode=mode,
            )

        return render_template_string(_THANKS_HTML, name=name)

    @app.get("/thanks")
    def thanks() -> str:
        return render_template_string(_THANKS_HTML, name=DEMO_NAME)

    @app.get("/healthz")
    def healthz() -> tuple[str, int]:
        return "ok", 200

    return app


def main() -> None:  # pragma: no cover - manual launch only
    """Run the dev server. Used by ``captchaai-doctor demo recaptcha-v3``."""
    create_app().run(host="127.0.0.1", port=8768, debug=False, use_reloader=False)


if __name__ == "__main__":  # pragma: no cover
    main()

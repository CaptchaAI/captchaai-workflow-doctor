"""Playwright wrappers used by the runner.

Synchronous Playwright API (much simpler than asyncio for our linear
workflow). One :class:`BrowserSession` per workflow run. Action
dispatch maps each :class:`~captchaai_doctor.schemas.Action` onto a
Playwright call.

We deliberately keep this module side-effect-free with respect to the
profile / runner: all the workflow logic lives in
:mod:`captchaai_doctor.runner`.
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    sync_playwright,
)

from captchaai_doctor.detector import read_sitekey as _read_sitekey
from captchaai_doctor.injector import (
    InjectionError,
)
from captchaai_doctor.injector import (
    inject_token as _inject_token,
)
from captchaai_doctor.injector import (
    invoke_callback as _invoke_callback,
)
from captchaai_doctor.schemas import (
    Action,
    ClickAction,
    Detection,
    FillAction,
    InjectTokenAction,
    InvokeCallbackIfDetectedAction,
    WaitAction,
)
from captchaai_doctor.schemas import (
    Browser as BrowserConfig,
)

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping

log = logging.getLogger(__name__)


class BrowserActionError(RuntimeError):
    """An action could not be executed (selector missing, timeout, etc.)."""


@dataclass
class ActionStep:
    """One step recorded by :meth:`BrowserSession.run_actions`."""

    type: str
    selector: str | None
    succeeded: bool
    detail: str | None = None


@dataclass
class BrowserSession:
    """Convenience handle bundling the live browser/context/page + cfg."""

    browser: Browser
    context: BrowserContext
    page: Page
    config: BrowserConfig
    steps: list[ActionStep] = field(default_factory=list)

    # ---- action dispatch ------------------------------------------------

    def run_actions(
        self,
        actions: list[Action],
        *,
        env: Mapping[str, str] | None = None,
        token: str | None = None,
        detection: Detection | None = None,
    ) -> list[ActionStep]:
        """Run ``actions`` in order. First failure stops + raises."""
        env_map = dict(os.environ if env is None else env)
        for action in actions:
            try:
                self._dispatch(action, env_map, token, detection)
                self.steps.append(
                    ActionStep(type=action.type, selector=_selector_of(action), succeeded=True)
                )
            except BrowserActionError as exc:
                self.steps.append(
                    ActionStep(
                        type=action.type,
                        selector=_selector_of(action),
                        succeeded=False,
                        detail=str(exc),
                    )
                )
                raise
        return self.steps

    def _dispatch(
        self,
        action: Action,
        env: Mapping[str, str],
        token: str | None,
        detection: Detection | None,
    ) -> None:
        timeout_ms = self.config.timeout_ms
        if isinstance(action, FillAction):
            value = action.value
            if value is None and action.value_env:
                resolved = env.get(action.value_env)
                if resolved is None:
                    raise BrowserActionError(
                        f"env var {action.value_env!r} not set for fill action on {action.selector!r}"
                    )
                value = resolved
            try:
                self.page.locator(action.selector).first.fill(value or "", timeout=timeout_ms)
            except Exception as exc:
                raise BrowserActionError(f"fill failed for {action.selector!r}: {exc}") from exc
            return

        if isinstance(action, ClickAction):
            try:
                self.page.locator(action.selector).first.click(timeout=timeout_ms)
            except Exception as exc:
                raise BrowserActionError(f"click failed for {action.selector!r}: {exc}") from exc
            return

        if isinstance(action, WaitAction):
            self.page.wait_for_timeout(action.milliseconds)
            return

        if isinstance(action, InjectTokenAction):
            if token is None:
                raise BrowserActionError(
                    "inject_token requires a CAPTCHA token, none was solved yet"
                )
            try:
                _inject_token(self.page, action.selector, token)
            except InjectionError as exc:
                raise BrowserActionError(str(exc)) from exc
            return

        if isinstance(action, InvokeCallbackIfDetectedAction):
            if detection is None or not detection.callback_candidates:
                raise BrowserActionError(
                    "invoke_callback_if_detected requires detection.callback_candidates"
                )
            if token is None:
                raise BrowserActionError(
                    "invoke_callback_if_detected requires a CAPTCHA token, none was solved yet"
                )
            try:
                outcome = _invoke_callback(self.page, list(detection.callback_candidates), token)
            except InjectionError as exc:
                raise BrowserActionError(str(exc)) from exc
            if outcome.error:
                raise BrowserActionError(
                    f"callback {outcome.callback_name!r} threw: {outcome.error}"
                )
            if not outcome.invoked:
                raise BrowserActionError(
                    "none of the callback candidates were defined on the page: "
                    f"{detection.callback_candidates}"
                )
            return

        raise BrowserActionError(  # pragma: no cover
            f"unsupported action type: {action.type}"
        )

    # ---- detection ------------------------------------------------------

    def read_sitekey(self, detection: Detection) -> str | None:
        return _read_sitekey(self.page, detection)

    # ---- screenshots ----------------------------------------------------

    def screenshot(self, path: str) -> str | None:
        if not self.config.screenshots:
            return None
        try:
            self.page.screenshot(path=path, full_page=True)
            return path
        except Exception as exc:
            log.warning("screenshot failed: %s", exc)
            return None


def _selector_of(action: Action) -> str | None:
    return getattr(action, "selector", None)


@contextmanager
def launch_browser(
    config: BrowserConfig, *, headed_override: bool | None = None
) -> Iterator[BrowserSession]:
    """Launch Playwright + an isolated context + a fresh page.

    ``headed_override``: lets the CLI ``--headed`` flag win over the
    profile setting without mutating the (frozen) profile.
    """
    headless = config.headless if headed_override is None else not headed_override
    with sync_playwright() as pw:
        browser = _launch_engine(pw, config.engine, headless=headless)
        context = browser.new_context()
        context.set_default_timeout(config.timeout_ms)
        page = context.new_page()
        try:
            yield BrowserSession(browser=browser, context=context, page=page, config=config)
        finally:
            try:
                context.close()
            finally:
                browser.close()


def _launch_engine(pw: Playwright, engine: str, *, headless: bool) -> Browser:
    if engine == "chromium":
        return pw.chromium.launch(headless=headless)
    if engine == "firefox":
        return pw.firefox.launch(headless=headless)
    if engine == "webkit":
        return pw.webkit.launch(headless=headless)
    raise ValueError(f"unknown browser engine: {engine}")  # pragma: no cover


__all__ = [
    "ActionStep",
    "BrowserActionError",
    "BrowserSession",
    "launch_browser",
]

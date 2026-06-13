"""Simulated browser driver (Faza 7 Task 21).

A fully-offline browser stand-in: it records navigation/form-fill/click/submit/
download actions and returns deterministic page state plus a screenshot
reference, without a real browser or network. This mirrors the project's
offline-placeholder convention (cf. the hashing embedder): a real Playwright /
Chromium driver implements the same :class:`BrowserDriver` port and drops in
without changing the Execution Agent.

Sensitive/egress concerns are decided by the sandbox *before* the driver runs;
this driver assumes its input has already been vetted.
"""
from __future__ import annotations

from urllib.parse import urlparse

from app.modules.execution.domain import actions as A
from app.modules.execution.domain.drivers import BrowserDriver, DriverResult


class SimulatedBrowserDriver(BrowserDriver):
    async def execute(self, action: A.Action) -> DriverResult:
        handler = {
            A.NAVIGATE: self._navigate,
            A.FILL: self._fill,
            A.CLICK: self._click,
            A.SUBMIT: self._submit,
            A.DOWNLOAD: self._download,
            A.SCREENSHOT: self._screenshot,
        }[action.type]
        return handler(action.params)

    @staticmethod
    def _host(params: dict) -> str:
        return urlparse(params.get("url", "")).hostname or "about:blank"

    def _navigate(self, params: dict) -> DriverResult:
        host = self._host(params)
        return DriverResult(
            output={"url": params.get("url"), "title": f"Page at {host}", "status": 200},
            logs=[f"navigated to {params.get('url')}"],
            screenshot=f"screenshot://{host}/navigate",
        )

    def _fill(self, params: dict) -> DriverResult:
        # Never echo the submitted value back — it may be sensitive.
        value = params.get("value", "")
        return DriverResult(
            output={"selector": params.get("selector"), "value_length": len(value)},
            logs=[f"filled {params.get('selector')}"],
        )

    def _click(self, params: dict) -> DriverResult:
        return DriverResult(
            output={"selector": params.get("selector"), "url": params.get("url")},
            logs=[f"clicked {params.get('selector')}"],
        )

    def _submit(self, params: dict) -> DriverResult:
        host = self._host(params)
        return DriverResult(
            output={"submitted": True, "url": params.get("url"), "status": 200},
            logs=[f"submitted form to {params.get('url')}"],
            screenshot=f"screenshot://{host}/submit",
        )

    def _download(self, params: dict) -> DriverResult:
        url = params.get("url", "")
        return DriverResult(
            output={
                "url": url,
                "saved_as": params.get("dest") or url.rsplit("/", 1)[-1] or "download",
                "bytes": max(len(url) * 8, 1),
            },
            logs=[f"downloaded {url}"],
        )

    def _screenshot(self, params: dict) -> DriverResult:
        host = self._host(params)
        return DriverResult(
            output={"captured": True},
            logs=["captured screenshot"],
            screenshot=f"screenshot://{host}/capture",
        )

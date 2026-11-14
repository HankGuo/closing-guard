"""Minimal Chrome DevTools Protocol client for the Android WebView.

The WebView is exposed with:
    adb forward tcp:9222 localabstract:webview_devtools_remote_<pid>

Playwright refuses WebView browser-context management, so this tiny client
talks to the page target directly. It is used by the Android end-to-end test
and by the screenshot/video scripts.
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import json
import urllib.request
from pathlib import Path

import websockets


def page_ws() -> str:
    with urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=10) as r:
        pages = json.load(r)
    if not pages:
        raise RuntimeError("no WebView page; is the app running?")
    return pages[0]["webSocketDebuggerUrl"]


class CDP:
    def __init__(self) -> None:
        self.ws = None
        self._id = 0
        self._pending: dict[int, asyncio.Future] = {}

    async def __aenter__(self) -> "CDP":
        self.ws = await websockets.connect(page_ws(), max_size=64 * 1024 * 1024, ping_interval=None, close_timeout=5)
        asyncio.create_task(self._reader())
        await self.call("Page.enable")
        await self.call("Runtime.enable")
        return self

    async def __aexit__(self, *exc) -> None:
        if self.ws:
            await self.ws.close()

    async def _reader(self) -> None:
        try:
            async for raw in self.ws:  # type: ignore[union-attr]
                msg = json.loads(raw)
                if "id" in msg and msg["id"] in self._pending:
                    fut = self._pending.pop(msg["id"])
                    if not fut.done():
                        fut.set_result(msg)
        except Exception:
            # The WebView closes the socket when the page reloads or the app
            # is backgrounded; pending calls will time out with a clear error.
            return

    async def call(self, method: str, params: dict | None = None, timeout: float = 120) -> dict:
        self._id += 1
        msg_id = self._id
        fut: asyncio.Future = asyncio.get_running_loop().create_future()
        self._pending[msg_id] = fut
        await self.ws.send(json.dumps({"id": msg_id, "method": method, "params": params or {}}))
        return await asyncio.wait_for(fut, timeout=timeout)

    async def eval(self, expression: str, await_promise: bool = True):
        res = await self.call(
            "Runtime.evaluate",
            {
                "expression": expression,
                "awaitPromise": await_promise,
                "returnByValue": True,
                "userGesture": True,
            },
        )
        result = res.get("result", {})
        if "exceptionDetails" in result:
            raise RuntimeError(json.dumps(result["exceptionDetails"], ensure_ascii=False))
        return result.get("result", {}).get("value")

    async def screenshot(self, path: str) -> None:
        res = await self.call("Page.captureScreenshot", {"format": "png"})
        Path(path).write_bytes(base64.b64decode(res["result"]["data"]))

    async def navigate(self, url: str) -> None:
        await self.call("Page.navigate", {"url": url})
        await asyncio.sleep(1.5)


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["eval", "screenshot", "title"])
    parser.add_argument("value", nargs="?")
    args = parser.parse_args()
    async with CDP() as cdp:
        if args.action == "title":
            print(await cdp.eval("document.title"))
        elif args.action == "eval":
            print(json.dumps(await cdp.eval(args.value or "1+1"), ensure_ascii=False, indent=2))
        elif args.action == "screenshot":
            await cdp.screenshot(args.value or "/tmp/webview.png")
            print(args.value or "/tmp/webview.png")


if __name__ == "__main__":
    asyncio.run(main())

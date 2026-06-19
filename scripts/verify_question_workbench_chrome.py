from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


async def verify(endpoint: str, url: str, screenshot_path: Path) -> int:
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp(endpoint)
        except Exception as exc:
            print(f"CDP_UNAVAILABLE: cannot connect to {endpoint}: {exc}")
            print(
                "Start Chrome with remote debugging, for example:\n"
                '  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" '
                "--remote-debugging-port=9222 --user-data-dir=%TEMP%\\chem-admin-cdp"
            )
            return 2

        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        pages = context.pages
        page = next((item for item in pages if "localhost" in item.url and "/question-banks" in item.url), None)
        if page is None:
            page = await context.new_page()
            await page.goto(url, wait_until="networkidle")
        else:
            await page.bring_to_front()
            if "/question-banks" not in page.url:
                await page.goto(url, wait_until="networkidle")

        await page.wait_for_load_state("networkidle")

        repair_button = page.get_by_role("button", name="AI 修正建议").first
        if await repair_button.count() == 0:
            view_button = page.get_by_role("button", name="查看").first
            await view_button.click()
            await page.get_by_text("题目详情").wait_for(timeout=10_000)
            repair_button = page.get_by_role("button", name="AI 修正建议").first
        await repair_button.click()

        try:
            await page.get_by_text("AI 修题工作台").wait_for(timeout=15_000)
            await page.get_by_text("原题上下文").wait_for(timeout=10_000)
            await page.get_by_text("多轮提示").wait_for(timeout=10_000)
            await page.get_by_text("候选版本").wait_for(timeout=10_000)
        except PlaywrightTimeoutError:
            await page.screenshot(path=str(screenshot_path), full_page=True)
            raise

        screenshot_path.parent.mkdir(parents=True, exist_ok=True)
        await page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"OK: screenshot={screenshot_path}")
        await browser.close()
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the AI question workbench by attaching to Chrome over CDP.")
    parser.add_argument("--endpoint", default="http://127.0.0.1:9222")
    parser.add_argument("--url", default="http://localhost:5174/question-banks")
    parser.add_argument("--screenshot", default="artifacts/playwright/question-workbench-cdp.png")
    args = parser.parse_args()
    return asyncio.run(verify(args.endpoint, args.url, Path(args.screenshot)))


if __name__ == "__main__":
    raise SystemExit(main())

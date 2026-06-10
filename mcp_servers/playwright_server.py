from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from mcp.server.fastmcp import FastMCP


PROJECT_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = PROJECT_DIR / "workspace"

mcp = FastMCP(
    "playwright-server",
    instructions=(
        "Browser automation for pages that need JavaScript rendering. Requires "
        "the Python playwright package and installed browser binaries."
    ),
)


def _safe_workspace_path(raw_path: str) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = WORKSPACE_DIR / path

    resolved = path.resolve()
    workspace = WORKSPACE_DIR.resolve()
    if resolved != workspace and not resolved.is_relative_to(workspace):
        raise ValueError(f"Path is outside workspace: {raw_path}")
    return resolved


def _validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https", "file"}:
        raise ValueError("Only http://, https://, and file:// URLs are allowed.")
    if parsed.scheme in {"http", "https"} and not parsed.netloc:
        raise ValueError("URL must include a host.")


def _import_playwright():
    try:
        from playwright.async_api import async_playwright  # type: ignore
    except Exception as exc:
        raise RuntimeError(
            "Playwright support requires: python -m pip install playwright; "
            "python -m playwright install chromium"
        ) from exc
    return async_playwright


async def _open_page(playwright: Any, url: str, timeout_ms: int) -> tuple[Any, Any]:
    browser = await playwright.chromium.launch(headless=True)
    page = await browser.new_page()
    await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
    try:
        await page.wait_for_load_state("networkidle", timeout=min(timeout_ms, 5000))
    except Exception:
        pass
    return browser, page


@mcp.tool()
def playwright_health() -> dict[str, Any]:
    """
    Check whether Python Playwright is importable.
    """
    try:
        _import_playwright()
        return {"ok": True, "tool": "playwright_health", "dependency": "playwright"}
    except Exception as exc:
        return {
            "ok": False,
            "tool": "playwright_health",
            "dependency": "playwright",
            "dependency_failure": True,
            "error": str(exc),
        }


@mcp.tool()
async def playwright_get_text(url: str, selector: str | None = None, timeout_ms: int = 30000, max_chars: int = 12000) -> dict[str, Any]:
    """
    Open a page with Playwright and return visible text.
    """
    try:
        _validate_url(url)
        timeout_ms = max(1000, min(int(timeout_ms), 120000))
        max_chars = max(1, min(int(max_chars), 200000))
        async_playwright = _import_playwright()

        async with async_playwright() as playwright:
            browser, page = await _open_page(playwright, url, timeout_ms)
            locator = page.locator(selector) if selector else page.locator("body")
            text = await locator.inner_text(timeout=timeout_ms)
            title = await page.title()
            final_url = page.url
            await browser.close()

        return {
            "ok": True,
            "tool": "playwright_get_text",
            "url": url,
            "final_url": final_url,
            "title": title,
            "selector": selector,
            "text": text[:max_chars],
            "truncated": len(text) > max_chars,
        }
    except Exception as exc:
        return {"ok": False, "tool": "playwright_get_text", "url": url, "error": str(exc)}


@mcp.tool()
async def playwright_screenshot(url: str, path: str, full_page: bool = True, timeout_ms: int = 30000) -> dict[str, Any]:
    """
    Capture a screenshot into the workspace.
    """
    try:
        _validate_url(url)
        output_path = _safe_workspace_path(path)
        if output_path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
            return {"ok": False, "tool": "playwright_screenshot", "error": "Screenshot path must end with .png, .jpg, or .jpeg.", "path": path}

        timeout_ms = max(1000, min(int(timeout_ms), 120000))
        async_playwright = _import_playwright()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        async with async_playwright() as playwright:
            browser, page = await _open_page(playwright, url, timeout_ms)
            await page.screenshot(path=str(output_path), full_page=full_page)
            title = await page.title()
            final_url = page.url
            await browser.close()

        return {
            "ok": True,
            "tool": "playwright_screenshot",
            "url": url,
            "final_url": final_url,
            "title": title,
            "path": str(output_path.relative_to(WORKSPACE_DIR.resolve())),
        }
    except Exception as exc:
        return {"ok": False, "tool": "playwright_screenshot", "url": url, "path": path, "error": str(exc)}


if __name__ == "__main__":
    mcp.run(transport="stdio")

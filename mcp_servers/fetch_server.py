from __future__ import annotations

import re
import urllib.error
import urllib.request
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlparse

from mcp.server.fastmcp import FastMCP


MAX_FETCH_CHARS = 200_000

mcp = FastMCP(
    "fetch-server",
    instructions=(
        "Fetch HTTP/HTTPS URLs and return readable text. This server is for "
        "retrieving public web pages; it does not execute JavaScript."
    ),
)


class ReadableHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.title_parts: list[str] = []
        self._skip_depth = 0
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1
        elif tag == "title":
            self._in_title = True
        elif tag in {"p", "br", "div", "section", "article", "li", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1
        elif tag == "title":
            self._in_title = False
        elif tag in {"p", "li", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        if self._in_title:
            self.title_parts.append(data)
        self.parts.append(data)

    def text(self) -> str:
        text = " ".join("".join(self.parts).split())
        return re.sub(r"\s*\n\s*", "\n", text).strip()

    def title(self) -> str:
        return " ".join("".join(self.title_parts).split()).strip()


def _validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only http:// and https:// URLs are allowed.")
    if not parsed.netloc:
        raise ValueError("URL must include a host.")


def _decode_body(body: bytes, content_type: str) -> str:
    charset_match = re.search(r"charset=([^;\s]+)", content_type, re.I)
    encoding = charset_match.group(1) if charset_match else "utf-8"
    try:
        return body.decode(encoding, errors="replace")
    except LookupError:
        return body.decode("utf-8", errors="replace")


def _readable_text(raw_text: str, content_type: str) -> tuple[str, str]:
    if "html" not in content_type.lower():
        return raw_text.strip(), ""

    parser = ReadableHTMLParser()
    parser.feed(raw_text)
    return parser.text(), parser.title()


@mcp.tool()
def fetch_url(
    url: str,
    max_chars: int = 12000,
    timeout: int = 20,
    user_agent: str = "my_agents-fetch-mcp/1.0",
) -> dict[str, Any]:
    """
    Fetch a URL and return readable text.
    """
    try:
        _validate_url(url)
        max_chars = max(1, min(int(max_chars), MAX_FETCH_CHARS))
        timeout = max(1, min(int(timeout), 60))

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": user_agent,
                "Accept": "text/html,application/xhtml+xml,text/plain,*/*;q=0.8",
            },
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get("content-type", "")
            body = response.read(MAX_FETCH_CHARS + 1)
            status = getattr(response, "status", None)
            final_url = response.geturl()

        raw_text = _decode_body(body[:MAX_FETCH_CHARS], content_type)
        text, title = _readable_text(raw_text, content_type)
        truncated = len(text) > max_chars or len(body) > MAX_FETCH_CHARS

        return {
            "ok": True,
            "url": url,
            "final_url": final_url,
            "status": status,
            "content_type": content_type,
            "title": title,
            "text": text[:max_chars],
            "truncated": truncated,
            "max_chars": max_chars,
        }
    except urllib.error.HTTPError as exc:
        return {
            "ok": False,
            "url": url,
            "status": exc.code,
            "error": str(exc),
        }
    except Exception as exc:
        return {
            "ok": False,
            "url": url,
            "error": str(exc),
        }


if __name__ == "__main__":
    mcp.run(transport="stdio")

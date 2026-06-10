from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from typing import Any

from mcp.server.fastmcp import FastMCP


mcp = FastMCP(
    "search-server",
    instructions=(
        "Search the web using configured providers. Prefer Brave or Tavily API "
        "keys when available; use DuckDuckGo HTML only as best-effort fallback."
    ),
)


class DuckDuckGoParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.results: list[dict[str, str]] = []
        self._in_result_link = False
        self._in_snippet = False
        self._current_href = ""
        self._current_text: list[str] = []
        self._current_snippet: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key: value or "" for key, value in attrs}
        css_class = attrs_dict.get("class", "")

        if tag.lower() == "a" and ("result__a" in css_class or "result-link" in css_class):
            self._in_result_link = True
            self._current_href = attrs_dict.get("href", "")
            self._current_text = []
        elif tag.lower() == "td" and "result-snippet" in css_class:
            self._in_snippet = True
            self._current_snippet = []

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._in_result_link:
            title = " ".join("".join(self._current_text).split())
            href = self._clean_href(self._current_href)
            if title and href:
                self.results.append({"title": title, "url": href, "snippet": ""})
            self._in_result_link = False
        elif tag.lower() == "td" and self._in_snippet:
            snippet = " ".join("".join(self._current_snippet).split())
            if snippet and self.results and not self.results[-1].get("snippet"):
                self.results[-1]["snippet"] = snippet
            self._in_snippet = False

    def handle_data(self, data: str) -> None:
        if self._in_result_link:
            self._current_text.append(data)
        elif self._in_snippet:
            self._current_snippet.append(data)

    @staticmethod
    def _clean_href(href: str) -> str:
        if href.startswith("//duckduckgo.com/l/?"):
            parsed = urllib.parse.urlparse("https:" + href)
            query = urllib.parse.parse_qs(parsed.query)
            uddg = query.get("uddg", [""])[0]
            return urllib.parse.unquote(uddg)
        return href


def _request_json(url: str, *, method: str = "GET", data: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> dict[str, Any]:
    body = None
    request_headers = dict(headers or {})
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        request_headers.setdefault("Content-Type", "application/json")

    request = urllib.request.Request(url, data=body, headers=request_headers, method=method)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def _search_tavily(query: str, limit: int) -> list[dict[str, Any]]:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError("TAVILY_API_KEY is not configured.")

    payload = _request_json(
        "https://api.tavily.com/search",
        method="POST",
        data={
            "api_key": api_key,
            "query": query,
            "max_results": limit,
            "include_answer": False,
        },
    )
    return [
        {
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "snippet": item.get("content", ""),
            "score": item.get("score"),
        }
        for item in payload.get("results", [])
    ]


def _search_brave(query: str, limit: int) -> list[dict[str, Any]]:
    api_key = os.getenv("BRAVE_SEARCH_API_KEY")
    if not api_key:
        raise RuntimeError("BRAVE_SEARCH_API_KEY is not configured.")

    url = "https://api.search.brave.com/res/v1/web/search?" + urllib.parse.urlencode(
        {"q": query, "count": limit}
    )
    payload = _request_json(
        url,
        headers={
            "X-Subscription-Token": api_key,
            "Accept": "application/json",
        },
    )
    results = payload.get("web", {}).get("results", [])
    return [
        {
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "snippet": re.sub("<[^>]+>", "", item.get("description", "")),
        }
        for item in results
    ]


def _search_duckduckgo(query: str, limit: int) -> list[dict[str, Any]]:
    url = "https://lite.duckduckgo.com/lite/?" + urllib.parse.urlencode({"q": query})
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 my_agents-search-mcp/1.0",
            "Accept": "text/html,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        html = response.read().decode("utf-8", errors="replace")

    parser = DuckDuckGoParser()
    parser.feed(html)
    return parser.results[:limit]


def _provider_order() -> list[str]:
    preferred = os.getenv("SEARCH_PROVIDER", "").strip().lower()
    if preferred:
        return [preferred]
    if os.getenv("BRAVE_SEARCH_API_KEY"):
        return ["brave"]
    if os.getenv("TAVILY_API_KEY"):
        return ["tavily"]
    return ["duckduckgo"]


@mcp.tool()
def search_health() -> dict[str, Any]:
    """
    Return configured search providers.
    """
    return {
        "ok": True,
        "tool": "search_health",
        "providers": _provider_order(),
        "has_brave_key": bool(os.getenv("BRAVE_SEARCH_API_KEY")),
        "has_tavily_key": bool(os.getenv("TAVILY_API_KEY")),
        "fallback": "duckduckgo_lite_html",
    }


@mcp.tool()
def web_search(query: str, limit: int = 5) -> dict[str, Any]:
    """
    Search the web and return title/url/snippet results.
    """
    if not query or not query.strip():
        return {"ok": False, "tool": "web_search", "error": "Query is empty.", "results": []}

    limit = max(1, min(int(limit), 10))
    errors = []
    for provider in _provider_order():
        try:
            if provider == "brave":
                results = _search_brave(query, limit)
            elif provider == "tavily":
                results = _search_tavily(query, limit)
            elif provider == "duckduckgo":
                results = _search_duckduckgo(query, limit)
            else:
                raise RuntimeError(f"Unknown SEARCH_PROVIDER: {provider}")

            return {
                "ok": True,
                "tool": "web_search",
                "provider": provider,
                "query": query,
                "limit": limit,
                "results": results,
                "best_effort": provider == "duckduckgo",
            }
        except Exception as exc:
            errors.append({"provider": provider, "error": str(exc)})

    return {
        "ok": False,
        "tool": "web_search",
        "query": query,
        "errors": errors,
        "results": [],
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")

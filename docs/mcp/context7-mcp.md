# Context7 MCP

## Purpose

Context7 MCP dùng để tra documentation thư viện khi agent cần thông tin API/library.

## Server

- Server name: `context7`
- Package: `@upstash/context7-mcp`
- Transport: stdio via `npx`
- Optional env: `CONTEXT7_API_KEY`

## Tools

- `context7.resolve-library-id`
- `context7.query-docs`

## Flow

1. Resolve library id:

```json
{
  "tool": "context7.resolve-library-id",
  "args": {
    "libraryName": "react",
    "query": "hooks docs"
  }
}
```

2. Query docs:

```json
{
  "tool": "context7.query-docs",
  "args": {
    "libraryId": "/facebook/react",
    "query": "useEffect cleanup"
  }
}
```

## When To Use

- Library API uncertain.
- Need current-ish docs without general web search.
- User asks implementation details of a framework/library.

## When Not To Use

- Local project code questions: use Code Index/File Editor first.
- Current news or general web: use Search/Fetch MCP.


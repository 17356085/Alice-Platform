"""
MCP Browser Server — expose browser capabilities as MCP tools.

Any MCP-compatible AI client (Claude Desktop, Cursor, etc.) can control
a browser through this server. Wraps the Runtime abstraction so it works
with BrowserUse, Playwright, or Remote Browser backends.

Tools exposed:
  - browser_navigate:  Navigate to a URL or hash route
  - browser_observe:   Extract page structure (title, fields, buttons, table)
  - browser_click:     Click an element by text description
  - browser_type:      Type into an input field
  - browser_screenshot: Capture page screenshot (base64)
  - browser_execute:   Run a natural-language action
  - browser_login:     Log in with credentials
  - browser_close:     Close the browser session

Usage:
    python -m aitest.mcp.browser_server

    # With custom runtime:
    AITEST_BROWSER_BACKEND=remote BROWSER_WS_URL=ws://host:9222/cdp \
        python -m aitest.mcp.browser_server

Configuration (env vars):
    AITEST_BROWSER_BACKEND  — "browser_use" (default) | "remote"
    BROWSER_WS_URL          — CDP endpoint for remote backend
    BASE_URL                — SUT base URL
"""

import os
import asyncio
import json
import base64
from typing import Optional

# ── Tool definitions (MCP JSON Schema) ────────────────────────────────

BROWSER_TOOLS = [
    {
        "name": "browser_navigate",
        "description": "Navigate browser to a URL or hash route. E.g., '#/equipment/device' or 'https://example.com'.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "URL or hash route to navigate to.",
                },
            },
            "required": ["target"],
        },
    },
    {
        "name": "browser_observe",
        "description": "Extract page structure: title, search fields, action buttons, table columns.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "browser_click",
        "description": "Click an element described in natural language. E.g., '新增按钮', 'submit button'.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Natural language description of the element to click.",
                },
            },
            "required": ["description"],
        },
    },
    {
        "name": "browser_type",
        "description": "Type text into an input field described in natural language.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "field": {
                    "type": "string",
                    "description": "Description of the input field (e.g., '设备名称').",
                },
                "value": {
                    "type": "string",
                    "description": "Text to type into the field.",
                },
            },
            "required": ["field", "value"],
        },
    },
    {
        "name": "browser_screenshot",
        "description": "Capture a screenshot of the current page. Returns base64-encoded PNG.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "browser_execute",
        "description": "Execute a natural-language action on the page (AI-driven).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Natural language description of the action.",
                },
            },
            "required": ["action"],
        },
    },
    {
        "name": "browser_login",
        "description": "Perform login with provided credentials.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "username": {"type": "string"},
                "password": {"type": "string"},
            },
            "required": ["username", "password"],
        },
    },
    {
        "name": "browser_close",
        "description": "Close the browser session.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
]


# ── Browser MCP Server ─────────────────────────────────────────────────

class BrowserMCPServer:
    """MCP-compatible server wrapping a browser Runtime."""

    def __init__(self):
        self._runtime = None
        self._backend = os.environ.get("AITEST_BROWSER_BACKEND", "browser_use")

    async def _get_runtime(self):
        """Lazy-init the appropriate Runtime backend."""
        if self._runtime is not None:
            return self._runtime

        from aitest.config import config

        if self._backend == "remote":
            from aitest.platform.runtime import RemoteBrowserRuntime
            self._runtime = RemoteBrowserRuntime(
                ws_url=config.browser_ws_url,
                api_key=config.browser_api_key,
                base_url=config.base_url,
            )
        else:
            from aitest.platform.runtime import BrowserRuntime
            self._runtime = BrowserRuntime(
                base_url=config.base_url,
                headless=False,
            )

        return self._runtime

    def list_tools(self) -> list[dict]:
        return BROWSER_TOOLS

    async def call_tool(self, name: str, arguments: dict) -> list[dict]:
        """Handle a tool call, return MCP Content items."""
        rt = await self._get_runtime()

        try:
            if name == "browser_navigate":
                await rt.navigate(arguments["target"])
                return [{"type": "text", "text": f"Navigated to: {arguments['target']}"}]

            elif name == "browser_observe":
                structure = await rt.observe()
                return [{"type": "text", "text": json.dumps({
                    "page_title": structure.page_title,
                    "search_fields": structure.search_fields,
                    "action_buttons": structure.action_buttons,
                    "table_columns": structure.table_columns,
                    "has_pagination": structure.has_pagination,
                }, ensure_ascii=False, indent=2)}]

            elif name == "browser_click":
                ok = await rt.click(arguments["description"])
                return [{"type": "text", "text": f"Click {'succeeded' if ok else 'failed'}: {arguments['description']}"}]

            elif name == "browser_type":
                ok = await rt.type(arguments["field"], arguments["value"])
                return [{"type": "text", "text": f"Type {'succeeded' if ok else 'failed'}: {arguments['field']} = {arguments['value']}"}]

            elif name == "browser_screenshot":
                img_bytes = await rt.screenshot()
                b64 = base64.b64encode(img_bytes).decode("utf-8") if img_bytes else ""
                return [{"type": "image", "data": b64, "mimeType": "image/png"}]

            elif name == "browser_execute":
                result = await rt.execute(arguments["action"])
                return [{"type": "text", "text": str(result)}]

            elif name == "browser_login":
                ok = await rt.login({"username": arguments["username"], "password": arguments["password"]})
                return [{"type": "text", "text": f"Login {'succeeded' if ok else 'failed'}"}]

            elif name == "browser_close":
                await rt.close()
                self._runtime = None
                return [{"type": "text", "text": "Browser closed"}]

            else:
                return [{"type": "text", "text": f"Unknown tool: {name}"}]

        except Exception as e:
            return [{"type": "text", "text": f"Error: {type(e).__name__}: {e}"}]


# ── MCP stdio server entry point ───────────────────────────────────────

async def main():
    """MCP stdio server — JSON-RPC over stdin/stdout."""
    import sys

    server = BrowserMCPServer()

    # Write capabilities (non-standard, for discovery)
    tools = server.list_tools()

    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            request = json.loads(line.strip())
            method = request.get("method", "")
            req_id = request.get("id")

            if method == "tools/list":
                response = {"jsonrpc": "2.0", "id": req_id, "result": {"tools": tools}}

            elif method == "tools/call":
                params = request.get("params", {})
                tool_name = params.get("name", "")
                arguments = params.get("arguments", {})
                content = await server.call_tool(tool_name, arguments)
                response = {"jsonrpc": "2.0", "id": req_id, "result": {"content": content}}

            elif method == "initialize":
                response = {
                    "jsonrpc": "2.0", "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "serverInfo": {"name": "aitest-browser", "version": "0.2.0"},
                        "capabilities": {"tools": {}},
                    },
                }

            else:
                response = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}

            sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            sys.stdout.flush()

        except json.JSONDecodeError:
            continue
        except Exception as e:
            err_resp = {"jsonrpc": "2.0", "id": req_id if 'req_id' in dir() else None,
                        "error": {"code": -32603, "message": str(e)}}
            sys.stdout.write(json.dumps(err_resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    asyncio.run(main())

"""MCP server for Door43 open content — free Bible resources and translations."""

from __future__ import annotations

from typing import Any

import httpx
from mcp.types import Tool

from .base import BaseBibleMcpServer

DOOR43_CATALOG_URL = "https://git.door43.org/api/v1/catalog/search"
DOOR43_CONTENT_URL = "https://git.door43.org/api/v1/repos"


class OpenContentMcpServer(BaseBibleMcpServer):
    def __init__(self):
        super().__init__("mcp-open-content")

    def get_tools(self) -> list[Tool]:
        return [
            Tool(
                name="door43.catalog.search",
                description="Search Door43 Content Service catalog for Bible resources",
                inputSchema={
                    "type": "object",
                    "required": ["query"],
                    "properties": {
                        "query": {"type": "string"},
                        "language": {"type": "string", "default": "en"},
                        "subject": {
                            "type": "string",
                            "description": "e.g. 'Bible', 'Translation Notes'",
                        },
                    },
                },
            ),
            Tool(
                name="door43.resource.fetch",
                description="Fetch a specific resource from Door43 by owner/repo path",
                inputSchema={
                    "type": "object",
                    "required": ["owner", "repo", "path"],
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "path": {"type": "string"},
                    },
                },
            ),
        ]

    async def execute_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name == "door43.catalog.search":
            query = arguments["query"]
            language = arguments.get("language", "en")
            subject = arguments.get("subject", "")
            params: dict[str, str] = {"q": query, "lang": language}
            if subject:
                params["subject"] = subject
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                try:
                    resp = await client.get(DOOR43_CATALOG_URL, params=params)
                    if resp.status_code == 200:
                        return {"results": resp.json().get("data", []), "query": query}
                except httpx.HTTPError:
                    pass
            return {"results": [], "query": query}

        elif name == "door43.resource.fetch":
            owner = arguments["owner"]
            repo = arguments["repo"]
            path = arguments["path"]
            url = f"{DOOR43_CONTENT_URL}/{owner}/{repo}/contents/{path}"
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                try:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        return resp.json()
                except httpx.HTTPError:
                    pass
            return {"error": "Resource not found", "path": f"{owner}/{repo}/{path}"}

        raise ValueError(f"Unknown tool: {name}")

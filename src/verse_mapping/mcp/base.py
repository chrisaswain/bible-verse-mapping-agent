"""Base MCP server class with tools/list and tools/call support."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent


class BaseBibleMcpServer(ABC):
    """Base class for all Bible data MCP servers."""

    def __init__(self, name: str):
        self.name = name
        self.server = Server(name)
        self._register_handlers()

    def _register_handlers(self) -> None:
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return self.get_tools()

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            result = await self.execute_tool(name, arguments)
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

    @abstractmethod
    def get_tools(self) -> list[Tool]:
        ...

    @abstractmethod
    async def execute_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        ...

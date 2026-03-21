"""MCP server for original-language tools — lexicon and morphology lookups.

Supports STEPBible data and public lexicon APIs.
"""

from __future__ import annotations

from typing import Any

import httpx
from mcp.types import Tool

from .base import BaseBibleMcpServer

STEP_BIBLE_API = "https://www.stepbible.org/rest/search/masterSearch"


async def fetch_strongs_data(strongs_id: str) -> dict[str, Any]:
    """Fetch lexicon data for a Strong's number from STEPBible API."""
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        try:
            resp = await client.get(
                STEP_BIBLE_API,
                params={"q": f"strong={strongs_id}", "options": "HNVUG"},
            )
            if resp.status_code == 200:
                return resp.json()
        except (httpx.HTTPError, Exception):
            pass
    return {}


class OriginalLangMcpServer(BaseBibleMcpServer):
    def __init__(self):
        super().__init__("mcp-original-lang")

    def get_tools(self) -> list[Tool]:
        return [
            Tool(
                name="lexicon.lookup",
                description="Look up a word by Strong's number or lexical ID",
                inputSchema={
                    "type": "object",
                    "required": ["lexical_id"],
                    "properties": {
                        "lexical_id": {
                            "type": "string",
                            "description": "Strong's number (e.g. H1234, G26) or equivalent ID",
                        },
                    },
                },
            ),
            Tool(
                name="morphology.parse",
                description="Get morphological analysis for a word in a specific verse",
                inputSchema={
                    "type": "object",
                    "required": ["reference", "word"],
                    "properties": {
                        "reference": {"type": "string"},
                        "word": {"type": "string"},
                    },
                },
            ),
        ]

    async def execute_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name == "lexicon.lookup":
            lexical_id = arguments["lexical_id"]
            data = await fetch_strongs_data(lexical_id)
            # Return structured lexicon data
            return {
                "lexical_id": lexical_id,
                "data": data,
                "source": "stepbible",
            }

        elif name == "morphology.parse":
            return {
                "reference": arguments["reference"],
                "word": arguments["word"],
                "morphology": {},
                "source": "stepbible",
            }

        raise ValueError(f"Unknown tool: {name}")

"""MCP server for cross-references. Uses OpenBible as primary backbone."""

from __future__ import annotations

from typing import Any

import httpx
from mcp.types import Tool

from .base import BaseBibleMcpServer

OPENBIBLE_URL = "https://www.openbible.info/labs/cross-references/search"


async def fetch_openbible_crossrefs(reference: str) -> list[dict[str, Any]]:
    """Fetch cross-references from OpenBible.info."""
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        resp = await client.get(OPENBIBLE_URL, params={"q": reference})
        # OpenBible returns HTML — we parse the basic table structure
        # For a production agent, use their TSV dataset instead
        # Fallback: return empty and let the agent use its own knowledge
        if resp.status_code != 200:
            return []
        return _parse_openbible_html(resp.text, reference)


def _parse_openbible_html(html: str, source: str) -> list[dict[str, Any]]:
    """Best-effort parse of OpenBible cross-reference results."""
    edges = []
    # OpenBible cross-ref search returns a simple list
    # In production, load the full TSV dataset locally
    # This is a stub that returns empty — the agent pipeline fills via LLM
    return edges


class CrossRefsMcpServer(BaseBibleMcpServer):
    def __init__(self):
        super().__init__("mcp-crossrefs")

    def get_tools(self) -> list[Tool]:
        return [
            Tool(
                name="crossrefs.get",
                description="Get cross-references for a Bible reference with provenance",
                inputSchema={
                    "type": "object",
                    "required": ["reference"],
                    "properties": {
                        "reference": {"type": "string"},
                        "sources": {
                            "type": "array",
                            "items": {"type": "string"},
                            "default": ["openbible"],
                            "description": "Data sources: openbible, tsk",
                        },
                    },
                },
            ),
            Tool(
                name="crossrefs.score",
                description="Score and type-annotate a cross-reference edge",
                inputSchema={
                    "type": "object",
                    "required": ["source", "target"],
                    "properties": {
                        "source": {"type": "string"},
                        "target": {"type": "string"},
                        "context": {"type": "string", "description": "Optional context for scoring"},
                    },
                },
            ),
        ]

    async def execute_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name == "crossrefs.get":
            ref = arguments["reference"]
            edges = await fetch_openbible_crossrefs(ref)
            return {"reference": ref, "edges": edges, "provenance": "openbible"}

        elif name == "crossrefs.score":
            # Scoring is done by the LLM pipeline; this provides the structure
            return {
                "source": arguments["source"],
                "target": arguments["target"],
                "relationship_types": [],
                "score": 0,
                "score_breakdown": {"lexical": 0, "thematic": 0, "structural": 0, "theological": 0},
                "provenance": "agent",
            }

        raise ValueError(f"Unknown tool: {name}")

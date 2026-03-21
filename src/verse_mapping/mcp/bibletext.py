"""MCP server for Bible text retrieval and translation comparison.

Uses free APIs: bible-api.com (KJV/WEB) and bolls.life (multiple translations).
"""

from __future__ import annotations

from typing import Any

import httpx
from mcp.types import Tool

from .base import BaseBibleMcpServer

# Free API endpoints
BIBLE_API_URL = "https://bible-api.com"
BOLLS_API_URL = "https://bolls.life/get-verse"

# Translation IDs available on bolls.life
BOLLS_TRANSLATIONS = {
    "KJV": "KJV",
    "ASV": "ASV",
    "WEB": "WEB",
    "YLT": "YLT",
    "BBE": "BBE",
}


def _build_bible_api_ref(book: str, chapter: int, verse_start: int, verse_end: int | None) -> str:
    """Build a bible-api.com compatible reference string."""
    ref = f"{book} {chapter}:{verse_start}"
    if verse_end and verse_end != verse_start:
        ref += f"-{verse_end}"
    return ref


async def fetch_bible_api(
    reference: str, translation: str = "kjv"
) -> dict[str, Any]:
    """Fetch verse text from bible-api.com (supports KJV and WEB)."""
    url = f"{BIBLE_API_URL}/{reference}"
    params = {"translation": translation.lower()}
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()


async def fetch_bolls(
    book_id: int, chapter: int, verse: int, translation: str = "KJV"
) -> dict[str, Any]:
    """Fetch a single verse from bolls.life API."""
    url = f"{BOLLS_API_URL}/{translation}/{book_id}/{chapter}/{verse}"
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()


class BibleTextMcpServer(BaseBibleMcpServer):
    def __init__(self):
        super().__init__("mcp-bibletext")

    def get_tools(self) -> list[Tool]:
        return [
            Tool(
                name="bibletext.get",
                description="Fetch Bible text for a reference in a specific translation",
                inputSchema={
                    "type": "object",
                    "required": ["reference"],
                    "properties": {
                        "reference": {"type": "string", "description": "e.g. 'John 3:16'"},
                        "translation": {"type": "string", "default": "KJV"},
                    },
                },
            ),
            Tool(
                name="bibletext.compare_translations",
                description="Compare a verse across multiple translations. Always used in Step 2.",
                inputSchema={
                    "type": "object",
                    "required": ["reference", "translations"],
                    "properties": {
                        "reference": {"type": "string"},
                        "translations": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of translation codes",
                        },
                    },
                },
            ),
        ]

    async def execute_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name == "bibletext.get":
            ref = arguments["reference"]
            translation = arguments.get("translation", "KJV")
            try:
                data = await fetch_bible_api(ref, translation)
                return {
                    "reference": ref,
                    "translation": translation,
                    "text": data.get("text", "").strip(),
                    "verses": data.get("verses", []),
                }
            except httpx.HTTPError as e:
                return {"error": str(e), "reference": ref, "translation": translation}

        elif name == "bibletext.compare_translations":
            ref = arguments["reference"]
            translations = arguments["translations"]
            renderings = []
            for t in translations:
                try:
                    data = await fetch_bible_api(ref, t)
                    renderings.append({
                        "translation": t,
                        "text": data.get("text", "").strip(),
                    })
                except httpx.HTTPError:
                    renderings.append({"translation": t, "text": None, "error": "unavailable"})
            # Compute variant signals
            variant_signals = _compute_variant_signals(renderings)
            return {
                "reference": ref,
                "renderings": renderings,
                "variant_signals": variant_signals,
            }

        raise ValueError(f"Unknown tool: {name}")


def _compute_variant_signals(renderings: list[dict]) -> list[dict]:
    """Identify key differences between translation renderings."""
    signals = []
    texts = {r["translation"]: r.get("text", "") for r in renderings if r.get("text")}
    if len(texts) < 2:
        return signals

    # Simple word-diff heuristic: find words unique to specific translations
    all_words: dict[str, set[str]] = {}
    for t, text in texts.items():
        words = set(text.lower().split())
        for w in words:
            all_words.setdefault(w, set()).add(t)

    for word, trans in all_words.items():
        if 1 < len(trans) < len(texts) and len(word) > 3:
            signals.append({
                "keyword": word,
                "translations_differ": sorted(set(texts.keys()) - trans),
                "impact": f"Word '{word}' appears in {sorted(trans)} but not all translations",
            })
            if len(signals) >= 10:
                break

    return signals

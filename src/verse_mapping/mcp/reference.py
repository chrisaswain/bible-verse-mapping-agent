"""MCP server for reference parsing — normalizes human reference strings into verse spans."""

from __future__ import annotations

import re
from typing import Any

from mcp.types import Tool

from .base import BaseBibleMcpServer

# Book name normalization map (abbreviated -> canonical)
BOOK_ALIASES: dict[str, str] = {
    "gen": "Genesis", "genesis": "Genesis",
    "exod": "Exodus", "exodus": "Exodus", "ex": "Exodus",
    "lev": "Leviticus", "leviticus": "Leviticus",
    "num": "Numbers", "numbers": "Numbers",
    "deut": "Deuteronomy", "deuteronomy": "Deuteronomy",
    "josh": "Joshua", "joshua": "Joshua",
    "judg": "Judges", "judges": "Judges",
    "ruth": "Ruth",
    "1sam": "1 Samuel", "1 samuel": "1 Samuel", "1 sam": "1 Samuel",
    "2sam": "2 Samuel", "2 samuel": "2 Samuel", "2 sam": "2 Samuel",
    "1kgs": "1 Kings", "1 kings": "1 Kings", "1 kgs": "1 Kings",
    "2kgs": "2 Kings", "2 kings": "2 Kings", "2 kgs": "2 Kings",
    "1chr": "1 Chronicles", "1 chronicles": "1 Chronicles", "1 chron": "1 Chronicles",
    "2chr": "2 Chronicles", "2 chronicles": "2 Chronicles", "2 chron": "2 Chronicles",
    "ezra": "Ezra", "neh": "Nehemiah", "nehemiah": "Nehemiah",
    "est": "Esther", "esther": "Esther",
    "job": "Job",
    "ps": "Psalms", "psa": "Psalms", "psalm": "Psalms", "psalms": "Psalms",
    "prov": "Proverbs", "proverbs": "Proverbs",
    "eccl": "Ecclesiastes", "ecclesiastes": "Ecclesiastes",
    "song": "Song of Solomon", "song of solomon": "Song of Solomon", "sos": "Song of Solomon",
    "isa": "Isaiah", "isaiah": "Isaiah",
    "jer": "Jeremiah", "jeremiah": "Jeremiah",
    "lam": "Lamentations", "lamentations": "Lamentations",
    "ezek": "Ezekiel", "ezekiel": "Ezekiel",
    "dan": "Daniel", "daniel": "Daniel",
    "hos": "Hosea", "hosea": "Hosea",
    "joel": "Joel", "amos": "Amos",
    "obad": "Obadiah", "obadiah": "Obadiah",
    "jonah": "Jonah", "jon": "Jonah",
    "mic": "Micah", "micah": "Micah",
    "nah": "Nahum", "nahum": "Nahum",
    "hab": "Habakkuk", "habakkuk": "Habakkuk",
    "zeph": "Zephaniah", "zephaniah": "Zephaniah",
    "hag": "Haggai", "haggai": "Haggai",
    "zech": "Zechariah", "zechariah": "Zechariah",
    "mal": "Malachi", "malachi": "Malachi",
    "matt": "Matthew", "matthew": "Matthew", "mt": "Matthew",
    "mark": "Mark", "mk": "Mark",
    "luke": "Luke", "lk": "Luke",
    "john": "John", "jn": "John",
    "acts": "Acts",
    "rom": "Romans", "romans": "Romans",
    "1cor": "1 Corinthians", "1 corinthians": "1 Corinthians", "1 cor": "1 Corinthians",
    "2cor": "2 Corinthians", "2 corinthians": "2 Corinthians", "2 cor": "2 Corinthians",
    "gal": "Galatians", "galatians": "Galatians",
    "eph": "Ephesians", "ephesians": "Ephesians",
    "phil": "Philippians", "philippians": "Philippians",
    "col": "Colossians", "colossians": "Colossians",
    "1thess": "1 Thessalonians", "1 thessalonians": "1 Thessalonians", "1 thess": "1 Thessalonians",
    "2thess": "2 Thessalonians", "2 thessalonians": "2 Thessalonians", "2 thess": "2 Thessalonians",
    "1tim": "1 Timothy", "1 timothy": "1 Timothy", "1 tim": "1 Timothy",
    "2tim": "2 Timothy", "2 timothy": "2 Timothy", "2 tim": "2 Timothy",
    "titus": "Titus", "tit": "Titus",
    "phlm": "Philemon", "philemon": "Philemon",
    "heb": "Hebrews", "hebrews": "Hebrews",
    "jas": "James", "james": "James",
    "1pet": "1 Peter", "1 peter": "1 Peter", "1 pet": "1 Peter",
    "2pet": "2 Peter", "2 peter": "2 Peter", "2 pet": "2 Peter",
    "1john": "1 John", "1 john": "1 John", "1 jn": "1 John",
    "2john": "2 John", "2 john": "2 John", "2 jn": "2 John",
    "3john": "3 John", "3 john": "3 John", "3 jn": "3 John",
    "jude": "Jude",
    "rev": "Revelation", "revelation": "Revelation",
}

# Pattern: "Book Chapter:Verse(-Verse)"
_REF_PATTERN = re.compile(
    r"(?P<book>(?:\d\s*)?[A-Za-z]+(?:\s+[A-Za-z]+)*)\s+"
    r"(?P<chapter>\d+)"
    r"(?::(?P<vstart>\d+)(?:\s*[-–]\s*(?P<vend>\d+))?)?"
)


def parse_reference(raw: str) -> list[dict[str, Any]]:
    """Parse a human reference string into a list of verse span dicts."""
    spans = []
    # Split on semicolons for multiple references
    segments = [s.strip() for s in raw.split(";")]
    for segment in segments:
        m = _REF_PATTERN.search(segment)
        if not m:
            continue
        book_raw = m.group("book").strip()
        book_key = book_raw.lower()
        book = BOOK_ALIASES.get(book_key, book_raw)
        chapter = int(m.group("chapter"))
        vstart = int(m.group("vstart")) if m.group("vstart") else 1
        vend = int(m.group("vend")) if m.group("vend") else None
        spans.append({
            "book": book,
            "chapter": chapter,
            "verse_start": vstart,
            "verse_end": vend,
        })
    return spans


class ReferenceMcpServer(BaseBibleMcpServer):
    def __init__(self):
        super().__init__("mcp-reference")

    def get_tools(self) -> list[Tool]:
        return [
            Tool(
                name="reference.parse",
                description="Parse a human reference string into normalized verse spans",
                inputSchema={
                    "type": "object",
                    "required": ["reference"],
                    "properties": {
                        "reference": {
                            "type": "string",
                            "description": "Human-readable Bible reference (e.g. 'Rom 3:21-26; Eph 2:8-10')",
                        }
                    },
                },
            )
        ]

    async def execute_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name == "reference.parse":
            raw = arguments["reference"]
            spans = parse_reference(raw)
            return {"raw": raw, "spans": spans}
        raise ValueError(f"Unknown tool: {name}")

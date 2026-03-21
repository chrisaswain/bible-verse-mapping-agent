"""Tests for MCP server tool discovery and invocation."""

from __future__ import annotations

import pytest

from verse_mapping.mcp.reference import ReferenceMcpServer, parse_reference
from verse_mapping.mcp.bibletext import BibleTextMcpServer
from verse_mapping.mcp.crossrefs import CrossRefsMcpServer
from verse_mapping.mcp.original_lang import OriginalLangMcpServer
from verse_mapping.mcp.open_content import OpenContentMcpServer


class TestReferenceParsing:
    def test_single_verse(self):
        spans = parse_reference("John 3:16")
        assert len(spans) == 1
        assert spans[0]["book"] == "John"
        assert spans[0]["chapter"] == 3
        assert spans[0]["verse_start"] == 16
        assert spans[0]["verse_end"] is None

    def test_verse_range(self):
        spans = parse_reference("Romans 3:21-26")
        assert len(spans) == 1
        assert spans[0]["book"] == "Romans"
        assert spans[0]["verse_start"] == 21
        assert spans[0]["verse_end"] == 26

    def test_multiple_references(self):
        spans = parse_reference("Rom 3:21-26; Eph 2:8-10")
        assert len(spans) == 2
        assert spans[0]["book"] == "Romans"
        assert spans[1]["book"] == "Ephesians"

    def test_abbreviated_book(self):
        spans = parse_reference("Gen 22")
        assert len(spans) == 1
        assert spans[0]["book"] == "Genesis"

    def test_numbered_book(self):
        spans = parse_reference("1 Tim 2:11-15")
        assert len(spans) == 1
        assert spans[0]["book"] == "1 Timothy"

    def test_full_book_name(self):
        spans = parse_reference("Revelation 21:1-4")
        assert len(spans) == 1
        assert spans[0]["book"] == "Revelation"


class TestToolDiscovery:
    """Every MCP server must expose tools via get_tools()."""

    def test_reference_server_tools(self):
        server = ReferenceMcpServer()
        tools = server.get_tools()
        assert len(tools) >= 1
        names = [t.name for t in tools]
        assert "reference.parse" in names

    def test_bibletext_server_tools(self):
        server = BibleTextMcpServer()
        tools = server.get_tools()
        names = [t.name for t in tools]
        assert "bibletext.get" in names
        assert "bibletext.compare_translations" in names

    def test_crossrefs_server_tools(self):
        server = CrossRefsMcpServer()
        tools = server.get_tools()
        names = [t.name for t in tools]
        assert "crossrefs.get" in names

    def test_original_lang_server_tools(self):
        server = OriginalLangMcpServer()
        tools = server.get_tools()
        names = [t.name for t in tools]
        assert "lexicon.lookup" in names

    def test_open_content_server_tools(self):
        server = OpenContentMcpServer()
        tools = server.get_tools()
        names = [t.name for t in tools]
        assert "door43.catalog.search" in names
        assert "door43.resource.fetch" in names


class TestToolSchemas:
    """Every tool must have an inputSchema."""

    @pytest.mark.parametrize("server_cls", [
        ReferenceMcpServer,
        BibleTextMcpServer,
        CrossRefsMcpServer,
        OriginalLangMcpServer,
        OpenContentMcpServer,
    ])
    def test_all_tools_have_input_schema(self, server_cls):
        server = server_cls()
        for tool in server.get_tools():
            assert tool.inputSchema is not None
            assert "type" in tool.inputSchema
            assert tool.inputSchema["type"] == "object"


class TestToolInvocation:
    @pytest.mark.asyncio
    async def test_reference_parse(self):
        server = ReferenceMcpServer()
        result = await server.execute_tool("reference.parse", {"reference": "John 3:16"})
        assert result["raw"] == "John 3:16"
        assert len(result["spans"]) == 1

    @pytest.mark.asyncio
    async def test_unknown_tool_raises(self):
        server = ReferenceMcpServer()
        with pytest.raises(ValueError, match="Unknown tool"):
            await server.execute_tool("nonexistent.tool", {})

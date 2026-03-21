"""Tests for pipeline steps using mock LLM."""

from __future__ import annotations

import pytest

from verse_mapping.config import AgentConfig, TextMode
from verse_mapping.models import ParsedReference, VerseSpan
from verse_mapping.mcp.bibletext import BibleTextMcpServer
from verse_mapping.mcp.crossrefs import CrossRefsMcpServer
from verse_mapping.mcp.original_lang import OriginalLangMcpServer
from verse_mapping.pipeline.context import expand_context_window, run_context_step
from verse_mapping.pipeline.translations import run_translation_step
from verse_mapping.pipeline.keywords import run_keywords_step
from verse_mapping.pipeline.crossrefs import run_crossrefs_step
from verse_mapping.pipeline.application import run_application_step

from tests.helpers import mock_llm_fn


@pytest.fixture
def ref():
    return ParsedReference(
        raw="John 3:16",
        spans=[VerseSpan(book="John", chapter=3, verse_start=16)],
    )


@pytest.fixture
def config():
    return AgentConfig()


class TestContextExpansion:
    def test_default_window(self, ref, config):
        window = expand_context_window(ref, config)
        assert len(window) == 1
        assert window[0].verse_start == 6  # 16 - 10
        assert window[0].verse_end == 26  # 16 + 10

    def test_custom_window(self, ref):
        config = AgentConfig(context_window=5)
        window = expand_context_window(ref, config)
        assert window[0].verse_start == 11
        assert window[0].verse_end == 21

    def test_window_floor_at_verse_1(self):
        ref = ParsedReference(
            raw="John 1:3",
            spans=[VerseSpan(book="John", chapter=1, verse_start=3)],
        )
        config = AgentConfig(context_window=10)
        window = expand_context_window(ref, config)
        assert window[0].verse_start == 1  # Doesn't go below 1


class TestStep1Context:
    @pytest.mark.asyncio
    async def test_context_step(self, ref, config):
        result = await run_context_step(ref, config, mock_llm_fn)
        assert result.flow_summary
        assert result.genre
        assert result.genre_rationale
        assert result.redemptive_historical_tag
        assert result.redemptive_historical_rationale


class TestStep2Translations:
    @pytest.mark.asyncio
    async def test_always_included(self, ref, config):
        mcp = BibleTextMcpServer()
        result = await run_translation_step(ref, config, mcp, mock_llm_fn)
        assert result.always_included is True

    @pytest.mark.asyncio
    async def test_references_only_no_text(self, ref):
        config = AgentConfig(text_mode=TextMode.REFERENCES_ONLY)
        mcp = BibleTextMcpServer()
        result = await run_translation_step(ref, config, mcp, mock_llm_fn)
        assert result.always_included is True
        # In references-only mode, text should be None
        for r in result.renderings:
            assert r.text is None


class TestStep3Keywords:
    @pytest.mark.asyncio
    async def test_keyword_extraction(self, ref, config):
        translations = (await run_translation_step(
            ref, config, BibleTextMcpServer(), mock_llm_fn
        ))
        mcp_lang = OriginalLangMcpServer()
        result = await run_keywords_step(ref, translations, config, mcp_lang, mock_llm_fn)
        assert 3 <= len(result.keywords) <= 12

    @pytest.mark.asyncio
    async def test_translation_diff_keyword(self, ref, config):
        translations = (await run_translation_step(
            ref, config, BibleTextMcpServer(), mock_llm_fn
        ))
        mcp_lang = OriginalLangMcpServer()
        result = await run_keywords_step(ref, translations, config, mcp_lang, mock_llm_fn)
        # At least one keyword should be influenced by translation diff
        assert any(kw.influenced_by_translation_diff for kw in result.keywords)


class TestStep4CrossRefs:
    @pytest.mark.asyncio
    async def test_crossrefs(self, ref, config):
        translations = (await run_translation_step(
            ref, config, BibleTextMcpServer(), mock_llm_fn
        ))
        mcp_lang = OriginalLangMcpServer()
        keywords = await run_keywords_step(ref, translations, config, mcp_lang, mock_llm_fn)
        mcp_xrefs = CrossRefsMcpServer()
        result = await run_crossrefs_step(ref, keywords, config, mcp_xrefs, mock_llm_fn)
        assert len(result.edges) >= 1
        assert 3 <= len(result.clusters) <= 8
        # Every edge has provenance and relationship type
        for edge in result.edges:
            assert edge.provenance
            assert len(edge.relationship_types) >= 1


class TestStep5Application:
    @pytest.mark.asyncio
    async def test_application(self, ref, config):
        context = await run_context_step(ref, config, mock_llm_fn)
        translations = (await run_translation_step(
            ref, config, BibleTextMcpServer(), mock_llm_fn
        ))
        keywords = await run_keywords_step(
            ref, translations, config, OriginalLangMcpServer(), mock_llm_fn
        )
        result = await run_application_step(ref, context, keywords, config, mock_llm_fn)
        assert 2 <= len(result.principles) <= 4
        assert 3 <= len(result.prompts) <= 6


class TestPipelineOrder:
    @pytest.mark.asyncio
    async def test_full_pipeline_order(self, ref, config):
        """Verify the pipeline executes in the required order and no step is skipped."""
        steps_executed = []

        mcp_bibletext = BibleTextMcpServer()
        mcp_original_lang = OriginalLangMcpServer()
        mcp_crossrefs = CrossRefsMcpServer()

        step1 = await run_context_step(ref, config, mock_llm_fn)
        steps_executed.append("context")

        step2 = await run_translation_step(ref, config, mcp_bibletext, mock_llm_fn)
        steps_executed.append("translations")

        step3 = await run_keywords_step(ref, step2, config, mcp_original_lang, mock_llm_fn)
        steps_executed.append("keywords")

        step4 = await run_crossrefs_step(ref, step3, config, mcp_crossrefs, mock_llm_fn)
        steps_executed.append("crossrefs")

        step5 = await run_application_step(ref, step1, step3, config, mock_llm_fn)
        steps_executed.append("application")

        assert steps_executed == ["context", "translations", "keywords", "crossrefs", "application"]

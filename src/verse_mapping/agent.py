"""Main Verse Mapping Agent — orchestrates the 5-step pipeline."""

from __future__ import annotations

import asyncio
import json
import shutil
from typing import Any, Callable, Awaitable

from verse_mapping.config import AgentConfig, LlmProvider
from verse_mapping.models import ParsedReference, VerseMapOutput, VerseSpan
from verse_mapping.mcp.bibletext import BibleTextMcpServer
from verse_mapping.mcp.crossrefs import CrossRefsMcpServer
from verse_mapping.mcp.original_lang import OriginalLangMcpServer
from verse_mapping.mcp.reference import ReferenceMcpServer
from verse_mapping.pipeline.context import run_context_step
from verse_mapping.pipeline.translations import run_translation_step
from verse_mapping.pipeline.keywords import run_keywords_step
from verse_mapping.pipeline.crossrefs import run_crossrefs_step
from verse_mapping.pipeline.application import run_application_step
from verse_mapping.report import render_report


def _strip_json_fences(text: str) -> str:
    """Strip markdown code fences from LLM output."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    return text


class VerseMappingAgent:
    """Orchestrates the verse mapping pipeline:
    Context -> Translations -> Keywords -> Cross-References -> Application
    """

    def __init__(self, config: AgentConfig | None = None, api_key: str | None = None):
        self.config = config or AgentConfig()
        self._api_client = None

        if self.config.llm_provider == LlmProvider.API:
            from anthropic import AsyncAnthropic
            self._api_client = AsyncAnthropic(api_key=api_key) if api_key else AsyncAnthropic()
        elif self.config.llm_provider == LlmProvider.CLAUDE_CLI:
            if not shutil.which("claude"):
                raise RuntimeError(
                    "claude CLI not found on PATH. Install Claude Code or switch to --provider api."
                )

        # Initialize MCP servers
        self.mcp_reference = ReferenceMcpServer()
        self.mcp_bibletext = BibleTextMcpServer()
        self.mcp_crossrefs = CrossRefsMcpServer()
        self.mcp_original_lang = OriginalLangMcpServer()

    async def _llm_call(self, prompt: str) -> Any:
        """Call the LLM and parse JSON response."""
        full_prompt = prompt + "\n\nRespond with valid JSON only, no markdown fences."

        if self.config.llm_provider == LlmProvider.CLAUDE_CLI:
            text = await self._claude_cli_call(full_prompt)
        else:
            message = await self._api_client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                messages=[{"role": "user", "content": full_prompt}],
            )
            text = message.content[0].text

        text = _strip_json_fences(text)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text

    async def _claude_cli_call(self, prompt: str) -> str:
        """Call the claude CLI using the already-authenticated session."""
        proc = await asyncio.create_subprocess_exec(
            "claude", "-p", prompt, "--output-format", "text",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            err = stderr.decode().strip()
            raise RuntimeError(f"claude CLI failed (exit {proc.returncode}): {err}")
        return stdout.decode()

    async def run(self, reference_str: str) -> VerseMapOutput:
        """Execute the full verse mapping pipeline.

        Args:
            reference_str: Human-readable Bible reference (e.g., "John 3:16")

        Returns:
            VerseMapOutput with all 5 steps populated.
        """
        # Parse reference via MCP
        parsed = await self.mcp_reference.execute_tool(
            "reference.parse", {"reference": reference_str}
        )
        reference = ParsedReference(
            raw=parsed["raw"],
            spans=[VerseSpan(**s) for s in parsed["spans"]],
        )

        # Step 1: Context
        step1 = await run_context_step(reference, self.config, self._llm_call)

        # Step 2: Translation Comparison (ALWAYS included)
        step2 = await run_translation_step(
            reference, self.config, self.mcp_bibletext, self._llm_call
        )

        # Step 3: Keywords / Word Study
        step3 = await run_keywords_step(
            reference, step2, self.config, self.mcp_original_lang, self._llm_call
        )

        # Step 4: Cross-References
        step4 = await run_crossrefs_step(
            reference, step3, self.config, self.mcp_crossrefs, self._llm_call
        )

        # Step 5: Application
        step5 = await run_application_step(
            reference, step1, step3, self.config, self._llm_call
        )

        return VerseMapOutput(
            reference=reference_str,
            step1_context=step1,
            step2_translations=step2,
            step3_keywords=step3,
            step4_crossrefs=step4,
            step5_application=step5,
        )

    async def run_json(self, reference_str: str) -> str:
        """Run pipeline and return validated JSON string."""
        output = await self.run(reference_str)
        return output.model_dump_json(indent=2)

    async def run_report(self, reference_str: str) -> str:
        """Run pipeline and return human-readable report."""
        output = await self.run(reference_str)
        return render_report(output)

    async def run_both(self, reference_str: str) -> tuple[str, str]:
        """Run pipeline and return both JSON and report."""
        output = await self.run(reference_str)
        return output.model_dump_json(indent=2), render_report(output)

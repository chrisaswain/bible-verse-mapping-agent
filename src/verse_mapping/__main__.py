"""CLI entry point for the verse mapping agent."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from verse_mapping.agent import VerseMappingAgent
from verse_mapping.config import AgentConfig, LlmProvider, TextMode


def main() -> None:
    parser = argparse.ArgumentParser(description="Biblical Verse Mapping Agent")
    parser.add_argument("reference", help="Bible reference (e.g., 'John 3:16')")
    parser.add_argument(
        "--format", choices=["json", "report", "both"], default="both",
        help="Output format (default: both)",
    )
    parser.add_argument(
        "--text-mode", choices=["full", "references_only"], default="full",
        help="Text mode (default: full)",
    )
    parser.add_argument(
        "--context-window", type=int, default=10,
        help="Context expansion ± verses (default: 10)",
    )
    parser.add_argument(
        "--translations", nargs="+", default=["KJV", "ESV", "NIV", "NASB", "NLT"],
        help="Translations to compare",
    )
    parser.add_argument(
        "--provider", choices=["claude-cli", "api"], default="claude-cli",
        help="LLM provider: claude-cli (uses authenticated Claude Code) or api (requires ANTHROPIC_API_KEY)",
    )
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")

    args = parser.parse_args()

    config = AgentConfig(
        text_mode=TextMode(args.text_mode),
        context_window=args.context_window,
        translations=args.translations,
        llm_provider=LlmProvider(args.provider),
        output_format=args.format,
    )

    agent = VerseMappingAgent(config=config)

    async def execute():
        if args.format == "json":
            return await agent.run_json(args.reference)
        elif args.format == "report":
            return await agent.run_report(args.reference)
        else:
            j, r = await agent.run_both(args.reference)
            return f"{r}\n\n---\n\n## Machine Output (JSON)\n\n```json\n{j}\n```"

    result = asyncio.run(execute())

    import sys
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"Output written to {args.output}")
    else:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        print(result)


if __name__ == "__main__":
    main()

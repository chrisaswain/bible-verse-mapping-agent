"""Step 1: Context expansion — passage flow, genre, redemptive-historical tagging."""

from __future__ import annotations

from verse_mapping.config import AgentConfig
from verse_mapping.models import ContextStep, ParsedReference, VerseSpan


def expand_context_window(
    reference: ParsedReference, config: AgentConfig
) -> list[VerseSpan]:
    """Expand reference by ±context_window verses."""
    window = []
    for span in reference.spans:
        start = max(1, span.verse_start - config.context_window)
        end = (span.verse_end or span.verse_start) + config.context_window
        window.append(VerseSpan(
            book=span.book,
            chapter=span.chapter,
            verse_start=start,
            verse_end=end,
        ))
    return window


async def run_context_step(
    reference: ParsedReference,
    config: AgentConfig,
    llm_fn,
) -> ContextStep:
    """Execute Step 1: Context.

    Args:
        reference: Parsed Bible reference.
        config: Agent configuration.
        llm_fn: Async callable that takes a prompt and returns structured data.
    """
    context_window = expand_context_window(reference, config)

    prompt = f"""Analyze the context for {reference.raw}.

Context window: {[str(w) for w in context_window]}

Provide:
1. A short flow summary of the passage (2-3 sentences)
2. The literary genre (e.g., narrative, poetry, epistle, prophecy, apocalyptic, wisdom, law)
3. A one-sentence rationale for the genre classification
4. A redemptive-historical tag (e.g., Creation, Fall, Promise, Exodus, Monarchy, Exile, Return, Incarnation, Cross, Resurrection, Church, Consummation)
5. A one-sentence rationale for the redemptive-historical placement
6. A "thought_process" field: explain step by step HOW you determined the context — what surrounding verses you considered, why you identified this genre and redemptive-historical placement, and what interpretive clues led to your flow summary. Cite specific verses (e.g., "v. 8 shifts to...", "vv. 13-14 ground the argument in...").

Return as JSON with keys: flow_summary, genre, genre_rationale, redemptive_historical_tag, redemptive_historical_rationale, thought_process"""

    result = await llm_fn(prompt)

    return ContextStep(
        reference=reference,
        context_window=context_window,
        flow_summary=result.get("flow_summary", ""),
        genre=result.get("genre", ""),
        genre_rationale=result.get("genre_rationale", ""),
        redemptive_historical_tag=result.get("redemptive_historical_tag", ""),
        redemptive_historical_rationale=result.get("redemptive_historical_rationale", ""),
        thought_process=result.get("thought_process", ""),
    )

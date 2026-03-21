"""Step 2: Translation Comparison — always included, even in references-only mode."""

from __future__ import annotations

from verse_mapping.config import AgentConfig, TextMode
from verse_mapping.models import (
    ParsedReference,
    TranslationComparison,
    TranslationRendering,
    VariantSignal,
)


async def run_translation_step(
    reference: ParsedReference,
    config: AgentConfig,
    mcp_bibletext,
    llm_fn,
) -> TranslationComparison:
    """Execute Step 2: Translation Comparison.

    This step is ALWAYS included per spec, even in references-only mode.
    """
    # Call MCP bibletext.compare_translations
    comparison = await mcp_bibletext.execute_tool(
        "bibletext.compare_translations",
        {"reference": reference.raw, "translations": config.translations},
    )

    renderings = []
    for r in comparison.get("renderings", []):
        text = r.get("text")
        if config.text_mode == TextMode.REFERENCES_ONLY:
            text = None  # MUST NOT output restricted verse text
        renderings.append(TranslationRendering(translation=r["translation"], text=text))

    raw_signals = comparison.get("variant_signals", [])

    # If signals are sparse, ask LLM for deeper analysis
    if len(raw_signals) < 2 and any(r.text for r in renderings):
        texts = {r.translation: r.text for r in renderings if r.text}
        prompt = f"""Compare these translations of {reference.raw} and identify key variant signals
(words/phrases where translations meaningfully differ):

{texts}

For each variant signal, explain WHY the translations diverge — what underlying Greek/Hebrew
word, grammatical ambiguity, or textual variant drives the difference.

Return JSON array of objects with keys: keyword, translations_differ (array of
"TRANSLATION: 'rendering'" entries showing each translation's choice), impact (one sentence
on interpretive significance, citing the original-language word that causes the divergence)."""
        llm_signals = await llm_fn(prompt)
        if isinstance(llm_signals, list):
            raw_signals = llm_signals

    variant_signals = [
        VariantSignal(
            keyword=s.get("keyword", ""),
            translations_differ=s.get("translations_differ", []),
            impact=s.get("impact", ""),
        )
        for s in raw_signals
    ]

    # Generate impact summary and thought process
    impact_prompt = f"""Summarize the interpretive impact of translation differences for {reference.raw}.
Signals: {[s.keyword for s in variant_signals]}

Return JSON with keys:
- impact_summary: 2-3 sentences on how these translation choices shape interpretation
- thought_process: explain your reasoning — how you compared the translations, which differences
  matter most and why, and what original-language evidence drives the divergences. Cite specific
  Greek/Hebrew terms and the translations that render them differently."""
    impact_result = await llm_fn(impact_prompt)
    if isinstance(impact_result, str):
        impact_summary = impact_result
        thought_process = ""
    elif isinstance(impact_result, dict):
        impact_summary = impact_result.get("impact_summary", "")
        thought_process = impact_result.get("thought_process", "")
    else:
        impact_summary = str(impact_result)
        thought_process = ""

    return TranslationComparison(
        always_included=True,
        renderings=renderings,
        variant_signals=variant_signals,
        impact_summary=impact_summary,
        thought_process=thought_process,
    )

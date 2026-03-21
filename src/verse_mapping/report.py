"""Human-readable report renderer with deterministic headings and linked citations."""

from __future__ import annotations

from verse_mapping.linkify import (
    bible_link,
    linkify_all,
    source_link_with_strongs,
    strongs_link,
)
from verse_mapping.models import VerseMapOutput


def _L(text: str) -> str:
    """Linkify all references and Strong's numbers in free text."""
    return linkify_all(text)


def _render_thought(thought: str, lines: list[str]) -> None:
    """Render a thought process block if present, with linked citations."""
    if thought:
        lines.append("")
        lines.append("> **How I got here:**")
        for paragraph in thought.split("\n"):
            paragraph = paragraph.strip()
            if paragraph:
                lines.append(f"> {_L(paragraph)}")
        lines.append("")


def render_report(output: VerseMapOutput) -> str:
    """Render a VerseMapOutput as a structured human-readable report."""
    lines: list[str] = []

    lines.append(f"# Verse Map: {bible_link(output.reference)}")
    lines.append("")

    # --- Step 1: Context ---
    ctx = output.step1_context
    lines.append("## 1. Context")
    lines.append("")
    lines.append(f"**Reference:** {bible_link(ctx.reference.raw)}")
    lines.append(f"**Context Window:** {', '.join(bible_link(str(w)) for w in ctx.context_window)}")
    lines.append("")
    lines.append(f"**Passage Flow:** {_L(ctx.flow_summary)}")
    lines.append("")
    lines.append(f"**Genre:** {ctx.genre}")
    lines.append(f"> {_L(ctx.genre_rationale)}")
    lines.append("")
    lines.append(f"**Redemptive-Historical Placement:** {ctx.redemptive_historical_tag}")
    lines.append(f"> {_L(ctx.redemptive_historical_rationale)}")
    _render_thought(ctx.thought_process, lines)

    # --- Step 2: Translation Comparison ---
    tc = output.step2_translations
    lines.append("## 2. Translation Comparison")
    lines.append("")
    for r in tc.renderings:
        if r.text:
            lines.append(f"**{r.translation}:** {r.text}")
        else:
            lines.append(f"**{r.translation}:** *(text restricted — references-only mode)*")
    lines.append("")

    if tc.variant_signals:
        lines.append("### Variant Signals")
        lines.append("")
        for vs in tc.variant_signals:
            lines.append(f"- **{vs.keyword}** — differs in: {', '.join(vs.translations_differ)}")
            lines.append(f"  - Impact: {_L(vs.impact)}")
        lines.append("")

    if tc.impact_summary:
        lines.append(f"**Impact Summary:** {_L(tc.impact_summary)}")
        lines.append("")
    _render_thought(tc.thought_process, lines)

    # --- Step 3: Keywords / Word Study ---
    kw = output.step3_keywords
    lines.append("## 3. Keyword / Original Language Word Study")
    lines.append("")
    _render_thought(kw.thought_process, lines)

    for ws in kw.keywords:
        diff_marker = " (translation-diff)" if ws.influenced_by_translation_diff else ""
        lines.append(f"### {ws.keyword}{diff_marker}")
        lines.append("")
        lines.append(f"- **Lemma:** {ws.lemma} ({ws.transliteration})")
        lexid_display = strongs_link(ws.lexical_id) if ws.lexical_id else ""
        lines.append(f"- **Lexical ID:** {lexid_display}")
        lines.append(f"- **Language:** {ws.language}")
        lines.append(f"- **Gloss Range:** {', '.join(ws.gloss_range)}")
        lines.append(f"- **Possible Meanings:** {'; '.join(ws.possible_meanings)}")
        lines.append(f"- **Meaning in Context:** {_L(ws.meaning_in_context)}")
        if ws.usage_examples:
            lines.append("- **Usage Examples:**")
            for ex in ws.usage_examples:
                lines.append(f"  - {bible_link(ex.reference)}: {ex.snippet}")
        if ws.sources:
            linked_sources = [
                source_link_with_strongs(s, ws.lexical_id) for s in ws.sources
            ]
            lines.append(f"- **Sources:** {', '.join(linked_sources)}")
        _render_thought(ws.thought_process, lines)
        lines.append("")

    # --- Step 4: Cross-References ---
    cr = output.step4_crossrefs
    lines.append("## 4. Cross-References")
    lines.append("")
    _render_thought(cr.thought_process, lines)

    lines.append("### Top Cross-References")
    lines.append("")
    sorted_edges = sorted(cr.edges, key=lambda e: e.score, reverse=True)
    for edge in sorted_edges[:15]:
        types_str = ", ".join(edge.relationship_types)
        lines.append(
            f"- **{bible_link(edge.target)}** (score: {edge.score}, type: {types_str}, "
            f"source: {edge.provenance})"
        )
        if edge.snippet:
            lines.append(f"  - {edge.snippet}")
        if edge.why:
            lines.append(f"  - *Why:* {_L(edge.why)}")
    lines.append("")

    lines.append("### Thematic Clusters")
    lines.append("")
    for cluster in cr.clusters:
        lines.append(f"#### {cluster.name}")
        lines.append(f"> {_L(cluster.rationale)}")
        lines.append("")
        for ref in cluster.edges:
            lines.append(f"- {bible_link(ref)}")
        lines.append("")

    # --- Step 5: Application ---
    app = output.step5_application
    lines.append("## 5. Application")
    lines.append("")
    _render_thought(app.thought_process, lines)

    lines.append("### Principles")
    lines.append("")
    for i, p in enumerate(app.principles, 1):
        lines.append(f"{i}. **{p.statement}**")
        lines.append(f"   - Grounding: {_L(p.grounding)}")
        if p.supporting_refs:
            linked_refs = [bible_link(r) for r in p.supporting_refs]
            lines.append(f"   - Supporting: {', '.join(linked_refs)}")
    lines.append("")

    lines.append("### Reflection Prompts")
    lines.append("")
    for prompt in app.prompts:
        cond = " *(conditional)*" if prompt.conditional else ""
        lines.append(f"- [{prompt.category.upper()}]{cond} {_L(prompt.text)}")
        if prompt.condition_note:
            lines.append(f"  - Note: {_L(prompt.condition_note)}")
    lines.append("")

    return "\n".join(lines)

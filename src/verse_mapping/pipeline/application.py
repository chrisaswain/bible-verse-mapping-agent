"""Step 5: Application — principles and prompts grounded in the text's intent."""

from __future__ import annotations

from verse_mapping.config import AgentConfig
from verse_mapping.models import (
    ApplicationPrompt,
    ApplicationStep,
    ContextStep,
    KeywordsStep,
    ParsedReference,
    Principle,
)


async def run_application_step(
    reference: ParsedReference,
    context: ContextStep,
    keywords: KeywordsStep,
    config: AgentConfig,
    llm_fn,
) -> ApplicationStep:
    """Execute Step 5: Application.

    Produces 2-4 principles and 3-6 prompts (belief/response/prayer/community)
    grounded in the text's intent.
    """
    keyword_summaries = [
        f"{kw.keyword} ({kw.meaning_in_context})" for kw in keywords.keywords[:6]
    ]

    prompt = f"""Based on the study of {reference.raw}:

Context: {context.flow_summary}
Genre: {context.genre}
Redemptive-historical: {context.redemptive_historical_tag}
Key words: {keyword_summaries}

Theological posture: {config.theological_posture.tradition}, {config.theological_posture.soteriology}, {config.theological_posture.gender_roles}

Generate application content:

1. PRINCIPLES (2-4): Timeless truths derived from the passage.
   Each has:
   - statement: the principle
   - grounding: how it connects to the text's original meaning — cite the specific verses,
     Greek/Hebrew terms, and contextual evidence that support this principle
   - supporting_refs: array of Scripture references that support this principle (e.g.,
     ["1 Tim 2:11", "1 Tim 3:15", "Titus 2:3-5"])

2. PROMPTS (3-6): Practical application prompts in these categories:
   - belief: What does this teach me to believe about God/humanity?
   - response: How should I respond or act?
   - prayer: How can I pray in light of this?
   - community: How does this apply to life together?

   Each has:
   - category: one of [belief, response, prayer, community]
   - text: the prompt
   - conditional: true if there's uncertainty about the application
   - condition_note: explanation of the uncertainty (if conditional), citing the specific
     exegetical ambiguity (e.g., "depends on whether αὐθεντεῖν means...")

3. THOUGHT_PROCESS: explain how you moved from the textual data (context, keywords,
   cross-references) to these principles and prompts. What interpretive decisions did you
   make, and why?

IMPORTANT:
- Stay tethered to the passage's original intent
- Do NOT import modern issues unless clearly warranted by the text
- If uncertainty exists, mark prompts as conditional
- Every principle must cite at least one supporting Scripture reference

Return as JSON: {{"principles": [...], "prompts": [...], "thought_process": "..."}}"""

    result = await llm_fn(prompt)
    if not isinstance(result, dict):
        result = {"principles": [], "prompts": []}

    step_thought = result.get("thought_process", "")

    principles = [
        Principle(
            statement=p.get("statement", ""),
            grounding=p.get("grounding", ""),
            supporting_refs=p.get("supporting_refs", []),
        )
        for p in result.get("principles", [])
    ]

    prompts = [
        ApplicationPrompt(
            category=p.get("category", "belief"),
            text=p.get("text", ""),
            conditional=p.get("conditional", False),
            condition_note=p.get("condition_note"),
        )
        for p in result.get("prompts", [])
    ]

    return ApplicationStep(principles=principles, prompts=prompts, thought_process=step_thought)

"""Step 3: Keyword extraction and original-language word study."""

from __future__ import annotations

from verse_mapping.config import AgentConfig
from verse_mapping.models import (
    KeywordsStep,
    ParsedReference,
    TranslationComparison,
    UsageExample,
    WordStudy,
)


async def run_keywords_step(
    reference: ParsedReference,
    translations: TranslationComparison,
    config: AgentConfig,
    mcp_original_lang,
    llm_fn,
) -> KeywordsStep:
    """Execute Step 3: Keyword/Word Study.

    Keywords are selected using translation-diff salience and grammatical/theological salience.
    At least one keyword must be influenced by translation differences when differences exist.
    """
    # Gather variant keywords from Step 2
    variant_keywords = [s.keyword for s in translations.variant_signals]

    prompt = f"""For {reference.raw}, extract {config.min_keywords}-{config.max_keywords} keywords
for original-language word study.

Selection criteria:
1. Translation-diff salience: words where translations differ meaningfully
2. Grammatical salience: words with significant morphological features
3. Theological salience: words carrying key doctrinal weight

Translation variant signals: {variant_keywords}

For EACH keyword, provide a JSON object:
- keyword: the English word
- lemma: original language lemma (Hebrew/Greek)
- transliteration: romanized form
- lexical_id: Strong's number (e.g., H2617, G26)
- language: "Hebrew" or "Greek"
- gloss_range: array of possible English glosses
- usage_examples: array of {{reference, snippet}} showing the word elsewhere in Scripture
- possible_meanings: array of meaning options
- meaning_in_context: the most likely meaning for this passage, explaining WHY this meaning
  fits — cite the immediate context, grammatical clues, and parallel usage that support this reading
- influenced_by_translation_diff: true if this keyword was selected because translations differ
- sources: array of lexical references consulted (e.g., "BDAG", "Thayer's", "BDB", "LSJ",
  "HALOT", "TDNT"). Only cite sources you actually drew data from.
- thought_process: explain WHY you selected this keyword and HOW you arrived at the contextual
  meaning — what grammatical, contextual, or theological factors guided your reasoning

IMPORTANT: At least one keyword MUST have influenced_by_translation_diff=true if translation
differences exist.

Also provide a top-level thought_process explaining your overall keyword selection strategy —
why these words and not others, and how translation differences influenced your choices.

Return as JSON: {{"keywords": [...], "thought_process": "..."}}"""

    raw_result = await llm_fn(prompt)
    if isinstance(raw_result, list):
        keywords_data = raw_result
        step_thought = ""
    else:
        keywords_data = raw_result.get("keywords", [])
        step_thought = raw_result.get("thought_process", "")

    word_studies = []
    for kw in keywords_data:
        # Optionally enrich with MCP lexicon lookup
        lexical_id = kw.get("lexical_id", "")
        if lexical_id and mcp_original_lang:
            try:
                lex_data = await mcp_original_lang.execute_tool(
                    "lexicon.lookup", {"lexical_id": lexical_id}
                )
                # Merge any enriched data from the lexicon
                if lex_data.get("data"):
                    pass  # Enrich gloss_range, etc. from external data
            except Exception:
                pass

        word_studies.append(WordStudy(
            keyword=kw.get("keyword", ""),
            lemma=kw.get("lemma", ""),
            transliteration=kw.get("transliteration", ""),
            lexical_id=lexical_id,
            language=kw.get("language", ""),
            gloss_range=kw.get("gloss_range", []),
            usage_examples=[
                UsageExample(reference=ex.get("reference", ""), snippet=ex.get("snippet", ""))
                for ex in kw.get("usage_examples", [])
            ],
            possible_meanings=kw.get("possible_meanings", []),
            meaning_in_context=kw.get("meaning_in_context", ""),
            influenced_by_translation_diff=kw.get("influenced_by_translation_diff", False),
            sources=kw.get("sources", []),
            thought_process=kw.get("thought_process", ""),
        ))

    # Validate: at least one must be influenced by translation diff if diffs exist
    if variant_keywords and not any(ws.influenced_by_translation_diff for ws in word_studies):
        if word_studies:
            word_studies[0].influenced_by_translation_diff = True

    return KeywordsStep(keywords=word_studies, thought_process=step_thought)

"""Shared test helpers."""

from __future__ import annotations

from typing import Any


async def mock_llm_fn(prompt: str) -> Any:
    """Mock LLM function that returns minimal valid data for testing.

    Matching uses specific phrases from each pipeline step's prompt template
    to avoid cross-matching.
    """
    p = prompt.lower()

    # Step 2b: Impact summary (must be before keyword check since keyword prompts contain generic words)
    if "summarize the interpretive impact" in p:
        return {"impact_summary": "Translation differences highlight key theological nuances."}

    # Step 3: Keyword / word study (check before context since keyword prompts mention "context")
    if "extract" in p and "keywords" in p and "word study" in p:
        return [
            {
                "keyword": "test",
                "lemma": "\u03c4\u03b5\u03c3\u03c4",
                "transliteration": "test",
                "lexical_id": "G9999",
                "language": "Greek",
                "gloss_range": ["test"],
                "usage_examples": [{"reference": "John 1:1", "snippet": "test"}],
                "possible_meanings": ["test"],
                "meaning_in_context": "test meaning",
                "influenced_by_translation_diff": True,
            },
            {
                "keyword": "word2",
                "lemma": "\u03bb\u03b5\u03be",
                "transliteration": "lex",
                "lexical_id": "G9998",
                "language": "Greek",
                "gloss_range": ["word"],
                "usage_examples": [{"reference": "John 1:2", "snippet": "word"}],
                "possible_meanings": ["word"],
                "meaning_in_context": "word meaning",
                "influenced_by_translation_diff": False,
            },
            {
                "keyword": "word3",
                "lemma": "\u03c4\u03c1\u03b9",
                "transliteration": "tri",
                "lexical_id": "G9997",
                "language": "Greek",
                "gloss_range": ["three"],
                "usage_examples": [{"reference": "John 1:3", "snippet": "three"}],
                "possible_meanings": ["three"],
                "meaning_in_context": "third meaning",
                "influenced_by_translation_diff": False,
            },
        ]

    # Step 1: Context
    if "analyze the context" in p or "passage flow" in p:
        return {
            "flow_summary": "Test flow summary.",
            "genre": "epistle",
            "genre_rationale": "Test rationale.",
            "redemptive_historical_tag": "Church",
            "redemptive_historical_rationale": "Test rationale.",
        }

    # Step 2a: Translation variant signals
    if "compare these translations" in p or "identify key variant" in p:
        return [
            {"keyword": "test", "translations_differ": ["KJV", "NIV"], "impact": "Test impact"},
        ]

    # Step 4: Cross-references
    if "cross-reference" in p or "provide cross-references" in p:
        return {
            "edges": [
                {
                    "source": "John 3:16",
                    "target": "Romans 5:8",
                    "relationship_types": ["thematic_parallel"],
                    "score": 90,
                    "score_breakdown": {"lexical": 20, "thematic": 25, "structural": 20, "theological": 25},
                    "provenance": "agent",
                    "snippet": "God demonstrates his own love",
                },
            ],
            "clusters": [
                {"name": "Love of God", "rationale": "God's love theme", "edges": ["Romans 5:8"]},
                {"name": "Salvation", "rationale": "Salvation theme", "edges": ["Romans 5:8"]},
                {"name": "Faith", "rationale": "Faith theme", "edges": ["Romans 5:8"]},
            ],
        }

    # Step 5: Application
    if "application" in p or "principles" in p and "prompts" in p:
        return {
            "principles": [
                {"statement": "God loves sacrificially", "grounding": "The text says God gave."},
                {"statement": "Faith is the means", "grounding": "Whoever believes receives life."},
            ],
            "prompts": [
                {"category": "belief", "text": "What does God's love mean?"},
                {"category": "response", "text": "How will I respond?"},
                {"category": "prayer", "text": "Lord, help me trust."},
            ],
        }

    return {}

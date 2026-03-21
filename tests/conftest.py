"""Shared test fixtures for the verse mapping agent."""

from __future__ import annotations

import pytest

from verse_mapping.config import AgentConfig
from verse_mapping.models import (
    ApplicationPrompt,
    ApplicationStep,
    ContextStep,
    CrossRefEdge,
    CrossRefsStep,
    KeywordsStep,
    ParsedReference,
    Principle,
    ScoreBreakdown,
    ThematicCluster,
    TranslationComparison,
    TranslationRendering,
    UsageExample,
    VariantSignal,
    VerseMapOutput,
    VerseSpan,
    WordStudy,
)


@pytest.fixture
def config():
    return AgentConfig()


@pytest.fixture
def john_3_16_reference():
    return ParsedReference(
        raw="John 3:16",
        spans=[VerseSpan(book="John", chapter=3, verse_start=16)],
    )


@pytest.fixture
def sample_output():
    """A complete sample VerseMapOutput for John 3:16."""
    return VerseMapOutput(
        reference="John 3:16",
        step1_context=ContextStep(
            reference=ParsedReference(
                raw="John 3:16",
                spans=[VerseSpan(book="John", chapter=3, verse_start=16)],
            ),
            context_window=[
                VerseSpan(book="John", chapter=3, verse_start=6, verse_end=26),
            ],
            flow_summary="Jesus explains the new birth to Nicodemus, culminating in the declaration of God's love and the purpose of the Son's coming.",
            genre="Gospel narrative (discourse)",
            genre_rationale="This is a theological discourse within a narrative Gospel, where Jesus teaches Nicodemus about salvation.",
            redemptive_historical_tag="Incarnation",
            redemptive_historical_rationale="Jesus speaks of God sending His Son into the world, pointing to the incarnation and its salvific purpose.",
        ),
        step2_translations=TranslationComparison(
            always_included=True,
            renderings=[
                TranslationRendering(translation="KJV", text="For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life."),
                TranslationRendering(translation="ESV", text="For God so loved the world, that he gave his only Son, that whoever believes in him should not perish but have eternal life."),
                TranslationRendering(translation="NIV", text="For God so loved the world that he gave his one and only Son, that whoever believes in him shall not perish but have eternal life."),
            ],
            variant_signals=[
                VariantSignal(
                    keyword="only begotten / only / one and only",
                    translations_differ=["KJV", "ESV", "NIV"],
                    impact="The rendering of monogenes affects whether the emphasis is on uniqueness or biological begetting.",
                ),
            ],
            impact_summary="The key translation variant centers on monogenes — whether 'only begotten' (KJV) or 'only/one and only' (ESV/NIV). This affects the theological nuance of the Son's unique relationship to the Father.",
        ),
        step3_keywords=KeywordsStep(
            keywords=[
                WordStudy(
                    keyword="loved",
                    lemma="ἀγαπάω",
                    transliteration="agapaō",
                    lexical_id="G25",
                    language="Greek",
                    gloss_range=["to love", "to value", "to esteem"],
                    usage_examples=[
                        UsageExample(reference="Romans 5:8", snippet="God demonstrates his own love for us"),
                        UsageExample(reference="1 John 4:8", snippet="God is love"),
                    ],
                    possible_meanings=["sacrificial love", "divine affection", "unconditional love"],
                    meaning_in_context="God's sacrificial, self-giving love directed toward the whole world",
                ),
                WordStudy(
                    keyword="only begotten",
                    lemma="μονογενής",
                    transliteration="monogenēs",
                    lexical_id="G3439",
                    language="Greek",
                    gloss_range=["only begotten", "one and only", "unique"],
                    usage_examples=[
                        UsageExample(reference="John 1:14", snippet="the glory of the only begotten from the Father"),
                        UsageExample(reference="Hebrews 11:17", snippet="Abraham offered up his only begotten son Isaac"),
                    ],
                    possible_meanings=["only begotten", "unique one", "one of a kind"],
                    meaning_in_context="The unique, one-of-a-kind Son who shares the Father's nature",
                    influenced_by_translation_diff=True,
                ),
                WordStudy(
                    keyword="believes",
                    lemma="πιστεύω",
                    transliteration="pisteuō",
                    lexical_id="G4100",
                    language="Greek",
                    gloss_range=["to believe", "to trust", "to have faith"],
                    usage_examples=[
                        UsageExample(reference="Romans 10:9", snippet="if you believe in your heart"),
                        UsageExample(reference="Acts 16:31", snippet="Believe in the Lord Jesus"),
                    ],
                    possible_meanings=["intellectual assent", "personal trust", "ongoing faith commitment"],
                    meaning_in_context="Active, personal trust in Jesus — not mere intellectual assent but relational dependence",
                ),
            ],
        ),
        step4_crossrefs=CrossRefsStep(
            edges=[
                CrossRefEdge(
                    source="John 3:16",
                    target="Romans 5:8",
                    relationship_types=["thematic_parallel", "theological_development"],
                    score=92,
                    score_breakdown=ScoreBreakdown(lexical=18, thematic=25, structural=24, theological=25),
                    provenance="openbible",
                    snippet="God demonstrates his own love for us in this: While we were still sinners, Christ died for us.",
                ),
                CrossRefEdge(
                    source="John 3:16",
                    target="1 John 4:9-10",
                    relationship_types=["verbal_parallel", "thematic_parallel"],
                    score=95,
                    score_breakdown=ScoreBreakdown(lexical=23, thematic=25, structural=22, theological=25),
                    provenance="openbible",
                    snippet="God sent his one and only Son into the world that we might live through him.",
                ),
                CrossRefEdge(
                    source="John 3:16",
                    target="Genesis 22:2",
                    relationship_types=["typological"],
                    score=78,
                    score_breakdown=ScoreBreakdown(lexical=10, thematic=22, structural=21, theological=25),
                    provenance="agent",
                    snippet="Take your son, your only son Isaac, whom you love.",
                ),
            ],
            clusters=[
                ThematicCluster(
                    name="God's Love for the World",
                    rationale="Passages that directly parallel God's sacrificial love expressed toward humanity",
                    edges=["Romans 5:8", "1 John 4:9-10"],
                ),
                ThematicCluster(
                    name="The Only Son Typology",
                    rationale="Passages connecting the sacrifice of an only son to God's gift of Christ",
                    edges=["Genesis 22:2"],
                ),
                ThematicCluster(
                    name="Salvation by Faith",
                    rationale="Passages developing the theme of believing/trusting for eternal life",
                    edges=["Romans 5:8"],
                ),
            ],
        ),
        step5_application=ApplicationStep(
            principles=[
                Principle(
                    statement="God's love is initiating and sacrificial",
                    grounding="The text states God loved first and gave His Son — the initiative and cost are God's.",
                ),
                Principle(
                    statement="Salvation is received through trust, not earned through works",
                    grounding="The condition for receiving eternal life is 'believes in him' — personal trust, not performance.",
                ),
            ],
            prompts=[
                ApplicationPrompt(
                    category="belief",
                    text="What does it mean that God loved 'the world' — not just a select group? How does this shape my understanding of God's character?",
                ),
                ApplicationPrompt(
                    category="response",
                    text="In what area of my life am I trying to earn God's favor rather than trusting in what He has already given?",
                ),
                ApplicationPrompt(
                    category="prayer",
                    text="Father, help me to grasp the width and depth of your love that moved you to give your only Son for me.",
                ),
                ApplicationPrompt(
                    category="community",
                    text="How can our community reflect God's initiating love by reaching out to those who feel unworthy or excluded?",
                ),
            ],
        ),
    )



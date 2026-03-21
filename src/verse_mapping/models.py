"""Pydantic models for all pipeline steps and output schema."""

from __future__ import annotations

from pydantic import BaseModel, Field


# --- Shared ---

class VerseSpan(BaseModel):
    book: str
    chapter: int
    verse_start: int
    verse_end: int | None = None

    def __str__(self) -> str:
        ref = f"{self.book} {self.chapter}:{self.verse_start}"
        if self.verse_end and self.verse_end != self.verse_start:
            ref += f"-{self.verse_end}"
        return ref


class ParsedReference(BaseModel):
    raw: str
    spans: list[VerseSpan]


# --- Step 1: Context ---

class ContextStep(BaseModel):
    reference: ParsedReference
    context_window: list[VerseSpan]
    flow_summary: str
    genre: str
    genre_rationale: str
    redemptive_historical_tag: str
    redemptive_historical_rationale: str
    thought_process: str = ""


# --- Step 2: Translation Comparison ---

class TranslationRendering(BaseModel):
    translation: str
    text: str | None = None  # None in references_only mode


class VariantSignal(BaseModel):
    keyword: str
    translations_differ: list[str]
    impact: str


class TranslationComparison(BaseModel):
    always_included: bool = True
    renderings: list[TranslationRendering]
    variant_signals: list[VariantSignal]
    impact_summary: str
    thought_process: str = ""


# --- Step 3: Keywords / Word Study ---

class UsageExample(BaseModel):
    reference: str
    snippet: str


class WordStudy(BaseModel):
    keyword: str
    lemma: str
    transliteration: str
    lexical_id: str  # Strong's or equivalent
    language: str  # "Hebrew" or "Greek"
    gloss_range: list[str]
    usage_examples: list[UsageExample]
    possible_meanings: list[str]
    meaning_in_context: str
    influenced_by_translation_diff: bool = False
    sources: list[str] = Field(default_factory=list)
    thought_process: str = ""


class KeywordsStep(BaseModel):
    keywords: list[WordStudy] = Field(min_length=3, max_length=12)
    thought_process: str = ""


# --- Step 4: Cross-References ---

class ScoreBreakdown(BaseModel):
    lexical: float = 0
    thematic: float = 0
    structural: float = 0
    theological: float = 0


class CrossRefEdge(BaseModel):
    source: str
    target: str
    relationship_types: list[str] = Field(min_length=1)
    score: int = Field(ge=0, le=100)
    score_breakdown: ScoreBreakdown
    provenance: str
    snippet: str | None = None
    why: str = ""


class ThematicCluster(BaseModel):
    name: str
    rationale: str
    edges: list[str]  # target references


class CrossRefsStep(BaseModel):
    edges: list[CrossRefEdge]
    clusters: list[ThematicCluster] = Field(min_length=3, max_length=8)
    thought_process: str = ""


# --- Step 5: Application ---

class Principle(BaseModel):
    statement: str
    grounding: str  # How it connects to the text
    supporting_refs: list[str] = Field(default_factory=list)


class ApplicationPrompt(BaseModel):
    category: str  # belief, response, prayer, community
    text: str
    conditional: bool = False
    condition_note: str | None = None


class ApplicationStep(BaseModel):
    principles: list[Principle] = Field(min_length=2, max_length=4)
    prompts: list[ApplicationPrompt] = Field(min_length=3, max_length=6)
    thought_process: str = ""


# --- Full Output ---

class VerseMapOutput(BaseModel):
    reference: str
    step1_context: ContextStep
    step2_translations: TranslationComparison
    step3_keywords: KeywordsStep
    step4_crossrefs: CrossRefsStep
    step5_application: ApplicationStep

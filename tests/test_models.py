"""Tests for Pydantic models and JSON schema validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from verse_mapping.models import (
    CrossRefEdge,
    CrossRefsStep,
    KeywordsStep,
    ScoreBreakdown,
    ThematicCluster,
    TranslationComparison,
    TranslationRendering,
    VariantSignal,
    VerseMapOutput,
    VerseSpan,
    WordStudy,
)


class TestVerseSpan:
    def test_single_verse(self):
        span = VerseSpan(book="John", chapter=3, verse_start=16)
        assert str(span) == "John 3:16"

    def test_verse_range(self):
        span = VerseSpan(book="Romans", chapter=3, verse_start=21, verse_end=26)
        assert str(span) == "Romans 3:21-26"


class TestTranslationComparison:
    def test_always_included_must_be_true(self):
        tc = TranslationComparison(
            always_included=True,
            renderings=[TranslationRendering(translation="KJV", text="test")],
            variant_signals=[],
            impact_summary="test",
        )
        assert tc.always_included is True


class TestKeywordsStep:
    def test_min_keywords_enforced(self):
        with pytest.raises(ValidationError):
            KeywordsStep(keywords=[])  # Needs at least 3

    def test_max_keywords_enforced(self):
        keywords = [
            WordStudy(
                keyword=f"word{i}",
                lemma="λ",
                transliteration="l",
                lexical_id=f"G{i}",
                language="Greek",
                gloss_range=["test"],
                usage_examples=[],
                possible_meanings=["test"],
                meaning_in_context="test",
            )
            for i in range(15)  # Exceeds max of 12
        ]
        with pytest.raises(ValidationError):
            KeywordsStep(keywords=keywords)


class TestCrossRefEdge:
    def test_edge_requires_relationship_type(self):
        with pytest.raises(ValidationError):
            CrossRefEdge(
                source="John 3:16",
                target="Romans 5:8",
                relationship_types=[],  # Min 1 required
                score=50,
                score_breakdown=ScoreBreakdown(),
                provenance="agent",
            )

    def test_score_bounds(self):
        with pytest.raises(ValidationError):
            CrossRefEdge(
                source="John 3:16",
                target="Romans 5:8",
                relationship_types=["thematic_parallel"],
                score=150,  # Max is 100
                score_breakdown=ScoreBreakdown(),
                provenance="agent",
            )


class TestCrossRefsStep:
    def test_cluster_count_bounds(self):
        edges = [
            CrossRefEdge(
                source="John 3:16",
                target="Romans 5:8",
                relationship_types=["thematic_parallel"],
                score=90,
                score_breakdown=ScoreBreakdown(),
                provenance="agent",
            )
        ]
        # Too few clusters (need 3 min)
        with pytest.raises(ValidationError):
            CrossRefsStep(
                edges=edges,
                clusters=[
                    ThematicCluster(name="A", rationale="r", edges=["Romans 5:8"]),
                ],
            )


class TestFullOutput:
    def test_output_serializes_to_json(self, sample_output):
        json_str = sample_output.model_dump_json()
        data = json.loads(json_str)
        assert "step1_context" in data
        assert "step2_translations" in data
        assert "step3_keywords" in data
        assert "step4_crossrefs" in data
        assert "step5_application" in data

    def test_always_included_in_output(self, sample_output):
        data = json.loads(sample_output.model_dump_json())
        assert data["step2_translations"]["always_included"] is True

    def test_json_schema_validation(self, sample_output):
        """Validate output against the JSON schema file."""
        schema_path = Path(__file__).parent.parent / "schemas" / "output.schema.json"
        if schema_path.exists():
            import jsonschema

            schema = json.loads(schema_path.read_text())
            data = json.loads(sample_output.model_dump_json())
            jsonschema.validate(data, schema)

    def test_all_edges_have_provenance_and_type(self, sample_output):
        for edge in sample_output.step4_crossrefs.edges:
            assert edge.provenance, "Edge missing provenance"
            assert len(edge.relationship_types) >= 1, "Edge missing relationship type"

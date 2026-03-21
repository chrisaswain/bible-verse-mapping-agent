"""Golden tests — validate output shape for representative passages."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from verse_mapping.models import VerseMapOutput

FIXTURES_DIR = Path(__file__).parent / "fixtures"

GOLDEN_PASSAGES = [
    "John 3:16",
    "Isaiah 53:5-6",
    "Genesis 22",
    "Exodus 12",
    "Psalm 110",
    "Romans 3:21-26",
    "Ephesians 2:8-10",
    "1 Timothy 2:11-15",
    "Acts 2",
    "Hebrews 10",
]


def _fixture_filename(passage: str) -> str:
    return passage.lower().replace(" ", "_").replace(":", "_").replace("-", "_") + ".json"


class TestGoldenFixtures:
    """Test that golden fixtures validate against the output schema."""

    @pytest.mark.parametrize("passage", GOLDEN_PASSAGES)
    def test_fixture_validates(self, passage):
        fixture_path = FIXTURES_DIR / _fixture_filename(passage)
        if not fixture_path.exists():
            pytest.skip(f"Golden fixture not yet created: {fixture_path.name}")

        data = json.loads(fixture_path.read_text(encoding="utf-8"))
        output = VerseMapOutput.model_validate(data)

        # Translation comparison is present on every fixture
        assert output.step2_translations.always_included is True

        # All 5 steps present
        assert output.step1_context is not None
        assert output.step2_translations is not None
        assert output.step3_keywords is not None
        assert output.step4_crossrefs is not None
        assert output.step5_application is not None

    @pytest.mark.parametrize("passage", GOLDEN_PASSAGES)
    def test_edge_completeness(self, passage):
        """Every cross-reference edge must include provenance and relationship type."""
        fixture_path = FIXTURES_DIR / _fixture_filename(passage)
        if not fixture_path.exists():
            pytest.skip(f"Golden fixture not yet created: {fixture_path.name}")

        data = json.loads(fixture_path.read_text(encoding="utf-8"))
        output = VerseMapOutput.model_validate(data)

        for edge in output.step4_crossrefs.edges:
            assert edge.provenance, f"Edge {edge.source}->{edge.target} missing provenance"
            assert len(edge.relationship_types) >= 1, (
                f"Edge {edge.source}->{edge.target} missing relationship type"
            )


class TestGoldenOutputShape:
    def test_sample_output_shape(self, sample_output):
        """Verify the sample output from conftest matches expected JSON shape."""
        data = json.loads(sample_output.model_dump_json())

        # All step keys present
        for key in ["step1_context", "step2_translations", "step3_keywords",
                     "step4_crossrefs", "step5_application"]:
            assert key in data

        # Translation comparison always included
        assert data["step2_translations"]["always_included"] is True

        # Keywords within bounds
        assert 3 <= len(data["step3_keywords"]["keywords"]) <= 12

        # Clusters within bounds
        assert 3 <= len(data["step4_crossrefs"]["clusters"]) <= 8

        # Application within bounds
        assert 2 <= len(data["step5_application"]["principles"]) <= 4
        assert 3 <= len(data["step5_application"]["prompts"]) <= 6

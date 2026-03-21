"""Configuration for the verse mapping agent."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class TextMode(str, Enum):
    FULL = "full"
    REFERENCES_ONLY = "references_only"


class LlmProvider(str, Enum):
    API = "api"
    CLAUDE_CLI = "claude-cli"


class TheologicalPosture(BaseModel):
    tradition: str = "evangelical"
    soteriology: str = "non-Calvinist"
    gender_roles: str = "soft-egalitarian"


class AgentConfig(BaseModel):
    text_mode: TextMode = TextMode.FULL
    context_window: int = Field(default=10, ge=1, le=50, description="Verses before/after")
    translations: list[str] = Field(
        default=["KJV", "ESV", "NIV", "NASB", "NLT"],
        description="Translations to compare",
    )
    max_keywords: int = Field(default=12, ge=3, le=20)
    min_keywords: int = Field(default=3, ge=1)
    max_clusters: int = Field(default=8, ge=3)
    min_clusters: int = Field(default=3, ge=1)
    theological_posture: TheologicalPosture = Field(default_factory=TheologicalPosture)
    mcp_servers: dict[str, str] = Field(
        default_factory=lambda: {
            "bibletext": "mcp-bibletext",
            "crossrefs": "mcp-crossrefs",
            "original_lang": "mcp-original-lang",
            "reference": "mcp-reference",
            "open_content": "mcp-open-content",
        }
    )
    llm_provider: LlmProvider = LlmProvider.CLAUDE_CLI
    output_format: Literal["json", "report", "both"] = "both"

# Bible Verse Mapping Agent

Spec-driven implementation of a Biblical Verse Mapping AI Agent.

## Architecture

5-step pipeline: Context -> Translations -> Keywords -> Cross-References -> Application

- `src/verse_mapping/agent.py` — Main orchestrator
- `src/verse_mapping/models.py` — Pydantic models (all 5 steps)
- `src/verse_mapping/config.py` — AgentConfig with defaults
- `src/verse_mapping/pipeline/` — One module per step
- `src/verse_mapping/mcp/` — MCP servers (bibletext, crossrefs, original_lang, reference, open_content)
- `src/verse_mapping/report.py` — Human-readable report renderer
- `schemas/output.schema.json` — JSON Schema for validation
- `tests/golden/fixtures/` — Golden test fixtures

## Spec Source of Truth

`C:\Dev\AI\openspec-verse-mapping-agent-spec\openspec\specs\**\spec.md`

## Key Rules

- Translation Comparison is **always** included (step2_translations.always_included = true)
- Pipeline order is fixed: Context, Translations, Keywords, Cross-References, Application
- No step may be skipped
- references_only mode: no restricted verse text, but variant_signals and impact_summary required
- Cross-ref edges MUST have provenance and at least one relationship_type
- 3-12 keywords, 3-8 clusters, 2-4 principles, 3-6 prompts

## Commands

```bash
# Install
pip install -e ".[dev]"

# Run agent
python -m verse_mapping "John 3:16" --format both

# Tests
pytest tests/ -v
pytest tests/golden/ -v  # Golden tests only
```

## Theological Defaults

Evangelical, non-Calvinist, soft-egalitarian (configurable via AgentConfig)

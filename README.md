# Bible Verse Mapping Agent

A spec-driven AI agent that produces comprehensive verse maps for any Bible passage. Given a reference like `1 Timothy 2:12`, it runs a 5-step pipeline and outputs a richly annotated study document with linked citations, original-language word studies, scored cross-references, and transparent reasoning at every step.

## Pipeline

| Step | What it does |
|------|-------------|
| **1. Context** | Expands ±10 verses, summarizes passage flow, tags genre and redemptive-historical placement |
| **2. Translation Comparison** | Compares KJV, ESV, NIV, NASB, NLT — identifies variant signals and their interpretive impact |
| **3. Keyword / Word Study** | Extracts 3–12 keywords with Greek/Hebrew lemma, Strong's number, semantic range, contextual meaning, and lexical sources |
| **4. Cross-References** | Retrieves 10–25 cross-references, each scored 0–100 with relationship types, provenance, and a "why" explanation; clusters into 3–8 thematic groups |
| **5. Application** | Produces 2–4 grounded principles and 3–6 reflection prompts (belief / response / prayer / community), with conditional markers where exegetical uncertainty exists |

Every step includes a **"How I got here"** thought-process block explaining the reasoning, and all citations link directly to source content.

## Linked Citations

| Citation type | Links to |
|---------------|----------|
| Scripture references | [BibleGateway](https://www.biblegateway.com) (ESV) |
| Strong's numbers (G/H) | [BibleHub](https://biblehub.com) Greek/Hebrew pages |
| BDAG | BibleHub entry for the specific word |
| Thayer's / BDB | [Blue Letter Bible](https://www.blueletterbible.org) lexicon entry |
| LSJ | [LSJ.gr](https://lsj.gr/) |
| TDNT | [Logos](https://www.logos.com) product page |

## Quick Start

### Prerequisites

- Python 3.11+
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI installed and authenticated

### Install

```bash
cd bible-verse-mapping-agent
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
```

### Run

```bash
# Human-readable report (default: uses Claude CLI, no API key needed)
python -m verse_mapping "John 3:16" --format report

# JSON output
python -m verse_mapping "Romans 8:28-30" --format json

# Both JSON + report
python -m verse_mapping "Psalm 23:1-6" --format both

# Save to file
python -m verse_mapping "1 Timothy 2:12" --format report -o output.md
```

### CLI Options

| Flag | Default | Description |
|------|---------|-------------|
| `--format` | `both` | Output format: `json`, `report`, or `both` |
| `--provider` | `claude-cli` | LLM backend: `claude-cli` (uses authenticated Claude Code) or `api` (requires `ANTHROPIC_API_KEY`) |
| `--text-mode` | `full` | `full` or `references_only` (omits licensed translation text) |
| `--context-window` | `10` | Number of verses to expand before/after the reference |
| `--translations` | `KJV ESV NIV NASB NLT` | Translations to compare |
| `-o` / `--output` | stdout | Output file path |

### Using the API provider

If you prefer to use the Anthropic API directly instead of the Claude CLI:

```bash
# Create .env from the example
cp .env.example .env
# Edit .env and add your key: ANTHROPIC_API_KEY=sk-ant-...

python -m verse_mapping "John 3:16" --provider api
```

## Project Structure

```
bible-verse-mapping-agent/
├── src/verse_mapping/
│   ├── __main__.py          # CLI entry point
│   ├── agent.py             # Pipeline orchestrator (Claude CLI or API backend)
│   ├── config.py            # AgentConfig, LlmProvider, TextMode
│   ├── models.py            # Pydantic models for all 5 steps
│   ├── linkify.py           # Citation → markdown link conversion
│   ├── report.py            # Human-readable report renderer
│   ├── pipeline/
│   │   ├── context.py       # Step 1: Context expansion
│   │   ├── translations.py  # Step 2: Translation comparison
│   │   ├── keywords.py      # Step 3: Keyword / word study
│   │   ├── crossrefs.py     # Step 4: Cross-references
│   │   └── application.py   # Step 5: Application
│   └── mcp/                 # MCP server interfaces
│       ├── base.py          # Base MCP server class
│       ├── bibletext.py     # Bible text retrieval
│       ├── crossrefs.py     # Cross-reference data
│       ├── original_lang.py # Lexicon / morphology
│       ├── reference.py     # Reference parsing
│       └── open_content.py  # Door43 open content
├── schemas/
│   └── output.schema.json   # JSON Schema for pipeline output
├── tests/
│   ├── golden/              # Golden test fixtures (10 passages)
│   ├── test_models.py       # Model validation tests
│   ├── test_mcp_servers.py  # MCP server tests
│   └── test_pipeline.py     # Pipeline integration tests
├── CLAUDE.md                # Agent instructions for Claude Code
├── pyproject.toml
└── .env.example
```

## Spec

This agent is implemented against the [OpenSpec](../openspec-verse-mapping-agent-spec/) requirements. Key non-negotiables from the spec:

- Translation Comparison is **always** included, even in references-only mode
- Pipeline order is fixed and no step may be skipped
- Cross-reference edges must have provenance and at least one relationship type
- 3–12 keywords, 3–8 clusters, 2–4 principles, 3–6 prompts

## Theological Defaults

| Setting | Default |
|---------|---------|
| Tradition | Evangelical |
| Soteriology | Non-Calvinist |
| Gender roles | Soft-egalitarian |

These are configurable via `AgentConfig.theological_posture`.

## Tests

```bash
pytest tests/ -v
pytest tests/golden/ -v  # Golden tests only
```

## License

MIT

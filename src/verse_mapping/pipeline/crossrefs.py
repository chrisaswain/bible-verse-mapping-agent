"""Step 4: Cross-reference retrieval, typing, scoring, and clustering."""

from __future__ import annotations

from verse_mapping.config import AgentConfig
from verse_mapping.models import (
    CrossRefEdge,
    CrossRefsStep,
    KeywordsStep,
    ParsedReference,
    ScoreBreakdown,
    ThematicCluster,
)


async def run_crossrefs_step(
    reference: ParsedReference,
    keywords: KeywordsStep,
    config: AgentConfig,
    mcp_crossrefs,
    llm_fn,
) -> CrossRefsStep:
    """Execute Step 4: Cross-References.

    Retrieves cross-references, annotates each edge with relationship types,
    scores (0-100), and provenance. Clusters into 3-8 thematic groups.
    """
    # Fetch from MCP crossrefs server
    raw_edges = []
    if mcp_crossrefs:
        try:
            result = await mcp_crossrefs.execute_tool(
                "crossrefs.get", {"reference": reference.raw}
            )
            raw_edges = result.get("edges", [])
        except Exception:
            pass

    # Use LLM to generate/enrich cross-references with typing and scoring
    keyword_list = [kw.keyword for kw in keywords.keywords]
    prompt = f"""For {reference.raw}, provide cross-references with full annotation.

Keywords from word study: {keyword_list}

For each cross-reference, provide:
- source: the input reference
- target: the cross-reference (e.g., "Romans 5:8")
- relationship_types: array of types from [direct_quote, allusion, thematic_parallel,
  typological, prophetic_fulfillment, conceptual, verbal_parallel, structural_parallel,
  theological_development, contrast]
- score: 0-100 relevance score
- score_breakdown: {{lexical, thematic, structural, theological}} (each 0-25)
- provenance: "openbible", "tsk", or "agent"
- snippet: brief quote or description of the target passage
- why: 1-2 sentences explaining WHY this passage connects to {reference.raw} — what specific
  word, theme, argument, or literary link justifies the connection. Be concrete (e.g., "Both
  passages use ἡσυχία in the context of congregational conduct" not just "similar theme").

Provide 10-25 cross-references, prioritizing the strongest connections.

Then, cluster them into {config.min_clusters}-{config.max_clusters} thematic clusters:
- name: cluster name
- rationale: why these references cluster together (cite specific shared vocabulary, themes, or
  theological arguments that unify the cluster)
- edges: array of target references in this cluster

Finally, provide a top-level "thought_process" explaining your cross-reference strategy — how you
identified connections, what led you to prioritize certain references over others, and how the
keyword study influenced your selections.

Return as JSON: {{"edges": [...], "clusters": [...], "thought_process": "..."}}"""

    result = await llm_fn(prompt)
    if not isinstance(result, dict):
        result = {"edges": [], "clusters": []}

    step_thought = result.get("thought_process", "")

    edges = []
    for e in result.get("edges", []):
        edges.append(CrossRefEdge(
            source=e.get("source", reference.raw),
            target=e.get("target", ""),
            relationship_types=e.get("relationship_types", ["thematic_parallel"]),
            score=min(100, max(0, e.get("score", 50))),
            score_breakdown=ScoreBreakdown(**e.get("score_breakdown", {})),
            provenance=e.get("provenance", "agent"),
            snippet=e.get("snippet"),
            why=e.get("why", ""),
        ))

    clusters = []
    for c in result.get("clusters", []):
        clusters.append(ThematicCluster(
            name=c.get("name", ""),
            rationale=c.get("rationale", ""),
            edges=c.get("edges", []),
        ))

    # Validate cluster count
    if len(clusters) < config.min_clusters:
        # Ask LLM to re-cluster if too few
        pass
    if len(clusters) > config.max_clusters:
        clusters = clusters[: config.max_clusters]

    return CrossRefsStep(edges=edges, clusters=clusters, thought_process=step_thought)

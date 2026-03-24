# Search Loop

Use this file when `causal-abel` needs external search to explain a graph-backed edge, path, or proxy dimension.

Search is a support tool. CAP structure remains primary.

## Rule Zero

Do not search until you can name what the search is explaining.

Allowed grounding shapes:

- a graph edge
- a graph path
- a proxy dimension
- a convergence candidate that appeared across multiple anchors

If you cannot name one of those, go back to graph grounding first.

## Pre-Search Frame

Before every search call, write this frame mentally or explicitly:

```text
Edge or proxy: [NodeA -> NodeB] or [proxy dimension]
Causal question: [WHY this connection matters / WHAT its current state is]
Query: [terms derived from the edge or proxy dimension]
```

If the query cannot be filled honestly, do not search yet.

## Good Reasons To Search

- the graph shows a plausible edge or path but not the real-world mechanism
- a proxy dimension is honest but needs current evidence to explain what it represents now
- several anchors converge on the same candidate and you need to know whether that hub is real
- the graph structure is clear, but timing or current-state evidence is missing

## Good Reasons To Return To The Graph

- search reveals a new entity that maps cleanly to a ticker or node candidate
- search clarifies that the real open question is structural, not narrative
- search produces credible counter-evidence that should be tested with `paths`, `neighbors`, `traverse-parents`, or `validate-connectivity`
- search reveals a second-order effect that deserves its own structural check

## Mechanism Extraction

After each useful search result, extract only what supports the current causal question:

- `event`: what happened
- `mechanism`: why that event matters for the edge or proxy dimension
- `persistence`: one-off or ongoing
- `state_now`: whether the mechanism appears current, stale, or unresolved
- `conflict`: strongest counter-evidence found so far

When evidence is thin, say so.

## Search Feedback Scan

After each search, check these four follow-ups:

1. Is there a new entity to map into the graph?
2. Did the current edge or proxy dimension change state?
3. Is there credible counter-evidence that challenges the current path story?
4. Is there a second-order effect worth a structural follow-up?

If all four answers are no, the search loop is likely converging.

## Stop Rules

- stop after repeated low-signal search results that do not change the next graph question
- stop when the main uncertainty is a future event the current graph and evidence cannot resolve
- stop when the search only repeats generic sector commentary without improving graph interpretation

## Language And Source Quality

- Match search language to the region when the mechanism is region-specific.
- Treat source quality separately from search language.
- Use local-language search to find the right mechanism, then verify important claims with stronger sources when possible.

## Output Rule

When search contributes to the final answer, preserve provenance:

- `graph_fact`
- `searched_mechanism`
- `inference`

Do not let mechanism evidence masquerade as graph fact.

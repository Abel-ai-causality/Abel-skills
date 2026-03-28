# Multi-Tier Pipeline: L0 → L0.5 → L2

Execute this pipeline before entering the orchestration loop. It replaces manual anchor picking with structured hypothesis generation and screening.

## When to Use

All `proxy_routed` questions. For `direct_graph`, skip to the orchestration loop directly — the anchor is already known.

## Step 1: L0 Narrate (hypothesis generation)

Generate 4-6 candidate causal mechanisms for the user's question. Each mechanism is a short chain:

```
Mechanism: [cause] → (transmission) → [outcome]
Testable proxy: [concept or node name that could represent this in the graph]
```

Rules:
- Use your world knowledge, not the graph. This is a reasoning step, not a graph step.
- Generate multiple perspectives. At minimum include:
  - The obvious mechanism (what most people would guess)
  - A second-order or indirect mechanism (what's one step removed)
  - A **contrarian mechanism** (what would make the opposite outcome true? REQUIRED — forces adversarial thinking and catches confirmation bias)
  - A confounder (what third factor could explain both cause and outcome without direct causation)
- Each mechanism must name what it would take to falsify it.
- Time budget: one reasoning pass, ~5 seconds. Don't overthink.

## Step 2: L0.5 Screen (structural plausibility)

For each L0 mechanism, check graph support:

1. Map the cause and outcome concepts to candidate nodes (manual mapping → `query_node` → capillary discovery per `capillary-mapping.md`)
2. Run `graph.paths` between cause proxy and outcome proxy
3. Rank by structural strength:

| Path distance | Rating | Priority | Action |
|--------------|--------|----------|--------|
| dist ≤ 2 | **strong** | highest | L2 observe + intervene |
| dist 3-4 | **plausible** | medium | L2 observe, intervene if coherent |
| no path, has neighbors | **weak** | low | L2 observe only if budget remains |
| no path, no neighbors | **narrative-only** | context | web grounding only, no L2 probes |

Shorter distance = tighter causal coupling. A dist=2 path (direct transmission) is qualitatively different from dist=4 (long chain with bridge noise).

Output: mechanisms ranked by distance, then by number of corroborating paths.

Time budget: ~100ms per mechanism (paths + neighbors). Total: ~500ms for 5 mechanisms.

## Step 3: L2 Verify (statistical observation)

Enter the orchestration loop (`orchestration-loop.md`) with the L0.5 ranked mechanism list as input instead of manually-picked anchors.

- Start with the strongest graph-plausible mechanism
- Observe its key nodes
- If low-signal, try the next mechanism from the ranked list (not a random switch)
- Web grounding applies to ALL mechanisms (graph-plausible and narrative-only)

## Step 4: Annotate

Before writing the report, tag each significant claim with its tier:

- **L2**: Backed by observe/intervene probe result
- **L0.5**: Graph-plausible mechanism (paths exist) but not statistically tested
- **L0**: Web-sourced, LLM-inferred, or reasoning-only

Include epistemological composition summary at the end of the report.

## Fallback

If L0 generates nothing useful (all mechanisms are trivial or identical), fall back to current manual anchor approach. The pipeline is additive — current behavior is L0 = "human picks anchors" + L0.5 = "skipped."

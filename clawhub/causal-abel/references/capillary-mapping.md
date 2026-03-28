# Capillary Discovery Protocol

When a direct node returns 503/no-data, find observable supply-chain capillaries that carry the same economic signal. No hardcoded lookup tables — use reasoning and graph tools to discover capillaries dynamically.

## Discovery Contract

When `observe` fails on a target node, execute these steps in order:

### Step 1: Graph-structural discovery
Run `graph.neighbors` (both parents and children) on the failed node.
- If neighbors exist: these are graph-discoverable capillaries. Try `observe` on each.
- If observe succeeds on any neighbor: use it. Validate the economic relationship makes sense before trusting the signal.

### Step 2: Semantic discovery
If Step 1 returns zero neighbors (structurally isolated node), use `query_node` to search for the economic activity the target represents.
- Ask: "What companies' revenue is directly driven by this asset/market/activity?"
- Search terms should describe the economic function, not the asset name. For a crypto asset: search for exchanges, miners, infrastructure. For an index: search for its largest constituents. For a foreign market: search for US-listed companies operating in that market.
- Try `observe` on the top 2-3 results.

### Step 3: LLM reasoning (you)
If Steps 1-2 both fail, use your own world knowledge to identify the capillary network:
- Every traded asset has an economic ecosystem: issuers, exchanges, service providers, upstream suppliers, downstream consumers.
- Name 2-3 companies whose revenue mechanically correlates with the target's activity.
- Verify they exist in the graph with `query_node`, then `observe`.

### Step 4: Declare sparse
Only if all three steps fail to produce any observable capillary, declare this dimension graph-sparse and shift to web-primary for this dimension. This should be rare — most economic activities have a listed equity somewhere in the supply chain.

## Signal Aggregation

After observing capillaries:
- Aggregate into ONE directional signal per dimension (positive / negative / mixed / cooling / expanding)
- Never present individual capillary observations in the verdict layer
- In the evidence appendix, note which capillaries were used and how they were discovered (graph / semantic / reasoning)
- When capillaries within a dimension diverge (e.g., platform up but content owner down), name the divergence — it IS the signal

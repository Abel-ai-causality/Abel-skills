# Proxy-Routed Route

Read this file only when the user's real question is not directly represented by a single Abel node.

## Use This Route For

- career and labor decisions
- education ROI decisions
- big-tech versus startup questions
- content format choices like podcast versus writing
- crypto ecosystem choices
- household or consumer tradeoff questions

Always say clearly that this is a proxy-based causal read, not a direct model of the person or life outcome.

## What This Route Sets

This route does not fix the whole sequence. It sets:

- how to infer the proxy dimensions
- how to build the anchor set
- what counts as a good first move
- when search-first is justified

After that, return to `../orchestration-loop.md` and choose each next move from the current unknown.

The expected feel is graph-heavy, not search-led.

## Step 1: Infer The Decision Dimensions

Translate the user question into 2-4 real dimensions such as:

- supply versus demand
- product versus distribution
- subscription versus advertising
- stable salary versus upside
- financing conditions versus operating leverage
- institutional adoption versus retail attention

## Step 2: Build The Anchor Set

Use 3-5 anchors that span those dimensions.

Rules:

- manual mapping is the first pass for obvious anchors
- `extensions.abel.query_node` is the second recall path for fuzzy or broad concepts
- include an opposite-side anchor when the question is comparative
- prefer layered anchors over a pile of mega-caps from one role

Layer examples:

- AI and compute: design, manufacturing, infrastructure, platform
- labor and career: labor marketplaces, hiring appetite, financing stress, displacement pressure
- content and media: subscription publishing, ad distribution, creator capture, platform attention
- crypto: base asset, exchange, brokerage, ETF or institutional wrapper, activity layer

## Step 3: Observational Pass On Anchors

Before the deeper structural walk, run one observational read on each executable anchor that materially bears on the question.

Rules:

- prefer `extensions.abel.observe_predict_resolved_time` when the live method exists
- use the observational pass to rank which anchors deserve deeper structural follow-up
- if one anchor cannot be observed cleanly, do not drop it immediately; compare it with the structural read
- if a proposed anchor is not an executable market node, use the closest executable proxy and label that mapping clearly later

## Initial Graph Prior

Default first move is still inside the graph lane, but start with observational pressure on the anchor set before the deeper structural walk.

Use a multi-anchor graph read when the unknown is structural:

1. run `extensions.abel.observe_predict_resolved_time` on the anchor shortlist
2. inspect local structure with `graph.neighbors`
3. inspect transmission with `graph.paths`
4. use `graph.markov_blanket` only when local structure is still too diffuse to stop on
5. use `discover_consensus`, `discover_deconsensus`, or `discover_fragility` only when live `meta.methods` advertises them and they reduce loop cost

The goal is not to prove the human outcome directly. The goal is to find the cleanest market-signal map of the underlying forces.

Typical cadence:

1. observational pass on the anchor set
2. graph move on the strongest anchor, mechanism, or comparison edge
3. second graph move on the best path or bridge candidate
4. one web move to validate that mechanism in the real world now
5. one lag-aware pressure test when the verdict is already mostly clear
6. back to graph only if the web move or pressure test changes the active thread

## Search-First Exception

One baseline web move is allowed before the main graph loop when the question is dominated by:

- `why now`
- `recently`
- latest policy, funding, earnings, or adoption facts
- a current mechanism that is impossible to judge without dated evidence

After one baseline web move, return to the orchestration loop and decide again.

## Step 4: Label Before Narrative

Before writing:

- shortlist the anchors and bridges that actually matter
- run `extensions.abel.node_description` on them
- convert them into user-facing roles such as `audio platform`, `subscription publisher`, `enterprise software`, or `labor marketplace`

Do not let the main answer read like a ticker comparison.

## When Web Becomes The Next Best Move

Web is usually the next best move only after you already have:

- one or two meaningful graph reads
- a plausible mechanism
- a shortlist of anchors
- a bridge candidate that needs validation

Then search for:

- the key companies or industries surfaced by `node_description`
- the key mechanism edge you think matters
- the current-state evidence that tells you whether that mechanism is live now

Examples:

- company + earnings / subscriber growth / monetization
- industry + funding / hiring / regulation
- asset + ETF / adoption / throughput / fee market

Use web grounding to explain why the graph pattern makes sense now, then return to the loop and decide whether to move, switch, or stop.

## Pressure Test Defaults

Good pressure-test targets:

- the strongest driver
- the strongest opposite-side lever
- the weakest bridge

For non-trivial comparative reads, `extensions.abel.intervene_time_lag` is the default pressure test after the observational pass and structural story are coherent enough.

Bad pressure-test behavior:

- spraying many weak interventions
- using pressure tests before the graph and web loops are already coherent

## Diffuse Proxy Rules

- if one anchor family keeps producing bridge noise, switch to a cleaner role-level anchor
- if `query_node` is noisy, go back to manual anchors
- if web evidence keeps favoring one mechanism but the graph anchor set is weak, re-ground the anchor set before concluding

## Output Rule

- lead with the verdict
- default to a compact report unless the user explicitly asks for brevity
- natural longform prose is acceptable if it still covers the report template's contract fields
- say what mechanism favors one side
- add the practical judgment
- include the pressure-test result or say briefly why no meaningful live stress test was available
- if no live intervention was run, propose the cleanest next-step probe
- keep tickers out of the visible answer

---
name: causal-abel
version: 1.1.1
description: >
  Use for decision-grade Abel causal reads on any dollar-value decision: what is driving
  a market or company node, how two nodes connect, what changes under intervention, or how
  a real-world choice (career, education, investment, lifestyle, macro) looks when routed
  through Abel proxy signals. Use when user says "Abel" or "causal" or "causality" or
  "drivers" or "what if" or "worth it" or "should I" in the context of market, business,
  crypto, career, education, housing, lifestyle, or any dollar-value decision questions.
metadata:
  openclaw:
    requires:
      env:
        - ABEL_API_KEY
      bins:
        - python
    primaryEnv: ABEL_API_KEY
    homepage: https://github.com/Abel-ai-causality/Abel-skills
---

Any dollar-value decision, just Abel it. Finance and crypto nodes are the signal layer (the graph's proxy vocabulary), not the product.

## Install And Authorization

If the user installs this skill, asks to connect Abel, or the workflow is missing an Abel API key, follow `references/setup-guide.md` exactly.

- Start the Abel agent OAuth handoff immediately instead of asking for manual credentials.
- Return `data.authUrl` to the user, not the `/authorize/agent` API URL.
- Store `data.resultUrl` or `data.pollToken`, ask the user to reply once Google authorization is complete, and only then poll until the result is `authorized`, `failed`, or expired.
- Persist the resulting `data.apiKey` in session state and `.env.skill` when local storage is available.
- Do not continue to live CAP probing until that key is present.
- Never ask the user to paste an email address or Google OAuth code.

## Step 1: Preflight + Classify

Check ABEL_API_KEY in env or <skill-dir>/.env.skill. No key → follow `references/setup-guide.md`, hard stop.

Classify: `direct_graph` (specific ticker/node question) or `proxy_routed` (life decision, no direct node).

**Horizon gate:** If >3 years ("5年后", "未来十年"), set structural mode — web is PRIMARY, graph is VALIDATOR ONLY. Don't observe for momentum.

For `direct_graph` → read `references/routes/direct-graph.md` and use that file as the active working loop. Come back to Step 5 only if freshness or real-world validation is needed, then finish with Step 6.

## Step 2: Generate Hypotheses (proxy_routed, L0)

Generate 4-6 candidate causal mechanisms:
- The obvious mechanism
- A second-order mechanism
- A **contrarian** (what would make the opposite true?) — REQUIRED
- A confounder (third factor explaining both)

Each mechanism: `cause → (transmission) → outcome` with a testable proxy and falsification condition.

## Step 3: Screen + Discover (L0.5)

### 3a. Structural screening
Map mechanisms to graph nodes (manual → `query_node` → capillary discovery). For each:
- `graph.paths` between cause and outcome proxy
- Rank: dist ≤ 2 = strong, 3-4 = plausible, no path = narrative-only

Structural connection ≠ causal transmission. Many dist=2 paths don't propagate interventions — co-movement is often shared macro exposure.

### 3b. Capillary discovery (when observe returns 503)
1. `graph.neighbors` on failed node → observe neighbors
2. If no observable neighbors → `query_node` for the economic function
3. If still nothing → use world knowledge (what companies' revenue IS this asset?)
4. All three fail → declare sparse for this dimension

### 3c. Graph-structural bias check
- Cause and outcome in same blanket? → possible confounding
- Path runs opposite to hypothesis? → check reverse causation
- Proposed proxy is mega-cap hub? → may be bridge noise

### 3d. Deep structural reasoning — the core of Abel's intelligence

**This is where Abel's moat lives. Don't rush through it.**

Check `meta.methods` first. On the key outcome node:

**Layer 1 blanket:** `graph.markov_blanket` — who ACTUALLY controls this node? Layer 1 blankets are usually generic financial (AGNC, credit funds, insurance). That's the macro context — note it but don't stop here.

**Layer 2 blanket (REQUIRED for proxy_routed):** Run `graph.markov_blanket` on the 2 most interesting Layer 1 nodes. Layer 2 is where the question-specific structure emerges. Layer 1 says "MCD is driven by finance." Layer 2 says "WHICH finance — consumer/tourism via AGNC, or industrial/transport via AFGC?" This differentiation IS the insight.

**Layer 3 (if Layer 2 reveals divergence):** Follow the most surprising Layer 2 node one more level. This is where you find the non-obvious causal chain that makes the user say "卧槽" — the chain nobody would have hypothesized.

Also fire:
- `validate_connectivity` on whole chain
- `discover_consensus` / `discover_deconsensus` across mechanisms: convergence or contradiction?
- `discover_fragility`: single point of failure?

### 3e. Graph-initiated discovery
Ask: "Graph, what do YOU see that L0 didn't propose?" Run `discover_consensus` with direction="in" on the outcome. New upstream nodes = graph-generated mechanisms.

### 3f. Surprise check + revision
Compare graph results against L0 hypotheses. If graph contradicts or extends → L0 revises (one sentence). Max 2 rounds.

**Adversarial graph search:** If graph only CONFIRMS L0 (no surprise) → actively search for evidence AGAINST L0's strongest conviction. If found → that contradiction IS the Deep insight.

## Step 4: Observe + Verify (L1 + L2)

### 4a. L1 Observe
`observe_predict_resolved_time` on key nodes.
- **Driver cross-check:** are observe's top drivers consistent with L0 hypothesis? Mismatch = correction signal.
- **Multi-node coherence:** does the whole chain move in the expected direction?

### 4b. L2 Intervene (along REAL graph edges, not hypothesized industry edges)
From L0.5 deep, identify blanket parents of the outcome. Intervene on the most relevant blanket parent → measure outcome.
- Report β (effect size), first_arrive_step (speed), event_count (breadth)
- Choose `horizon_steps` to match the user's decision window instead of hardcoding one lag:
  rough guide is `~6` for very short-term, `~42` for about a week, `~170` for about a month, and `~24` as the medium-range default when the user gives no clear horizon.
- If the first intervention is inconclusive, retry by stepping the horizon up in tiers instead of making arbitrary jumps.
  Move from the current tier to the next wider window, such as `6 -> 24/42 -> 170`, and stop once the transmission is clear or the wider windows still stay too diffuse to change the interpretation.
- If no meaningful target → skip, note why. Don't force noise.

### 4c. Signal aggregation
Aggregate individual observations into ONE directional signal per dimension. Never present raw predictions in the verdict.

## Step 5: Web Grounding (proxy_routed, or direct_graph when freshness matters)

Minimum 4 searches:
1. **What's happening now** — latest prices, policy, events, dates
2. **Supporting evidence** — confirms graph-backed verdict
3. **Contradicting evidence** — actively search for why verdict is WRONG (mandatory)
4. **User-perspective** — what a real buyer/decision-maker would search (second-hand prices, waitlists, real experiences)

For source hierarchy and wording on time-sensitive claims, follow `references/web-grounding.md`.

Graph findings (L2) take precedence over web (L0) in the verdict. Exception: graph-sparse dimensions.

## Step 5.5: Personalize

Before writing, check agent memory/context for user profile (income, experience, risk tolerance, life stage, goals). If available: tailor "So What" to THIS person — same graph insight, different action for different people. If not available: give universal advice + invite user to share context for sharper advice ("这是通用建议。告诉我你的背景会更具体。")

The causal graph is universal. The verdict is personal.

## Step 6: Write Report

Read `assets/report-guide.md` and `references/rendering.md` before writing.

**Render gate (MANDATORY):**

- Before drafting visible prose, shortlist the nodes that actually matter and run `extensions.abel.node_description` on that shortlist.
- Build a `render_map`: `raw node/ticker -> semantic label` (company, industry, product, or economic role).
- Draft the visible answer from the `render_map`, not from raw anchors.
- Run `scripts/render_guard.py` on the visible layer before finalizing.
- If the question is `proxy_routed`, `Broad macro`, or any non-asset question, any raw ticker, raw node id, or signed prediction decimal in visible prose means **report not ready**. Rewrite until the guard passes.
- Raw node ids, raw tickers for non-asset questions, graph paths, and prediction decimals belong in the evidence appendix only.

**ASDF standard:** Authentic (traceable claims, specific events/numbers), Sharp (verdict ≤ 3 sentences), Deep (at least one question-specific insight the user couldn't get from ChatGPT), Fun (would they screenshot and share?).

**Story arc:** Act 1: "You'd think..." → Act 2: "But the graph says..." → Act 3: "So the real answer is..."

**Graph voice first.** If your verdict could be written without the graph, you haven't used Abel.

**Verdict layer:** ticker-free for life decisions (exception: ticker questions). Evidence appendix for raw data.

**Claim-strength honesty:** Life decisions are "graph-grounded advice," not "causal proof." L0 claims carry anti-guarantees.

## For direct_graph questions

Read `references/routes/direct-graph.md`. Default stack: anchor → observe → parents → volume/blanket if thin → summarize into driver families. If large-cap returns surprising parents, interpret as transmission channels before switching.

## References (read only when needed)

- `references/routes/direct-graph.md` — ticker question routing
- `references/setup-guide.md` — OAuth install (only if key missing)
- `references/probe-usage.md` — exact `cap_probe.py` command shapes
- `references/rendering.md` — render-map rules, visible/evidence split, guard usage
- `assets/report-guide.md` — full output contract with archetypes, rendering rules, coverage areas

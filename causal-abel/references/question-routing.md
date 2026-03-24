# Question Routing Guide

Use this file for the detailed decision logic behind `causal-abel` after `SKILL.md` has already told you that the skill applies.

## Two Modes

### 1. Direct CAP Mode

Use this when the user is already asking about graph structure or CAP verbs.

Examples:

- What is driving `X`?
- Why did `X` move?
- Which nodes matter around `X`?
- Is there a path from `X` to `Y`?
- What happens if `X` changes?
- If `X` had been different, what would happen to `Y`?
- What causal capabilities does this server expose?

### 2. Proxy-Routing Mode

Use this when the user is asking a real cause-effect question, but the graph does not contain direct nodes for the topic itself.

Examples:

- Should my kid pursue music or writing?
- Is an MBA worth it?
- Will AI replace designers or writers?
- Is cooking at home better than ordering out?
- How will AGI affect ordinary people?

Do not stop at "the graph only has equities and crypto." Route the question through proxy tickers that encode the relevant dimensions as market signals, then run CAP exploration on those proxies. Always say clearly that this is a proxy-based causal read, not a direct model of personal aptitude or life satisfaction.

## Working Loop

1. Start from the live server and the causal question.
   - Default CAP target: `https://cap.abel.ai` unless the user gives a different `base_url`.
   - `https://cap-sit.abel.ai` is the SIT variant when you need the staging environment.
   - Treat `https://api.abel.ai/echo/` as the OAuth and business API host, not as the default CAP graph probe host.
   - Use the bundled probe script first so the call path is deterministic.

2. Classify the question.
   - `capability_discovery`: what can the server do?
   - `direct_graph`: drivers, neighbors, Markov blanket, reachability, intervention, preview.
   - `proxy_routed`: map to proxy dimensions and proxy tickers.

3. Pick the right graph surface.
    - Local structure: `neighbors`, `markov-blanket`, `traverse-parents`, `traverse-children`
    - Transmission and reachability: `paths`, `validate-connectivity`
    - Observational regime: `observe`
    - Intervention and rollout: `intervene-do` (with required path gate), `intervene-time-lag`
   - Counterfactual preview: `counterfactual-preview`

4. Explore structure before making strong claims.
   - Start local for drivers, parents, children, or surrounding context.
   - Use paths for transmission, intermediaries, reachability, or whether one node can influence another.
   - Read the graph for structure first: who connects to whom, through what intermediaries, and with what public semantics.

5. Move to effect surfaces only after the structural question is clear.
   - `observe.predict` answers what the current observational regime suggests.
   - `intervene.do` answers what changes under the public `do()` surface.
   - `extensions.abel.intervene_time_lag` answers how an intervention rolls out over time.
   - `extensions.abel.counterfactual_preview` gives a preview-only what-if result.

6. Keep the loop question-driven.
    - After each call, ask what open causal question remains.
    - Good follow-ups are: who are the immediate drivers, is there a path, does a proxy node look real or just a bridge, what changes under intervention, and does a richer Abel extension materially change the interpretation.
    - Stop when the public CAP surface has answered the user's question or can honestly say no more.

## Node Normalization Gate

Before any live CAP call, normalize the input into the actual public Abel node-id form.

Decision order:

1. If the input is already `<ticker>_close` or `<ticker>_volume`, use it unchanged.
2. If the input looks like a real ticker such as `NVDA`, `SPOT`, or `ETHUSD`, default to `<ticker>_close`.
3. Only switch the default to `<ticker>_volume` when the question is explicitly about volume, trading activity, participation, or liquidity rather than price regime.
4. If the input is a company name, brand, or proxy phrase such as `Spotify`, `New York Times`, or `music streaming`, map it to a real ticker first.
5. If there is no honest ticker mapping, stop instead of probing a guessed node.

Interpretation rule:

- Proxy words are not executable nodes.
- Bare tickers are query shapes.
- `<ticker>_close` and `<ticker>_volume` are executable Abel public node ids.

## Standard Direct Graph Workflows

Use one workflow at a time. Do not mix driver discovery, reachability audit, and intervention testing into one long default chain.

### 1. `driver_explanation`

Use this for questions like "what is driving `X`" or "why did `X` move".

Default sequence:

1. Start with one direct-parent surface:
   - `traverse.parents`, or
   - `graph.neighbors` with `scope=parents`
2. If immediate drivers are still unclear, add `graph.markov_blanket`.
3. If the user then asks how a specific candidate reaches the node, run `graph.paths` only for that narrowed candidate.

Decision gates:

- Do not run `neighbors`, `traverse.parents`, `graph.markov_blanket`, and `extensions.abel.markov_blanket` all by default.
- Use `extensions.abel.markov_blanket` only when CAP core blanket output is insufficient for the real question.
- Do not default to `observe.predict` or `intervene.do` once the driver question has already been answered structurally.

Stop when:

- immediate drivers are clear enough to answer the user, or
- the remaining uncertainty is about transmission or effect rather than local drivers

### 2. `reachability_check`

Use this for questions like "can `X` influence `Y`" or "how does `X` reach `Y`".

Default sequence:

1. Run `graph.paths(source, target)` on the specific ordered pair.
2. If the user has a small candidate set and wants to know which are even worth path inspection, use `extensions.abel.validate_connectivity` as a screening step.
3. If a path exists and the user now wants effect semantics, move to an intervention workflow instead of continuing to fan out more path calls.

Decision gates:

- Do not probe both directions by default in a directed causal graph. Reverse the direction only if the user asks for the opposite claim or the first answer leaves direction itself unresolved.
- Do not sweep many unrelated tickers through repeated `graph.paths` calls unless the user explicitly wants a comparative screening task.
- Path existence answers reachability, not effect size.

Stop when:

- the graph has established whether a path exists,
- the main intermediaries are known, and
- the remaining question is no longer structural

### 3. `intervention_effect`

Use this for questions like "what happens if `X` changes".

Default sequence:

1. Confirm minimal structure first with one of:
   - `graph.paths(treatment, outcome)`, or
   - `traverse.parents(outcome)` when the question is about a likely direct driver
2. If the structural case is plausible, run `intervene.do`. In the bundled probe, `intervene-do` now performs the `graph.paths` check first and skips the intervention when no directed path is found.
3. If the user cares about rollout over time, add `extensions.abel.intervene_time_lag`.

Decision gates:

- Do not run intervention by default after a broad exploratory sweep.
- Do not use `observe.predict` as a substitute for intervention effect.
- If the path check finds no directed treatment-outcome path, stop and say the intervention was skipped for lack of structural support.
- If `intervene.do` fails, do not compensate by launching many more exploratory structure calls. Surface the failure honestly and note that intervention feasibility and complexity controls belong in the CAP package or server behavior.

Stop when:

- the intervention answer is returned,
- the intervention is rejected by the server, or
- the remaining question is really about temporal rollout or counterfactual framing

## Universal Question Routing

### Direct Graph Questions

- **"What can this server do?"** -> `capabilities`
- **"What's driving X?"** -> `neighbors`, `markov-blanket`, `traverse-parents`
- **"What does X influence?"** -> `neighbors --scope children`, `traverse-children`
- **"How does X reach Y?"** -> `paths`, sometimes `validate-connectivity`
- **"What happens if X changes?"** -> `intervene-do`, then `intervene-time-lag` if rollout matters
- **"If X had been different?"** -> `counterfactual-preview`
- **"Is this a CAP feature or an Abel extension?"** -> `capabilities`, then interpret the namespace and notes

### Proxy-Routed Questions

Map the question to decision dimensions, then choose 3-5 proxy tickers that encode those dimensions as market signals.

| Dimension | Proxy tickers | What they proxy |
|-----------|---------------|-----------------|
| AI displacement | `NVDA`, `MSFT`, `ADBE`, `FVRR`, `UPWK` | AI capability growth vs creative or labor platform pressure |
| Career / labor | `FVRR`, `UPWK`, `HYG` | Labor market flexibility, hiring appetite, credit conditions |
| Education ROI | `CHGG`, `DUOL`, `LOPE` | Education disruption, enrollment, skill signaling |
| Music / creative | `SPOT`, `UMG`, `WMG`, `SNAP` | Creator economics, streaming monetization, audience capture |
| Writing / publishing / media | `NYT`, `SNAP`, `SPOT` | Media economics, creator distribution, attention markets |
| Consumer / food / convenience | `DASH`, `KR`, `WMT`, `COST` | Convenience vs grocery and household budget trade-offs |
| Gaming / entertainment | `NTDOY`, `MSFT`, `AMD`, `NVDA` | Platform economics, hardware cycles, entertainment demand |
| Housing / real estate | `ITB`, `DHI`, `MBB`, `VNQ` | Builders, mortgage pressure, real-asset demand |
| Macro / China-US AI | `NVDA`, `BABA`, `BIDU`, `SMIC`, `USDCNY` proxies | Cross-ecosystem coupling, policy and supply-chain stress |

Routing rules:

- Pick 3-5 proxies that span the decision's key dimensions.
- Include at least one proxy from the opposite side of the decision when possible.
- Prefer layered routing over only mega-caps; mid-cap or supply-chain-specific names often carry cleaner signal.
- For broad comparisons or theme questions, treat those 3-5 proxies as independent anchors first, then compare where they converge before writing the story.
- For live Abel CAP calls, map proxies to real Abel node ids before probing; the current public graph expects `<ticker>_close` or `<ticker>_volume`, not free-form proxy labels.
- Treat proxy tickers in this table as routing anchors, not as proof that the exact node is present in the current graph. Normalize first, then validate with the live surface if existence is uncertain.
- The user should not see tickers as the answer. Tickers are intermediate routing signals.
- In user-facing prose, translate proxy nodes into economic roles first.
- If no honest proxy set exists, say so instead of forcing a story.

For repeatable layered anchor selection, see `layered-routing.md`.

## Search Rule

If search tools are available, use them to explain mechanisms, not to replace graph reasoning.

- Search only when you already know the edge, path, or proxy dimension you are trying to explain.
- If you cannot state the edge or proxy dimension first, stop and go back to the graph.
- Use `search-loop.md` when the query needs more than a single explanatory lookup.

Search template:

```text
Edge or proxy: [NodeA -> NodeB] or [proxy dimension]
Causal question: [WHY this connection matters / WHAT current real-world mechanism it represents]
Query: [terms derived from both nodes or the proxy dimension]
```

### Graph -> Search Triggers

Search is justified when one of these is true:

1. the graph suggests an edge or path, but the mechanism is unclear
2. a proxy dimension is honest but too abstract, and you need current real-world evidence for what it represents
3. the same candidate appears across multiple anchors and you need to check whether it is a real convergence node or just a bridge
4. a path looks structurally plausible, but the current state or catalyst timing is unclear

### Search -> Graph Triggers

Go back to graph structure after search when one of these is true:

1. search reveals a new causal entity that looks mappable to a real ticker or node candidate
2. search clarifies that a suspected mechanism is really a transmission path question
3. search provides counter-evidence to the current path story and the structure needs verification
4. search shows a second-order effect that should be checked with `paths`, `neighbors`, `traverse-parents`, or `validate-connectivity`

### Search Feedback Scan

After each search result, explicitly scan for:

- new entity to map into the graph
- current-state update on an existing edge or proxy dimension
- strongest contradiction to the current story
- second-order effect worth a structural follow-up

If none of those appear, the search loop is probably converging and another search hop is unlikely to add value.

## Multi-Anchor Convergence

Use convergence mode when the user asks a broad comparison, theme question, or life decision where a single anchor would be too fragile.

### When To Activate

- the question spans several economic layers or competing mechanisms
- one anchor produces a noisy or overly bridge-heavy local neighborhood
- the user wants the strongest shared signal across a theme, not a single-node explanation

### Workflow

1. Pick 3-5 anchors across the key dimensions.
2. Run independent structural reads on each anchor. Prefer one clean first read per anchor such as `traverse.parents`, `neighbors`, or `paths`.
3. Record repeated nodes, repeated bridge types, and repeated proxy dimensions.
4. Validate the strongest repeated candidate with a narrower CAP check such as `paths`, `validate-connectivity`, or a local neighborhood read.
5. If search tools are available and a repeated candidate still needs mechanism evidence, run an edge-anchored search.
6. Stop when the repeated signal stabilizes, not when every possible anchor has been exhausted.

### Convergence Heuristics

- repeated appearance across 2 anchors is worth checking
- repeated appearance across 3+ anchors is a strong candidate hub
- repeated bridge-only appearance is weaker than repeated real-economy appearance, but do not discard it automatically if the graph signal is consistent
- semantically strange nodes can still matter; keep them when structure is repeated and the mechanism can be grounded honestly

### Early Stop Rules

- stop when anchor results keep repeating with no new open causal question
- stop when two consecutive searches are low-signal and do not change the next graph question
- stop when the main unresolved uncertainty is a future event rather than a current structural or mechanism question

## Narration And Semantic Guardrails

### Structure Over Prediction

Read the graph for structure, not just directional output.

- Causal topology: who connects to whom, through what intermediaries
- Tau / lag: how fast effects propagate
- Path shape: whether the link is direct, indirect, or absent
- Local neighborhood: whether a node is surrounded by coherent drivers or noisy bridges
- Cross-dimension coupling: whether different proxy layers reinforce or contradict one another

For proxy-routed human questions, the graph is not modeling the child, the writer, or the life choice directly. It is modeling the financial shadow of the underlying forces. Be explicit about that.

### User-Facing Narration Rules

- Prefer present-tense framing such as "in the current graph" or "on the current CAP surface" over date-stamped retrieval language, unless the user asks for a dated audit trail.
- Use human or industry descriptions first when a node is only a proxy or a bridge.
- Keep raw node IDs and tickers for trace, verification, command examples, or when the user explicitly asks for exact nodes.
- If the relationship is indirect, say that plainly.

### Semantic Guardrails

- `observe.predict` is observational prediction, not causal effect.
- `intervene.do` is the smaller public intervention surface.
- `extensions.abel.intervene_time_lag` is the richer temporal rollout surface.
- `extensions.abel.validate_connectivity` is a proxy validation gate, not formal identification.
- `extensions.abel.counterfactual_preview` is preview-only approximate graph propagation, not full SCM counterfactual inference.
- CAP core and Abel extensions should be explained separately when that distinction matters.
- This wrapper is thin: it exposes contracts, capability metadata, and gateway-backed public semantics; it does not invent new causal computation.
- Proxy-routed answers are market-signal reads, not direct models of personal talent, family fit, or values.
- Separate graph fact, searched mechanism, and inference whenever the distinction matters.

## See Also

- `../SKILL.md` for the short agent-facing framework
- `../assets/report-template.md` for result organization centered on question, nodes, verb findings, and meaning
- `search-loop.md` for edge-anchored search discipline
- `layered-routing.md` for layered proxy anchor selection
- `capability-layers.md` for CAP core versus Abel extension disclosure depth
- `probe-usage.md` for command details and reusable `cap_probe.py` examples

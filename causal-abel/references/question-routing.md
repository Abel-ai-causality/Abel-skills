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
   - Intervention and rollout: `intervene-do`, `intervene-time-lag`
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
- The user should not see tickers as the answer. Tickers are intermediate routing signals.
- In user-facing prose, translate proxy nodes into economic roles first.
- If no honest proxy set exists, say so instead of forcing a story.

## Search Rule

If search tools are available, use them to explain mechanisms, not to replace graph reasoning.

- Search only when you already know the edge, path, or proxy dimension you are trying to explain.
- If you cannot state the edge or proxy dimension first, stop and go back to the graph.

Search template:

```text
Edge or proxy: [NodeA -> NodeB] or [proxy dimension]
Causal question: [WHY this connection matters / WHAT current real-world mechanism it represents]
Query: [terms derived from both nodes or the proxy dimension]
```

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

## See Also

- `../SKILL.md` for the short agent-facing framework
- `../assets/report-template.md` for result organization centered on question, nodes, verb findings, and meaning
- `capability-layers.md` for CAP core versus Abel extension disclosure depth
- `probe-usage.md` for command details and reusable `cap_probe.py` examples

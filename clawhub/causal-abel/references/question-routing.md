# Question Routing Guide

Use this file for the detailed decision logic behind `causal-abel` after `SKILL.md` has already told you that the skill applies.

## Three Modes

### 1. Direct Graph Mode

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

### 3. Capability Discovery Mode

Use this only when the user is explicitly inspecting the server surface, mounted verbs, or request/response contracts.

## Working Loop

1. Start from the live server and the causal question.
   - Default CAP target: `https://gateway-sit.abel.ai/api` unless the user gives a different `base_url`.
   - Production CAP target: `https://cap.abel.ai`.
   - SIT CAP target: `https://gateway-sit.abel.ai/api`.
   - Treat `https://api-sit.abel.ai/echo/` as the OAuth and business API host, not as the default CAP graph probe host.
   - Use the bundled probe script first so the call path is deterministic.

2. Classify the question.
   - `capability_discovery`: inventory or targeted method lookup
   - `direct_graph`: drivers, neighbors, reachability, intervention, preview
   - `proxy_routed`: map to proxy dimensions and proxy tickers.

3. Ground the nodes before probing.
   - If the input is already a public node id, keep it unchanged.
   - For obvious company names or familiar proxy anchors, manual ticker mapping is the default first pass.
   - For fuzzy names, concept words, Chinese phrases, or broad proxy labels, check live `meta.methods` and use `extensions.abel.query_node` when available.
   - Treat manual mapping and `query_node` as two recall paths. Merge them, shortlist the 2-5 most honest candidates, then continue.
   - Use `extensions.abel.node_description` only on the shortlisted nodes that matter for role labeling or bridge disambiguation.

4. Start graph-first.
   - Local structure default: `graph.neighbors`
   - Transmission default: `graph.paths`
   - `graph.markov_blanket` is a fallback when local structure is still low-signal
   - After the proxy set is stable, run a short-term observational pass on anchors
   - Effect surfaces come later

5. Run a multi-round graph-first loop.
   - After each call, ask what open causal question remains.
   - Choose the single next graph call with the highest information gain.
   - Keep looping while a real open question remains and the answer quality is still improving.
   - Stop when the conclusion is already strong enough for the user-facing answer.

6. Run a web-grounded evidence pass after structure is clear.
   - For `proxy_routed` questions, this is the default second stage, not an optional flourish.
   - Use ordinary web or news search, not image search.
   - Search only for a graph-grounded target: one edge, one candidate node, one sector, or one proxy dimension at a time.
   - Use the search pass to explain the current real-world mechanism behind the graph finding.

7. Move to pressure-test surfaces only after the structural question is clear.
   - `extensions.abel.observe_predict_resolved_time` gives the current observational baseline plus the resolved prediction timestamp.
   - `observe.predict` is the core fallback when the extension is unavailable.
   - `intervene.do` is the compact "push this lever" pressure test.
   - `extensions.abel.intervene_time_lag` shows how that pressure rolls out over time.
   - `extensions.abel.counterfactual_preview` gives a preview-only alternate-path test.

8. Use optional discovery shortcuts only when they reduce loop cost.
   - If live `meta.methods` advertises `extensions.abel.discover_consensus`, use it after the seed set is already stable to summarize a baseline consensus path.
   - If live `meta.methods` advertises `extensions.abel.discover_deconsensus`, use it to surface contrast candidates after the baseline is already clear.
   - If live `meta.methods` advertises `extensions.abel.discover_fragility`, use it only on a narrow shortlist of suspected load-bearing bridge nodes.
   - None of these should replace the first structural pass.

9. If search tools are available, use them to explain a known edge, path, or proxy tension.
   - Do not search without a graph-grounded question.
   - Do not let search replace graph reasoning.
   - For current-state, market-signal, or decision questions, do not stop at graph-only narration if a focused search could materially clarify the mechanism.

10. Run a brief red-team pass before finalizing.
   - State the strongest untested assumption.
   - State the strongest counter-evidence or alternative explanation you found.
   - State the weakest link in the graph path, bridge node, or proxy mapping.
   - If the conclusion depends on current mechanism and search is available, use one adversarial or falsification-oriented search.
   - If this materially weakens the thesis, lower certainty or switch to a conditional verdict.

11. Write the answer in old Abel app style.
   - verdict first
   - causal link second
   - compact full report after the first-screen answer for high-stakes or non-trivial analyses
   - concise card inside that report
   - optional trace only when useful

## Grounding Gate

Before any live CAP call, ground the input into the actual public Abel node-id form.

Decision order:

1. If the input is already `<ticker>_close` or `<ticker>_volume`, use it unchanged.
2. If the input looks like a real ticker such as `NVDA`, `SPOT`, or `ETHUSD`, default to `<ticker>_close`.
3. If the input is a bare crypto alias such as `BTC`, `ETH`, or `SOL`, expand it to `<alias>USD_close` first.
4. Only switch the default to `<ticker>_volume` when the question is explicitly about volume, trading activity, participation, or liquidity rather than price regime.
5. If the input is a company name, brand, or proxy phrase such as `Spotify`, `New York Times`, or `music streaming`, use manual mapping first when it is obvious.
6. If the phrase is fuzzy, multilingual, or concept-heavy, check live `meta.methods` and use `extensions.abel.query_node` when available.
7. If there is no honest ticker or node mapping after the combined recall step, stop instead of probing a guessed node.

Interpretation rule:

- Proxy words are not executable nodes.
- Bare tickers are query shapes.
- `_close` means close price. `_volume` means close volume.
- For crypto, the practical executable form is usually `*USD_close` or `*USD_volume`.
- `extensions.abel.node_description` is a label helper for shortlisted nodes, not a substitute for graph structure.
- `BTCUSD_close` is currently a bad bridge candidate.
  - recent validation found no parents, no children, and sampled paths to common anchors were disconnected
  - treat it as effectively independent unless fresh probes show otherwise

## Standard Direct Graph Workflows

Use one workflow at a time. Do not mix driver discovery, reachability audit, and intervention testing into one bloated default chain.

### 1. `driver_explanation`

Use this for questions like "what is driving `X`" or "why did `X` move".

Default sequence:

1. Start with one direct-parent surface:
   - `graph.neighbors` with `scope=parents`, or
   - `traverse.parents`
2. Choose the strongest open question from the result:
   - which parent actually matters most
   - whether a surprising parent is real or just local noise
   - whether one candidate has a meaningful path into the node
3. Run the next narrowed structural call:
   - another `graph.neighbors`
   - a narrowed `graph.paths`
   - `graph.markov_blanket` only if the local picture is still muddy
4. If the user gave a fuzzy company or concept label and one shortlisted node still feels semantically ambiguous, use `extensions.abel.node_description` on that narrow shortlist before narrating a driver story.
5. Stop when the immediate drivers are already clear enough for the answer.

Decision gates:

- Do not run `neighbors`, `traverse.parents`, `graph.markov_blanket`, and `extensions.abel.markov_blanket` all by default.
- Use `extensions.abel.markov_blanket` only when CAP core blanket output is insufficient for the real question.
- Do not default to `observe.predict` or `intervene.do` once the driver question has already been answered structurally.
- Do not keep looping once new rounds stop changing the answer.

Stop when:

- immediate drivers are clear enough to answer the user, or
- the remaining uncertainty is about transmission or effect rather than local drivers

### 2. `reachability_check`

Use this for questions like "can `X` influence `Y`" or "how does `X` reach `Y`".

Default sequence:

1. Run `graph.paths(source, target)` on the specific ordered pair.
2. If the returned path opens a better follow-up question, inspect the most important intermediary with `graph.neighbors`.
3. If the user has a small candidate set and wants to know which are even worth path inspection, use `extensions.abel.validate_connectivity` as a screening step.
4. If a path exists and the user now wants effect semantics, move to an intervention workflow instead of continuing to fan out more path calls.
5. If a bridge node looks load-bearing and live `meta.methods` advertises `extensions.abel.discover_fragility`, use it on the narrow shortlist to test whether the bridge is structurally fragile or replaceable.

Decision gates:

- Do not probe both directions by default in a directed causal graph. Reverse the direction only if the user asks for the opposite claim or the first answer leaves direction itself unresolved.
- Do not sweep many unrelated tickers through repeated `graph.paths` calls unless the user explicitly wants a comparative screening task.
- Path existence answers reachability, not effect size.

Stop when:

- the graph has established whether a path exists,
- the main intermediaries are known, and
- the remaining question is no longer structural

### 3. `pressure_test`

Use this for questions like "what happens if `X` changes", "what would flip the conclusion", or "which next lever should we test".

Default sequence:

1. Confirm minimal structure first with one of:
   - `graph.paths(treatment, outcome)`, or
   - `traverse.parents(outcome)` when the question is about a likely direct driver
2. Decide which single lever is most decision-relevant to stress:
   - the strongest driver behind the current verdict
   - the opposite-side lever that could flip the verdict
   - the weakest bridge node in the current explanation
3. If the structural case is plausible, run `intervene.do`.
4. If the user cares about rollout over time, add `extensions.abel.intervene_time_lag`.
5. If a live pressure test is low-signal or not worth the cost, switch to one graph-grounded fallback:
   - a cleaner bridge candidate
   - an alternate anchor on the losing side
   - a counterfactual target that would better expose flip risk

Decision gates:

- Do not run a pressure test by default after a broad exploratory sweep.
- Do not use `observe.predict` as a substitute for intervention effect.
- If `intervene.do` fails, do not compensate by launching many more exploratory structure calls. Surface the failure honestly and note that intervention feasibility and complexity controls belong in the CAP package or server behavior.
- Prefer one strong pressure test over many weak ones.
- Prefer a graph-lever stress test over a user workflow suggestion.
- The goal is calibration: what would make the verdict more robust, weaker, or conditional.
- Do not turn the pressure-test section into an execution plan, AB content plan, or generic "what you should try next" list.

Stop when:

- the pressure test answer is returned,
- the intervention is rejected by the server, or
- you have identified the cleanest fallback stress target and how it could change the verdict

## Universal Question Routing

### Direct Graph Questions

- **"What's driving X?"** -> start `graph.neighbors`, then loop on the best open structural question
- **"What does X influence?"** -> `graph.neighbors --scope children`, then loop if needed
- **"How does X reach Y?"** -> `graph.paths`, then inspect the most important intermediary if needed
- **"What happens if X changes?"** -> structure first, then a single pressure test with `intervene.do`, then `intervene-time-lag` if rollout matters
- **"If X had been different?"** -> structure first, then `counterfactual-preview`
- **"What can this server do?"** -> `meta.capabilities`, then targeted `meta.methods`
- **"Is this a CAP feature or an Abel extension?"** -> targeted discovery, not a whole-surface dump

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
- For live Abel CAP calls, map proxies to real Abel node ids before probing; the current public graph expects `<ticker>_close` or `<ticker>_volume`, not free-form proxy labels.
- Manual mapping is still the default first pass for obvious proxy anchors.
- For fuzzy or broad proxy phrases, use `extensions.abel.query_node` as a second recall path instead of guessing a ticker too early.
- Treat proxy tickers in this table as routing anchors, not as proof that the exact node is present in the current graph. Normalize first, then validate with the live surface if existence is uncertain.
- The user should not see tickers as the answer. Tickers are intermediate routing signals.
- In user-facing prose, translate proxy nodes into economic roles first.
- If no honest proxy set exists, say so instead of forcing a story.
- In a multi-round loop, do not spread attention evenly. Keep following the proxy, path, or bridge node that most improves the answer.
- If the seed set is already stable and live `meta.methods` advertises `extensions.abel.discover_consensus` or `extensions.abel.discover_deconsensus`, use them as optional shortcuts for baseline vs contrast, not as the first move.
- Once the anchor set is stable, run a quick observational pass across the main anchors.
  - check `meta.methods` first for the latest predictive extension surface
  - prefer `extensions.abel.observe_predict_resolved_time` when it is advertised there
  - fall back to `observe.predict`
  - use the sign and relative magnitude to summarize short-term pressure or support
  - treat returned drivers as hints for follow-up, not as clean user-facing anchors
  - for fast-moving extension verbs, prefer the generic `verb` caller over hard-coded wrappers

## Candidate Typing And Financial Small-Cap Handling

Classify graph candidates before you search them.

- `macro-linked non-financial`
  - operating companies, sectors, or macro-sensitive businesses with ordinary public evidence trails
- `financial transmission node`
  - closed-end funds, preferred shares, mortgage REITs, BDCs, and thinly-covered finance names that often act as bridges
- `idiosyncratic small-cap node`
  - names whose public narrative is dominated by listing, financing, merger, or other company-specific noise

Handling rules:

- Treat financial transmission nodes as bridge candidates first, not final narrative anchors.
- If the graph repeatedly returns financial transmission nodes with weak public evidence, switch source:
  - use `graph.markov_blanket`, or
  - deepen one hop on 1-2 financial parents and keep only cleaner second-hop candidates for search.
- If a financial or small-cap candidate has both strong graph signal and dated external evidence, keep it at equal priority. Do not downweight it just because it looks non-obvious.
- If repeated searches on financial microcaps stay low-signal, summarize them as transmission noise rather than forcing them into the final story.
- If a bridge node repeats across multiple anchor pairs, check its neighborhood quality before promoting it.
  - Recent examples: `SIM_close` and `MOOOUSD_close` repeated across media/content anchor pairs, but their neighborhoods were still dominated by microcap and crypto-heavy names.
  - Practical rule: repeated appearance alone is not enough; repeated appearance plus a semantically interpretable neighborhood is the real promotion threshold.

## Search Rule

If search tools are available, use them to explain mechanisms, not to replace graph reasoning.

- Search only when you already know the edge, path, or proxy dimension you are trying to explain.
- If you cannot state the edge or proxy dimension first, stop and go back to the graph.
- Use web or news search for this phase, not image search.
- For `proxy_routed` questions, search is the default second stage once the graph shortlist is clear.
- Each search should target one subject only.
- Default progression:
  - one baseline search for the key dimension or anchor
  - one focused search on the strongest candidate
  - one fallback search on a cleaner sector or comparison anchor if the first candidate is low-signal

Search template:

```text
Edge or proxy: [NodeA -> NodeB] or [proxy dimension]
Causal question: [WHY this connection matters / WHAT current real-world mechanism it represents]
Query: [terms derived from both nodes or the proxy dimension]
```

## Red Team Rule

Before you lock the answer, try to break it.

- `untested assumption`: name the assumption that is carrying the most weight but is not directly established
- `counter-evidence`: identify the strongest contrary signal from graph or web evidence
- `weakest link`: identify the bridge node, edge, or proxy mapping most likely to fail
- For non-trivial proxy-routed decisions, do one falsification-oriented search when search is available
- If the red-team pass changes the conclusion, surface that openly in `Certain`, `Decision tip`, or `Caveats`

## Pressure Test Rule

After the main graph and search read is clear, ask one more question: what would most likely flip or weaken the conclusion?

- If the answer points to a specific graph lever, run one pressure test.
- If the answer points to a broader real-world condition that the graph cannot stress cleanly, map it back to one cleaner graph lever instead of falling into generic planning advice.
- Good pressure-test targets:
  - the strongest driver in favor of the current verdict
  - the strongest driver on the losing side
  - the bridge node most likely to be transmission noise
- Good user-facing pressure-test lines:
  - "If attention-distribution weakens, the writing-first thesis loses its edge here."
  - "If creator-monetization on audio/video improves, this flips toward the audio side."
  - "If this bridge node is dropped and the path disappears, confidence should fall sharply."
- Keep this short. It is a calibration pass, not a second full report.

## Answer Style

### Structure Over Prediction

Read the graph for structure, not just directional output.

- Causal topology: who connects to whom, through what intermediaries
- Tau / lag: how fast effects propagate
- Path shape: whether the link is direct, indirect, or absent
- Local neighborhood: whether a node is surrounded by coherent drivers or noisy bridges
- Cross-dimension coupling: whether different proxy layers reinforce or contradict one another

For proxy-routed human questions, the graph is not modeling the child, the writer, or the life choice directly. It is modeling the financial shadow of the underlying forces. Be explicit about that.

### User-Facing Narration Rules

- Lead with the verdict, not the method.
- After the verdict, state the causal link in plain language.
- Then give a compact full report:
  - `Intent read`
  - `Graph mapping`
  - `Graph walk findings`
  - `Web-grounded evidence`
  - `Integrated interpretation`
  - `Pressure test`
  - `Challenges`
- Inside that report, compress the takeaway into a short card:
  - `Signal`
  - `Causal link`
  - `Sharp`
  - `Certain`
  - `Decision tip`
- Keep raw tickers out of all visible sections before `Trace`.
- In visible prose, translate nodes into roles, sectors, products, or mechanisms first.
- Prefer present-tense framing such as "in the current graph" over date-stamped retrieval language, unless the user asks for a dated audit trail.
- Use human or industry descriptions first when a node is only a proxy or a bridge.
- Keep raw node IDs and tickers for trace, verification, command examples, or when the user explicitly asks for exact nodes.
- If the relationship is indirect, say that plainly.
- Keep capability/protocol commentary brief unless the user explicitly asked for it.
- For `proxy_routed` answers, include a short `Trace` block by default when it helps verify the proxy dimensions or anchors.
- For blocked runs, include a short `Trace` block that states the intended normalization and next structural move instead of pretending the graph was queried.

### Minimal Guardrails

- `observe.predict` is observational prediction, not causal effect.
- `intervene.do` is the smaller public intervention surface.
- `extensions.abel.intervene_time_lag` is the richer temporal rollout surface.
- `extensions.abel.validate_connectivity` is a proxy validation gate, not formal identification.
- `extensions.abel.counterfactual_preview` is preview-only approximate graph propagation, not full SCM counterfactual inference.
- Proxy-routed answers are market-signal reads, not direct models of personal talent, family fit, or values.

## See Also

- `../SKILL.md` for the short agent-facing framework
- `../assets/report-template.md` for result organization centered on question, nodes, verb findings, and meaning
- `probe-usage.md` for command details and reusable `cap_probe.py` examples

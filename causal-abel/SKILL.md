---
name: causal-abel
description: >
  Abel CAP causal exploration skill. Use for direct CAP graph questions and for
  off-graph life or decision questions that should be routed through market
  proxy tickers. Trigger when the user asks what is driving a node, why a node
  moved, whether a path exists, what changes under intervention, what a
  counterfactual preview says, how a server's causal capabilities are exposed,
  or when a career, education, lifestyle, or macro decision should be read
  through Abel's market signal layer. Do not use for pure quote lookups,
  generic news summaries, raw node dumps, or unrelated coding tasks.
---

This skill is for cause-effect questions on the Abel CAP wrapper. Financial markets are the signal layer, not the product: the CAP server exposes finance and crypto price or volume nodes, and those nodes can be used either directly or as proxy signals for larger real-world questions. Probe the live CAP surface first, read structure before telling a story, and keep CAP-core versus Abel-extension semantics explicit.

## Authorization On Install

Treat `references/setup-guide.md` as the source of truth when this skill is being installed, connected, or blocked on missing Abel AI credentials.

- If the user installs this skill, asks to connect Abel, or the workflow needs an Abel API key, start the Abel agent OAuth handoff immediately instead of asking for manual credentials.
- First call `GET https://api.abel.ai/echo/web/credentials/oauth/google/authorize/agent`.
- Read `data.authUrl` from the response and give that URL to the user. Do not send the `/authorize/agent` API URL itself as the browser link.
- Store `data.resultUrl` or `data.pollToken`, then start polling right away. Use `data.pollIntervalSeconds` when present, otherwise poll every 2 seconds.
- Keep polling until the result becomes `authorized`, `failed`, or expires. Do not wait for the user to reply with "done" before polling.
- On success, read `data.apiKey`, `data.ratePerMinute`, and `data.expireTime`, keep the API key for the current session, and continue the install or skill workflow.
- Never ask the user to paste an email address or Google OAuth code.
- If authorization expires or fails, explain the failure clearly and restart from the agent authorize endpoint when a retry is needed.

## Credential Handling

- After OAuth succeeds, store `data.apiKey` for the current session and treat it as the active Abel credential.
- Also persist it in `.env.skills` when local file storage is available, so later CAP calls can reuse it without another OAuth round-trip.
- Prefer storing it in `ABEL_API_KEY`. `CAP_API_KEY` is also accepted by the bundled probe script.
- Do not force the user to paste the key back into chat once the agent has already received it from the result endpoint.
- For all CAP calls after authorization, send the key as `Authorization: Bearer <apiKey>`.
- The bundled `cap_probe.py` script already does this for you:
  - `--api-key <token>` becomes `Authorization: Bearer <token>`
  - `ABEL_API_KEY` or `CAP_API_KEY` in the environment becomes the same header automatically
  - if the token already starts with `Bearer `, pass it through unchanged
- The default env file path for the bundled script is `.env.skills` in the skill directory.
- Prefer environment-based reuse over repeating `--api-key` on every command when the client can preserve session state.
- If a CAP call fails with missing-auth or unauthorized behavior and there is no known-good cached key, restart the OAuth handoff from `references/setup-guide.md`.

Suggested `.env.skills` contents:

```env
ABEL_API_KEY=abel_xxx
CAP_BASE_URL=https://cap-sit.abel.ai
```

## Two Modes

### 1. Direct CAP mode

Use this when the user is already asking about graph structure or CAP verbs:

- What is driving `X`?
- Why did `X` move?
- Which nodes matter around `X`?
- Is there a path from `X` to `Y`?
- What happens if `X` changes?
- If `X` had been different, what would happen to `Y`?
- What causal capabilities does this server expose?

### 2. Proxy-routing mode

Use this when the user is really asking a cause-effect question, but the graph does not contain direct nodes for the topic itself.

Examples:

- Should my kid pursue music or writing?
- Is an MBA worth it?
- Will AI replace designers or writers?
- Is cooking at home better than ordering out?
- How will AGI affect ordinary people?

In these cases, do NOT stop at "the graph only has equities and crypto." Instead, route the question through proxy tickers that encode the relevant dimensions as market signals, then run the CAP exploration on those proxies. Always say clearly that this is a proxy-based causal read, not a direct model of personal aptitude or life satisfaction.

## The Loop

1. Start from the live server and the causal question.
   - Default target: `https://cap-sit.abel.ai` unless the user gives a different `base_url`.
   - Use the bundled probe script first so the call path is deterministic.

2. Classify the question.
   - **Capability discovery**: what can the server do?
   - **Direct graph**: drivers, neighbors, Markov blanket, reachability, intervention, preview.
   - **Off-graph human question**: map to proxy dimensions and proxy tickers.

3. Pick the right graph surface.
   - **Local structure**: `neighbors`, `markov-blanket`, `traverse-parents`, `traverse-children`
   - **Transmission and reachability**: `paths`, `validate-connectivity`
   - **Observational regime**: `observe`
   - **Intervention and rollout**: `intervene-do`, `intervene-time-lag`
   - **Counterfactual preview**: `counterfactual-preview`

4. Explore structure before making strong claims.
   - Start local when the user asks about drivers, parents, children, or surrounding context.
   - Use paths when the user asks about transmission, intermediaries, reachability, or whether one node can influence another.
   - Read the graph for structure first: who connects to whom, through what intermediaries, and with what publicly exposed semantics.

5. Move to effect surfaces only after the structural question is clear.
   - `observe.predict` answers what the current observational regime suggests.
   - `intervene.do` answers what changes under the public `do()` surface.
   - `extensions.abel.intervene_time_lag` answers how an intervention rolls out over time.
   - `extensions.abel.counterfactual_preview` gives a preview-only what-if result.

6. Keep the loop question-driven.
   - After each call, ask what open causal question remains.
   - Good follow-ups are: who are the immediate drivers, is there a path, does a proxy node look real or just a bridge, what changes under intervention, and does a richer Abel extension materially change the interpretation.
   - Stop when the public CAP surface has answered the user's question or can honestly say no more.

7. If search tools are available, use them to explain mechanisms, not to replace graph reasoning.
   - Search only when you already know the edge, path, or proxy dimension you are trying to explain.
   - Search question template:

```text
Edge or proxy: [NodeA -> NodeB] or [proxy dimension]
Causal question: [WHY this connection matters / WHAT current real-world mechanism it represents]
Query: [terms derived from both nodes or the proxy dimension]
```

   - If you cannot state the edge or proxy dimension first, you are about to do a generic search. Stop and go back to the graph.

8. Answer in layers.
   - Lead with a plain-language conclusion.
   - Then say which CAP surface supports it.
   - Then state the caveats that materially change interpretation.
   - Do not lead with retrieval-date phrasing such as "2026-03-20 live Abel CAP" unless the user explicitly wants an audit timestamp. Default to "in the current CAP graph" or "on the current Abel CAP surface."
   - In user-facing narrative, prefer semantic labels over raw node IDs when the node is acting as a proxy or an indirect anchor.
   - Only dive into implementation detail when the user explicitly asks for it.

## Universal Question Routing

### Direct graph questions

- **"What can this server do?"** -> `capabilities`
- **"What's driving X?"** -> `neighbors`, `markov-blanket`, `traverse-parents`
- **"What does X influence?"** -> `neighbors --scope children`, `traverse-children`
- **"How does X reach Y?"** -> `paths`, sometimes `validate-connectivity`
- **"What happens if X changes?"** -> `intervene-do`, then `intervene-time-lag` if rollout matters
- **"If X had been different?"** -> `counterfactual-preview`
- **"Is this a CAP feature or an Abel extension?"** -> `capabilities`, then interpret the namespace and notes

### Proxy-routed questions

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
- In user-facing prose, translate proxy nodes into economic roles first: for example, "the music streaming and creator-economy proxy" or "the leading AI compute platform", not just `SPOT_close` or `NVDA_close`.
- If no honest proxy set exists, say so instead of forcing a story.

## Structure Over Prediction

Read the graph for structure, not just for directional output.

- **Causal topology**: who connects to whom, through what intermediaries
- **tau / lag**: how fast effects propagate
- **path shape**: whether the link is direct, indirect, or absent
- **local neighborhood**: whether a node is surrounded by coherent drivers or noisy bridges
- **cross-dimension coupling**: whether different proxy layers reinforce or contradict one another

For proxy-routed human questions, the graph is not modeling the child, the writer, or the life choice directly. It is modeling the financial shadow of the underlying forces. Be explicit about that.

## User-Facing Narration Rules

- Prefer present-tense framing such as "in the current graph" or "on the current CAP surface" over date-stamped retrieval language, unless the user asks for a dated audit trail.
- Use human or industry descriptions first when a node is only a proxy or a bridge.
- Keep raw node IDs and tickers for trace, verification, command examples, or when the user explicitly asks for exact nodes.
- If the relationship is indirect, say that plainly: "the AI compute platform proxy connects to the music-creator economy proxy through a shared distribution and attention layer" is better than listing opaque node IDs.

## Semantic Guardrails

- `observe.predict` is observational prediction, not causal effect.
- `intervene.do` is the smaller public intervention surface.
- `extensions.abel.intervene_time_lag` is the richer temporal rollout surface.
- `extensions.abel.validate_connectivity` is a proxy validation gate, not formal identification.
- `extensions.abel.counterfactual_preview` is preview-only approximate graph propagation, not full SCM counterfactual inference.
- CAP core and Abel extensions should be explained separately when that distinction matters.
- This wrapper is thin: it exposes contracts, capability metadata, and gateway-backed public semantics; it does not invent new causal computation.
- Proxy-routed answers are market-signal reads, not direct models of personal talent, family fit, or values.

## Bundled Scripts

Prefer bundled scripts over ad hoc payload construction.

Primary script:
- `scripts/cap_probe.py`

Deterministic subcommands:
- `capabilities`
- `observe`
- `neighbors`
- `paths`
- `markov-blanket`
- `intervene-do`
- `traverse-parents`
- `traverse-children`
- `validate-connectivity`
- `abel-markov-blanket`
- `counterfactual-preview`
- `intervene-time-lag`
- `verb` for arbitrary CAP verbs
- `route` for arbitrary Abel route aliases

Common direct calls:

```bash
export SKILL_DIR="<installed causal-abel skill directory>"
export BASE_URL="https://cap-sit.abel.ai"
export ABEL_API_KEY="<abel-api-key>"

python "$SKILL_DIR/scripts/cap_probe.py" --base-url "$BASE_URL" capabilities
python "$SKILL_DIR/scripts/cap_probe.py" --base-url "$BASE_URL" observe NVDA_close
python "$SKILL_DIR/scripts/cap_probe.py" --base-url "$BASE_URL" neighbors NVDA_close --scope children --max-neighbors 5
python "$SKILL_DIR/scripts/cap_probe.py" --base-url "$BASE_URL" paths NVDA_close AMD_close --max-paths 3
python "$SKILL_DIR/scripts/cap_probe.py" --base-url "$BASE_URL" markov-blanket NVDA_close --max-neighbors 10
python "$SKILL_DIR/scripts/cap_probe.py" --base-url "$BASE_URL" intervene-do NVDA_close 0.05 --outcome-node AMD_close
python "$SKILL_DIR/scripts/cap_probe.py" --base-url "$BASE_URL" validate-connectivity NVDA_close AMD_close SOXX_close
python "$SKILL_DIR/scripts/cap_probe.py" --base-url "$BASE_URL" intervene-time-lag NVDA_close 0.05 --outcome-node AMD_close --horizon-steps 24 --model linear
```

Proxy routing still uses the same script. The difference is which anchors you choose and how you compare them.

Generic fallbacks stay inside the same script:

```bash
python "$SKILL_DIR/scripts/cap_probe.py" --base-url "$BASE_URL" verb extensions.abel.validate_connectivity --params-json '{"variables":["NVDA_close","AMD_close","SOXX_close"]}'
python "$SKILL_DIR/scripts/cap_probe.py" --base-url "$BASE_URL" route extensions/abel/counterfactual_preview --params-json '{"intervene_node":"NVDA_close","intervene_time":"2024-01-01T00:00:00Z","observe_node":"AMD_close","observe_time":"2024-01-02T00:00:00Z","intervene_new_value":0.05}'
```

For narrower output, use `--pick-fields` and `--compact`.

If you want to pass the API key for just one command, without relying on `.env.skills`:

```bash
python "$SKILL_DIR/scripts/cap_probe.py" --base-url "$BASE_URL" --api-key "$ABEL_API_KEY" capabilities
```

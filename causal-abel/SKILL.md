---
name: causal-abel
version: 1.0.7
update_repo: Abel-ai-causality/Abel-skills
update_branch: main
update_skill_path: causal-abel
update_changelog_path: /CHANGELOG.md
description: >
  Use when the user asks what is driving a node, how one node reaches another,
  what changes under intervention, or an off-graph decision that should be
  routed through Abel market proxies.
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

Use this skill for cause-effect questions on the Abel public CAP surface. Finance and crypto nodes are the signal layer, not the product. Read structure first, keep following the most valuable open causal question, then validate the winning mechanism with ordinary web search before you finalize the answer.

The answer should feel like old Abel app output, not like protocol documentation:

- verdict first
- causal link second
- ticker-hidden visible text
- concise, decision-grade wording
- graph-grounded web evidence when the question is proxy-routed or current-state dependent
- optional trace only when it adds verification value

## Authorization Gate

Authorization is a required entry step for this skill when it will call Abel APIs on the user's behalf.

- Before any live Abel CAP or business API call, check whether an Abel user API key is already available in session state, `--api-key`, or `.env.skills`.
- If no key is available, stop and follow `references/setup-guide.md` immediately. Do not start CAP probing or any other live API call first.
- Never print, quote, or paste the raw API key, OAuth result payload, or `.env.skills` contents into user-visible text, logs, or trace output. Check key presence without echoing secrets.
- The agent entrypoint is `GET https://api-sit.abel.ai/echo/web/credentials/oauth/google/authorize/agent`.
- Return only the resulting `data.authUrl` to the user, store `data.resultUrl` or `data.pollToken`, ask the user to tell the agent when Google authorization is finished, and only then poll until the result is `authorized`, `failed`, or expired.
- Never ask the user to paste an email address, OAuth code, or raw API key when the handoff flow can obtain the key directly.

## When To Use

Use `causal-abel` when the user needs causal structure, path reasoning, local driver analysis, intervention-based pressure testing, counterfactual preview, or a proxy-routed decision read over the Abel public graph.

Typical triggers:

- what is driving a node
- why a node moved
- which nodes matter around a node
- whether one node can reach another
- what changes under intervention or pressure test
- what a counterfactual preview implies
- off-graph human questions that should be routed through market proxies
- deep graph walk requests where the user wants the structure explained, not dumped

Do not use this skill for:

- pure quote lookups
- generic news summaries with no causal question
- raw node dumps with no interpretation
- unrelated coding or repo tasks

## How To Use

### 1. Preflight

- If `ABEL_API_KEY` is missing from session state, `--api-key`, and `.env.skills`, run the OAuth handoff from `references/setup-guide.md`.
- Treat missing credentials as a hard stop for live Abel CAP usage.

### 2. Runtime target

- Default CAP target: `https://gateway-sit.abel.ai/api`.
- Production CAP target: `https://cap.abel.ai`.
- SIT CAP target: `https://gateway-sit.abel.ai/api`.
- Treat `https://api-sit.abel.ai/echo/` as the OAuth and business API host, not as the default public CAP probe host.
- Use the bundled probe path first so call behavior stays deterministic.

### 3. Classify the task

Always classify the request before calling anything:

- `capability_discovery`
- `direct_graph`
- `proxy_routed`

Default interpretation:

- if the user asks about a specific node, path, driver, or what-if -> `direct_graph`
- if the user asks a real-world decision question with no direct node -> `proxy_routed`
- if the user is explicitly inspecting the server surface -> `capability_discovery`

### 4. Ground the executable nodes

Before any live CAP call:

1. If the input is already `<ticker>_close` or `<ticker>_volume`, use it unchanged.
2. If the input looks like a real equity or ETF ticker such as `NVDA` or `SPOT`, default to `<ticker>_close`.
3. If the input is a bare crypto alias such as `BTC`, `ETH`, or `SOL`, expand it to `*USD_close` first.
4. `_close` means close price. `_volume` means close volume.
5. Only switch the default to `<ticker>_volume` when the question is explicitly about volume, liquidity, or participation.
6. Use manual mapping first for obvious company names, familiar proxy anchors, and stable ticker knowledge.
7. If the input is a fuzzy company name, concept, Chinese phrase, or broad proxy idea such as `Spotify`, `music streaming`, or `半导体`, check live `meta.methods` and use `extensions.abel.query_node` when it is available.
8. Treat manual mapping and `query_node` as two recall paths. Merge them, shortlist 2-5 honest candidates, then continue.
9. Use `extensions.abel.node_description` only on the shortlisted nodes that matter for label quality, role assignment, or bridge disambiguation. Do not fetch descriptions for everything.
10. If there is no honest ticker or node mapping after grounding, stop instead of probing a guessed node.

Practical crypto rule:

- use `ETHUSD_close`, `SOLUSD_close`, `BTCUSD_close`, not `ETH_close` or `BTC_close`
- `BTCUSD_close` currently behaves like an isolated node in recent validation, so do not spend time trying to use it as a bridge unless fresh probes show otherwise

### 5. Run a multi-round graph-first loop

This is the main behavior. Do not collapse it into a one-shot lookup when real uncertainty remains.

Rules:

- start with structure, not prediction
- continue while an open causal question remains
- each round should pick the single next call with the highest information gain
- stop when the answer is already strong enough for the user-facing conclusion

#### 5A. `direct_graph`

Default first move:

- driver question -> `graph.neighbors(scope=parents)` or `traverse.parents`
- downstream question -> `graph.neighbors(scope=children)` or `traverse.children`
- transmission / reachability question -> `graph.paths`

Then loop:

1. Read the returned structure.
2. Ask what open causal question remains.
3. Choose the next structural call:
   - another `graph.neighbors`
   - a narrowed `graph.paths`
   - `graph.markov_blanket` only if local structure stays unclear
4. Only after the structure is clear, decide whether a pressure test adds value:
   - `extensions.abel.observe_predict_resolved_time`
   - `observe.predict`
   - `intervene.do`
   - `extensions.abel.intervene_time_lag`
   - `extensions.abel.counterfactual_preview`

Hard rules:

- Do not use `observe.predict` as a substitute for structure.
- For proxy-routed anchor comparison, run a short-term observational pass once the proxy set is stable.
- When you want the latest server-specific predictive surface, check `meta.methods` first instead of assuming the wrapper is current.
- Prefer `extensions.abel.observe_predict_resolved_time` when `meta.methods` says it is available because it returns the resolved prediction timestamp.
- When live `meta.methods` advertises newer extension helpers, prefer discovering them and calling them through the generic `verb` path over assuming the bundled script already has a dedicated wrapper.
- Call unstable or newly added extension verbs through the generic `verb` path rather than assuming a dedicated local wrapper already exists.
- Fall back to core `observe.predict` when the extension surface is unavailable.
- Do not start with `intervene.do` for a driver question.
- Do not fire every graph verb by default.
- Stop when the last round did not materially change the answer and no better open question remains.

#### 5B. `proxy_routed`

Map the real-world question into proxy dimensions, then into executable nodes.

Default sequence:

1. infer the actual decision the user cares about
2. extract the key dimensions behind that decision
3. choose 3-5 proxy tickers that span those dimensions
4. include an opposite-side proxy when the decision is comparative
5. normalize proxies into `<ticker>_close`
6. run a multi-anchor graph-first loop:
   - `graph.neighbors`
   - `graph.paths`
   - `graph.markov_blanket` when local structure is still low-signal or when the returned candidates are dominated by transmission nodes
   - if the seed set is already stable and live `meta.methods` advertises `extensions.abel.discover_consensus` or `extensions.abel.discover_deconsensus`, use them as optional summary or contrast shortcuts rather than as the first structural move
7. once the proxy set is stable, run a short-term observational pass on the main 2-5 anchors:
   - prefer `extensions.abel.observe_predict_resolved_time`
   - fall back to `observe.predict`
   - use the sign and relative magnitude as a quick trend / pressure read
   - treat returned `drivers` as hints, not as trusted narrative anchors
8. if one bridge candidate looks load-bearing and live `meta.methods` advertises `extensions.abel.discover_fragility`, use it as an optional structural risk check for that narrow shortlist rather than as a default broad scan
9. once the graph has surfaced 1-2 plausible mechanisms, run graph-grounded web search before finalizing
10. if a shortlisted node looks like a financial transmission node or idiosyncratic microcap, treat it as a bridge first:
   - search it once if the graph signal is strong
   - if evidence is weak, validate one path or deepen one hop, then switch the search anchor to a sector, macro-linked non-financial name, or cleaner bridge
11. use pressure-test surfaces only when they genuinely sharpen the answer

Proxy rules:

- proxy nodes are routing signals, not the answer itself
- visible output should describe roles, sectors, and mechanisms first
- the user should not see raw tickers unless they asked for them
- do not overclaim that the graph is directly modeling a person, value system, or life outcome
- do not let thinly-covered financial names dominate the story unless graph signal and dated evidence both support them

#### 5C. `capability_discovery`

Keep this narrow and utilitarian.

- use `meta.capabilities` for inventory
- use `meta.methods` only for the verbs actually under discussion
- do not default to whole-surface dumps
- do not let capability discovery hijack a normal analysis request

### 6. Search policy

If web search tools are available, use them to explain mechanisms, not to replace graph reasoning.

Default rule:

- for `proxy_routed` questions, web search is the default second phase after the graph shortlist is clear
- for direct graph questions, web search is required when the answer depends on current catalysts, recency, policy, or real-world mechanism rather than pure structure

Hard rules:

- Use ordinary web or news search for evidence grounding, not image search.
- Search only when you already know the edge, path, candidate node, or proxy dimension you are trying to explain.
- If you cannot state that graph-grounded target first, go back to the graph.
- Each search should target one subject only: one node, one company, one sector, or one proxy dimension.
- Prefer 1 baseline search plus 1-2 focused searches over a broad spray of weak searches.
- If a financial transmission node or microcap has weak external evidence, do not keep searching it repeatedly. Validate one path, then switch to a cleaner anchor.
- Stop searching when extra evidence is unlikely to change the user-facing conclusion.

### 7. Pressure tests are secondary

Use these only after the structural question is already clear.

Default role:

- pressure-test the working thesis
- show what would have to change for the answer to flip
- identify which graph lever or proxy dimension has the highest flip power

Pressure-test surfaces:

- `observe.predict`: current observational regime baseline
- `intervene.do`: compact "push this lever and see what moves" test
- `extensions.abel.intervene_time_lag`: rollout stress test over time
- `extensions.abel.counterfactual_preview`: preview-only alternate-path test

Rules:

- Do not run a pressure test before the graph and search loop has already exposed the key mechanism.
- Prefer one meaningful pressure test over a wide spray of weak interventions.
- Prefer a real graph-lever stress test over a user-workflow suggestion.
- When applicable, pressure-test one of:
  - the strongest driver behind the current verdict
  - the opposite-side lever that could flip the verdict
  - the weakest bridge node in the current explanation
- Name the stress target explicitly as `if this node / bridge / proxy dimension moves, the conclusion changes most here`.
- If a live pressure test would be low-signal, blocked, or excessive, give one graph-grounded fallback such as a cleaner bridge, alternate anchor, or counterfactual target. Do not default to an execution plan or AB content plan.
- Treat the pressure test as calibration. It should sharpen the decision, not restart exploration from scratch.

### 7A. Red Team pass

Before finalizing, run one brief challenge pass against your own conclusion.

Required checks:

- `Untested assumption`: what you are assuming but the graph or web evidence did not directly establish
- `Counter-evidence`: the strongest alternative explanation or contrary signal you found
- `Weakest link`: the path edge, bridge node, or proxy mapping that could most plausibly break the conclusion

Rules:

- For high-stakes or non-trivial proxy-routed decisions, include a red-team pass by default.
- If web search is available and the conclusion depends on current real-world mechanism, spend at least one search on the strongest alternative explanation or falsification angle.
- Do not write fake balance such as "there are pros and cons" or "the sector has opportunities and challenges."
- If the red-team pass materially weakens the original thesis, lower certainty, switch the verdict to conditional, or say the answer is closer than it first looked.
- Keep the challenge pass evidence-based and short. It exists to calibrate confidence, not to bury the answer.

### 8. Answer contract

- For high-stakes or non-trivial `proxy_routed` and multi-step graph investigations, produce a compact full report.
- Low-stakes casual comparisons can stay shorter, but they still need graph-grounded reasoning and, when relevant, at least one web-grounded mechanism.
- Only collapse to a short answer when the user explicitly asks for "brief", "一句话", "short", or "just give me the pick".

#### 8A. First screen

Lead with:

1. direct verdict
2. causal link in plain language
3. decision tip or practical judgment

Visible-text rules:

- do not lead with tool names, APIs, or protocol framing
- do not start with a worldview preamble
- do not show raw tickers in the main answer unless the user explicitly asks for them
- keep raw tickers out of `Intent read`, `Graph mapping`, `Graph walk findings`, `Web-grounded evidence`, `Integrated interpretation`, and `Insight Card`
- translate nodes into roles, sectors, products, or mechanisms in all visible sections before `Trace`

#### 8B. Compact full report

After the first screen, default to these sections in order:

- `Intent read`
- `Graph mapping`
- `Graph walk findings`
- `Web-grounded evidence`
- `Integrated interpretation`
- `Insight Card`
- `Pressure test`
- `Challenges`
- `Caveats`

#### 8C. Insight Card

After the first screen, compress the answer into this card:

- `Signal`
- `Causal link`
- `Sharp`
- `Certain`
- `Decision tip`

When applicable, add one short follow-through block after the card:

- `Pressure test`: the one graph lever you stressed, the impacted node or proxy dimension, and whether the verdict held

#### 8D. Optional trace

Only when it helps:

- `Routing`
- `Searches used`
- `Used surfaces`
- `Key nodes`
- `Challenges` or `Caveats`
- `Pressure test` when one was run

Keep trace separate from the main answer. It is for verification, not for headline reading.

Default trace rule:

- for `proxy_routed` answers, include a short `Trace` block by default unless the user explicitly wants no trace
- for auth-blocked or environment-blocked runs, include a short `Trace` block that says what node normalization or first graph step would have happened next
- keep the trace to 2-5 short lines
- keep visible-text prose human first; reserve raw node ids or tickers for trace when useful

### 9. Minimal guardrails

Do not make this the center of the answer, but do keep these boundaries straight:

- `observe.predict` is observational, not intervention
- `intervene.do` is a compact pressure test, not full rollout explanation
- `counterfactual_preview` is preview-only
- proxy-routed reads are signal reads, not direct models of a human subject

## Install And Authorization

If the user installs this skill, asks to connect Abel, or the workflow is missing an Abel API key, follow `references/setup-guide.md` exactly.

- Start the Abel agent OAuth handoff immediately instead of asking for manual credentials.
- Return `data.authUrl` to the user, not the `/authorize/agent` API URL.
- Store `data.resultUrl` or `data.pollToken`, ask the user to reply once Google authorization is complete, and only then poll until the result is `authorized`, `failed`, or expired.
- Persist the resulting `data.apiKey` in session state and `.env.skills` when local storage is available.
- Do not continue to live CAP probing until that key is present.
- Never ask the user to paste an email address or Google OAuth code.

## Detailed References

- Detailed routing logic, multi-round graph loop guidance, proxy dimensions, and narration rules: `references/question-routing.md`
- Report organization for fuller write-ups: `assets/report-template.md`
- OAuth install flow, polling behavior, and API key reuse: `references/setup-guide.md`
- Probe script commands and reusable examples: `references/probe-usage.md`

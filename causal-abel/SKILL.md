---
name: causal-abel
version: 1.0.10
update_repo: Abel-ai-causality/Abel-skills
update_branch: main
update_skill_path: causal-abel
update_changelog_path: /CHANGELOG.md
description: >
  Use for decision-grade Abel causal reads: explain what is driving a market or
  company node, how two nodes connect, what changes under intervention, or how
  a real-world choice looks when routed through Abel proxy signals. Use when user says "Abel" or "causal" or "causality" or "drivers" or "what if" in the context of market, business, crypto, or proxy-routed questions.
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

Use this skill to turn market, business, crypto, and proxy-routed decision questions into decision-grade Abel reads. Finance and crypto nodes are the signal layer, not the product. The visible answer should usually be a compact report: verdict first, mechanism second, practical judgment third.

Keep the skill centered on three rules:

- Treat Abel graph outputs as primary evidence. The graph is high-value market-data causal structure, not a weak brainstorming prior.
- For direct graph questions, answer the graph fact first. Do not replace a clear graph result with a more intuitive web narrative.
- For broad company or ticker driver questions, anchor to the executable ticker and actually run Abel on it before interpreting the result.

## Use This Skill For

- direct Abel graph questions about drivers, paths, neighborhoods, and interventions
- proxy-routed decisions where the graph does not contain the human question directly
- live CAP surface inspection and extension-verb discovery

Do not use it for pure price quotes, generic news summaries, raw node dumps, or unrelated repo work.

## Authorization Gate

- Before any live Abel CAP or business API call, check session state, `--api-key`, or `<skill-root>/.env.skill`.
- If a key is already available, skip auth references and continue.
- If no key is available, stop and follow `references/setup-guide.md`.
- Return only `data.authUrl` to the user, store `data.resultUrl` or `data.pollToken`, ask the user to confirm when browser auth is finished, and only then poll.
- Never ask the user to paste an email address, OAuth code, or raw API key.

## Read Order

Read the minimum needed, in this order:

1. Stay in this file long enough to decide the mode.
2. Read `references/routes/capability-discovery.md` as the live-surface module.
3. Read exactly one usage route file:
   - `references/routes/direct-graph.md`
   - `references/routes/proxy-routed.md`
4. Read `references/orchestration-loop.md`.
5. If you need node mapping or human-facing labels, read `references/grounding-and-labeling.md`.
6. If the next best move may be external evidence, read `references/web-grounding.md`.
7. For any comparative, proxy-routed, multi-anchor, or otherwise non-trivial read, open `assets/report-guide.md` before drafting the answer.
8. Only read `references/probe-usage.md` when you need exact `cap_probe.py` command shapes.

Do not read every reference file by default.

## Step 1: Preflight

- Treat missing credentials as a hard stop for live Abel usage.
- Default CAP target: `https://cap.abel.ai/api`.
- Treat `https://api.abel.ai/echo/` as the OAuth and business API host, not the CAP probe host.
- Use the bundled probe path first so call behavior stays deterministic.

## Step 2: Classify The Question

Pick one mode only:

- `direct_graph`: a specific node, path, driver, neighborhood, or what-if
- `proxy_routed`: a real-world decision with no direct node in the graph

Capability discovery is not a peer route. It is a mandatory ability:

- know how to check `meta.capabilities`
- know how to check targeted `meta.methods`
- know how to verify newer verbs from the live server instead of assuming local wrappers are current

## Step 3: Route

- `direct_graph` -> `references/routes/direct-graph.md`
- `proxy_routed` -> `references/routes/proxy-routed.md`

Read `references/routes/capability-discovery.md` as a required live-surface module, then use one usage route. Usage routes define the initial prior and default first move. They do not hardcode the whole chain.

## Step 4: Run The Unified Loop

After route selection, switch to the orchestration loop in `references/orchestration-loop.md`.

Each round:

1. state the current unknown
2. choose the best next tool: `graph` or `web`
3. investigate one candidate, one edge, or one mechanism at a time
4. decide `move`, `switch`, or `stop`

Default cadence is graph-heavy, but predictive before structural when executable anchors exist:

- `resolved-time observation -> graph -> graph -> maybe web -> lag pressure test`
- sometimes `resolved-time observation -> graph -> web -> graph -> lag pressure test`

Only go `web` early when the current unknown is clearly about freshness, timing, or live mechanism.

## Cross-Cutting Rules

### Grounding And Labels

- Use `references/grounding-and-labeling.md` whenever you need to map names, concepts, or proxies into executable nodes.
- Use manual mapping first for obvious company and crypto anchors.
- Use `extensions.abel.query_node` as the second recall path for fuzzy, multilingual, or concept-heavy inputs.
- Use `extensions.abel.node_description` on the final shortlist before writing the answer.
- In visible prose, prefer company names, sectors, products, or economic roles over raw tickers or raw node ids such as `*.price`.
- For listed-company driver questions, anchor the company to its ticker first, then treat the ticker node as the primary executable object.
- For broad reads, check `.price` first and add `.volume` only when it improves the interpretation of pressure or liquidity.

### Web Grounding

- Web is a peer tool inside the loop, not a mandatory final stage.
- The default bias is still toward graph work.
- For `proxy_routed`, web usually comes after 1-2 good graph moves on the current mechanism or shortlist.
- For `direct_graph`, web is required only when the user is asking for freshness, `why now`, current catalysts, policy, earnings, adoption, or a real-world mechanism that the graph itself does not already answer.
- In ClawHub / OpenClaw environments, first check whether a web search tool is actually available. If not, tell the user they need to install one before you can provide web-grounded validation.
- Search the company names, sectors, products, or mechanisms surfaced by `node_description`, not raw `*.price` strings.
- Search is there to explain or validate graph-backed mechanisms, not replace graph work.
- If web evidence suggests a more intuitive story than the graph, do not overwrite the graph answer. State the graph finding first, then label the web-backed interpretation as explanation, validation, or unresolved tension.
- Use `references/web-grounding.md` for the search loop.

### Probe Discipline

- `extensions.abel.observe_predict_resolved_time` is the default observational surface when the live method exists.
- For executable anchors and comparison tickers that materially bear on the question, run one observational read before committing to deeper structure.
- `extensions.abel.intervene_time_lag` is the default pressure-test surface once the mechanism is coherent enough to stress.
- For broad driver questions on liquid names, default graph stack is:
  `anchor ticker -> observe price -> inspect parents on price -> inspect volume or local blanket only if interpretation is still thin -> summarize into driver families`
- Choose `horizon_steps` to match the user's decision window instead of hardcoding one lag:
  rough guide is `~6` for very short-term, `~42` for about a week, `~170` for about a month, and `~24` as the medium-range default when the user gives no clear horizon.
- If the first intervention is inconclusive, retry by stepping the horizon up in tiers instead of making arbitrary jumps.
  Move from the current tier to the next wider window, such as `6 -> 24/42 -> 170`, and stop once the transmission is clear or the wider windows still stay low-signal.
- Check `meta.methods` before assuming a local wrapper is current.
- Prefer the generic `verb` path for new or unstable extension verbs.
- If graph calls stay low-signal, switch the candidate, switch the tool, or stop instead of spraying more probes.
- If a large-cap or liquid asset returns surprising direct parents, do not stop with `semantic mismatch`. Use one more Abel move to decide whether those parents behave like liquidity proxies, macro proxies, sector transmission, or bridge noise.

## Answer Contract

- Lead with the verdict.
- Then state the causal link in plain language.
- Then give the practical judgment.
- Keep tool names, protocol framing, and raw node ids out of the main answer.
- For proxy-routed reads, say clearly that this is a market-signal proxy read, not a direct model of the person or life outcome.

### Graph-Fact-First Rule

For direct graph questions, the answer should preserve this order:

1. `graph_fact`: what the graph literally returned
2. `interpretation`: what that graph fact might mean in plain language
3. `web_validation`: only if the user asked for freshness or the interpretation needs dated evidence

Never collapse `graph_fact` into `interpretation`.

If the user asks a literal membership question such as:

- `X 的 driver 里有 Y 吗`
- `X 的上游是不是 Y`
- `X 受哪些因素影响`

then answer the graph fact directly with `yes/no` or a driver list before offering any realism check or explanatory caveat.

If the returned drivers are surprising, do not dismiss them as useless. Frame them as graph-discovered market-data drivers or cross-asset transmission signals, then state whether their economic interpretation is clear, weak, or still unresolved.

### Broad Driver Interpretation Rule

When the user asks for broad drivers of a ticker or company, do not stop at a raw list of direct parents unless the user explicitly wants only the literal parent set.

After reporting the graph fact, answer one more Abel-level question:

1. do these direct parents cluster into a driver family
2. is the pressure mainly price, participation/liquidity, or both
3. does the surrounding graph look more macro, credit, risk-on/risk-off, industry, or cross-asset

Do not abandon the graph merely because the direct parents are unintuitive. First interpret them as transmission channels, especially for large-cap or liquid assets where liquidity, macro, credit, and cross-asset effects can dominate the local structure.

### Main-Answer Label Rule

Before finalizing:

1. shortlist the nodes that actually matter
2. run `extensions.abel.node_description` on that shortlist
3. rewrite the visible answer using company names, industries, products, or roles

Good:

- `audio distribution platforms`
- `subscription-led publishing assets`
- `AI infrastructure names`
- `labor marketplace proxies`

Avoid in the main answer:

- `SPOT.price`
- `ETHUSD.price`
- `NVDA`

### Answer Shapes

- Default to a compact report, using `assets/report-guide.md` as a coverage guide rather than a fixed template.
- Collapse to a shorter answer only when the user explicitly asks for brevity or the question is genuinely trivial.
- Low-stakes comparisons may still be shorter, but they should preserve graph-backed reasoning and any critical web-grounded mechanism.
- High-stakes, comparative, multi-anchor, or non-trivial reads should include a pressure-test section unless no meaningful live intervention surface is available.
- Natural longform prose is acceptable as long as the guide's contract fields are still covered in substance.
- If no live intervention was run, include the cleanest next-step probe so the user can see what `extensions.abel.intervene_time_lag` would test next.


## Install And Authorization

If the user installs this skill, asks to connect Abel, or the workflow is missing an Abel API key, follow `references/setup-guide.md` exactly. Start the OAuth handoff immediately, return `data.authUrl`, wait for the user's confirmation, then poll and persist the resulting key locally.

## References

- Route selection compatibility note: `references/question-routing.md`
- Live-surface discovery and method checks: `references/routes/capability-discovery.md`
- Direct graph route: `references/routes/direct-graph.md`
- Proxy-routed route: `references/routes/proxy-routed.md`
- Grounding and label rendering: `references/grounding-and-labeling.md`
- Unified graph/web planner: `references/orchestration-loop.md`
- Web-grounded mechanism loop: `references/web-grounding.md`
- OAuth install flow and API key reuse: `references/setup-guide.md`
- Probe script commands and reusable examples: `references/probe-usage.md`
- Report coverage guide for fuller write-ups: `assets/report-guide.md`

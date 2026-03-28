# Orchestration Loop

Read this file after route selection. It is the active planner for `direct_graph` and `proxy_routed`.

The route file sets the initial prior. This file decides each next move.

## Core Rule

Graph and web are peer tools, but the planner should be graph-biased. Graph stays the reasoning center, and the usual cadence is one resolved-time observational graph read, then structural graph work, then web only when dated validation is needed.

## One-Line Planner

Before each tool call, state internally or explicitly:

```text
Unknown now: ...
Best next tool: graph | web
Why this tool now: ...
```

## Choose The Next Tool

Choose `graph` when the unknown is:

- current directional pressure on an executable anchor
- path direction
- driver ranking
- neighborhood shape
- bridge-node position
- whether a candidate really belongs in the mechanism

Default to `graph` when in doubt.

Choose `web` when the unknown is:

- event freshness
- catalyst timing
- policy facts
- earnings, adoption, or monetization reality
- whether a graph-backed mechanism is actually live now

Search-first exception:

- for `recently / latest / why now` questions, one baseline web search is allowed before the main graph loop
- for `graph_sparse` archetype questions (passion careers, cultural trends, lifestyle choices), web is the primary tool — graph provides environmental context only, not the core answer. Do 1-2 light graph reads for economic scaffolding, then shift to web for the substantive answer.
- after that, return to graph unless the next unknown is still factual freshness

## Preferred Cadence

The usual cadence is:

- `resolved-time observation -> graph -> graph -> maybe web -> lag pressure test`

Interpret this as:

1. first graph-lane move is observational when an executable anchor exists
2. second move exposes local structure
3. third move refines the strongest mechanism or candidate
4. one web move only when that mechanism now needs dated validation
5. one lag-aware pressure test after the mechanism is coherent enough to stress. Choose `horizon_steps` to match the user's decision window: ~6 for very short-term, ~24 for medium-range default, ~42 for about a week, ~170 for about a month. If the first intervention is inconclusive, step up one tier (6→24→42→170) rather than jumping arbitrarily
6. return to graph only if the search or pressure test changes the active thread

Web should not become the dominant tool unless the user is explicitly asking a freshness-heavy `why now` question.

## Loop

Repeat until stop:

1. define the current unknown
2. pick one candidate, edge, or mechanism only
3. choose the best next tool
4. run one graph or web move
5. decide `move`, `switch`, or `stop`

For most questions, do not choose `web` until you have already done an observational pass plus at least one meaningful structural graph move on the active thread.

## Move / Switch / Stop

`move`

- the candidate is supported enough to become the next anchor
- the mechanism is clear enough to justify one follow-up on the same thread

`switch`

- evidence is weak, noisy, or contradictory
- the candidate is dominated by bridge noise
- the last tool call did not materially reduce uncertainty

`stop`

- another call is unlikely to change the user-facing conclusion
- the same pattern keeps repeating
- remaining uncertainty is honest but not decision-changing

## Low-Signal Fallbacks

- 2 consecutive low-signal candidate checks -> switch candidate
- 3 consecutive low-signal tool calls -> stop and state residual uncertainty
- for graph_sparse archetype: 1 low-signal graph read is enough to confirm sparsity — shift to web, don't keep probing the graph
- `query_node` drifts -> fall back to manual anchors
- observational reads across anchors are flat or unavailable -> let structure break the tie
- repeated bridge nodes that stay microcap or crypto-heavy -> summarize as transmission noise and move on
- **large-cap / liquid asset rule**: if a major equity returns surprising or unintuitive parents, do NOT dismiss as noise. First interpret them as transmission channels — liquidity proxies, macro proxies, sector transmission, or cross-asset effects often dominate the local structure for liquid names. Use one more graph move to classify the transmission type before switching
- **node returns 503/no-data on observe**: Use capillary grafting (see `references/capillary-mapping.md` for the discovery protocol). Do not retry the failed node or fall back to web until capillary search is exhausted.
- if graph is clear but current mechanism is weak -> switch to web
- if web is repetitive but the structure is still unresolved -> switch back to graph
- if you have done only an observational pass and one shallow graph move so far, prefer another graph move before searching

## Candidate Rule

- investigate one candidate at a time
- if a candidate is an executable market node, it is usually worth one observational read
- search one subject at a time
- do not fan out into many equal-priority branches

## Signal Aggregation (before writing)

After the loop ends but before writing the answer, aggregate individual probe results into directional signals:

- Do NOT present each ticker's prediction individually (NVDA +0.13%, MSFT +0.03%, GOOGL -0.12%)
- Instead, aggregate into one signal per dimension: "AI infrastructure investment momentum: positive" or "Big tech hiring appetite: mixed (expanding in AI, contracting elsewhere)"
- For life decisions, the user should never see raw prediction numbers. Translate everything into plain directional language.
- For investment questions, individual ticker data is acceptable but still prefer aggregated signals in the verdict.

Translate each cluster of observations into one plain-language directional signal per dimension.

## Output Rule

The final answer should feel coherent even if the loop alternated many times underneath.

- keep graph as the explanation center
- keep web as dated mechanism validation
- keep pressure tests as compact robustness checks, not detached demos

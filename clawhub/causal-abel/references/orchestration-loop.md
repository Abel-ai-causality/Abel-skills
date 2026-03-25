# Orchestration Loop

Read this file after route selection. It is the active planner for `direct_graph` and `proxy_routed`.

The route file sets the initial prior. This file decides each next move.

## Core Rule

Graph and web are peer tools, but the planner should be graph-biased. Graph stays the reasoning center, and the usual cadence is one observational graph read, then structural graph work, then web only when dated validation is needed.

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
- after that, return to graph unless the next unknown is still factual freshness

## Preferred Cadence

The usual cadence is:

- `observe -> graph -> graph -> maybe web -> intervene`

Interpret this as:

1. first graph-lane move is observational when an executable anchor exists
2. second move exposes local structure
3. third move refines the strongest mechanism or candidate
4. one web move only when that mechanism now needs dated validation
5. one compact intervention after the mechanism is coherent enough to stress
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
- `query_node` drifts -> fall back to manual anchors
- observational reads across anchors are flat or unavailable -> let structure break the tie
- repeated bridge nodes that stay microcap or crypto-heavy -> summarize as transmission noise and move on
- if graph is clear but current mechanism is weak -> switch to web
- if web is repetitive but the structure is still unresolved -> switch back to graph
- if you have done only an observational pass and one shallow graph move so far, prefer another graph move before searching

## Candidate Rule

- investigate one candidate at a time
- if a candidate is an executable market node, it is usually worth one observational read
- search one subject at a time
- do not fan out into many equal-priority branches

## Output Rule

The final answer should feel coherent even if the loop alternated many times underneath.

- keep graph as the explanation center
- keep web as dated mechanism validation
- keep pressure tests as compact robustness checks, not detached demos

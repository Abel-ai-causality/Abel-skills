# Direct Graph Route

Read this file only when the question is already about a graph node, path, neighborhood, or intervention.

## Use This Route For

- what is driving `X`
- why did `X` move
- which nodes matter around `X`
- is there a path from `X` to `Y`
- what happens if `X` changes

## What This Route Sets

This route sets the default first move and the preferred structural fallback.

After that, return to `../orchestration-loop.md` and choose each next move from the current unknown.

## First Move

Pick the first move from the user's question shape:

- direct node with executable market anchor and a current directional question -> `extensions.abel.observe_predict_resolved_time` when available, else `observe.predict`
- driver -> `graph.neighbors(scope=parents)` or `traverse.parents`
- downstream -> `graph.neighbors(scope=children)` or `traverse.children`
- transmission -> `graph.paths`
- ambiguity after one structural pass -> `graph.markov_blanket`

For driver or "why did it move" questions, prefer a quick observational read on the target node before the deeper structural pass when the node is executable.

## Structural Loop

Then use the orchestration loop:

1. If an observational read was taken, use it to decide which structural question matters most.
2. Read the returned structure.
3. State the open causal question.
4. Choose the next best tool: another graph move or a web move.
5. Stop when the user-facing mechanism is already strong enough.

## Pressure Test

- After the mechanism is coherent enough to stress:

- compact stress test -> `intervene.do`
- rollout sensitivity -> `extensions.abel.intervene_time_lag`

For non-trivial direct-node or comparative reads, one compact `intervene.do` pressure test is the default before finalizing. Do not start with a pressure test for a driver question or run it before you can name the mechanism being stressed.

## Web Grounding Rule

Web grounding is required when the answer depends on:

- current catalysts
- earnings or guidance
- policy or regulation
- product or adoption changes
- a real-world mechanism that the graph alone cannot explain

Search the named companies, sectors, or mechanisms from `node_description`, not raw tickers, and then return to the loop.

## Output Rule

- For any non-trivial direct-graph read, render the visible answer as a structured report, not as plain prose.
- Use `../../assets/report-guide.md` to make sure the report covers the right content. Natural longform prose is acceptable if it still covers the same contract fields.
- Main answer uses company names, industries, products, or roles.
- Include the pressure-test result or, if no live intervention was run, the cleanest next-step probe.
- If a repeated bridge node looks like microcap or crypto-heavy transmission noise, summarize it as noise unless external evidence says it matters.

# Web Grounding

Read this file when the current unknown is better answered by external evidence than by another graph move.

Search is a peer tool inside the loop, but not the dominant one. Graph structure stays primary. If web evidence suggests a more intuitive narrative than the graph result, do NOT overwrite the graph answer — state the L2 graph finding first, then label the web evidence as explanation, validation, or unresolved tension. Web narratives are L0; graph observations are L2. L2 takes precedence in the verdict.

## When To Use Web Next

Use web as the next move when:

- the graph already suggests a mechanism, but you need current evidence
- the question is about `latest`, `recently`, or `why now`
- a bridge candidate needs validation
- a company, sector, or asset needs current-state grounding

ClawHub / OpenClaw rule:

- before relying on web grounding, confirm that a web search tool is mounted in the current environment
- if no web search tool is available, tell the user they need to install one before you can do web-grounded validation
- do not pretend that web evidence was checked when the tool is missing

Default bias:

- if you have not yet done at least one or two meaningful graph moves on the active mechanism, go back to graph first
- if you already have a plausible mechanism and the missing piece is dated evidence, use web now

## What To Search

Search one grounded subject at a time:

- a key company from `node_description`
- a sector or industry from `node_description`
- a graph-backed mechanism edge
- a repeated bridge candidate that needs validation

## Pre-Search Frame

Before each search, be able to name:

- `edge or mechanism`
- `why it matters`
- `current-state question`

If you cannot name those, return to the graph first.

## Query Shape

Use company names, products, industries, or mechanisms.

Good (financial):

- `Spotify podcast advertising monetization latest`
- `New York Times digital subscription growth latest`
- `startup software funding hiring 2026`
- `Ethereum ETF flows latest`

Good (life decisions):

- `AI designer job market automation risk 2026`
- `MBA salary premium vs opportunity cost latest data`
- `luxury goods pricing cycle EUR CNY exchange rate trend`
- `GPU 5090 vs 9090 XT release date pricing comparison`
- `cooking vs eating out cost health time tradeoff`
- `San Francisco vs Shanghai housing price forecast 2026`

Bad:

- `Spotify stock price`
- `Ethereum price`
- `graph.neighbors news`
- `should I change jobs` (too vague — search the specific mechanism, not the question)

## What To Extract

After each useful result, keep only:

- `graph_fact`
- `searched_mechanism`
- `state_now`
- `counter-evidence`
- `inference`

## Search Budget (CurioCat-inspired adversarial protocol)

Minimum 4 searches, structured as:
1. **What's happening now** — latest prices, policy changes, dates, events
2. **Supporting evidence** — data that confirms the graph-backed verdict
3. **Contradicting evidence** — actively search for reasons the verdict is WRONG. "Why buying now might be better" if verdict says wait. This is mandatory.
4. **User-perspective data** — what a real buyer/decision-maker would search. Second-hand prices, waitlists, alternative channels, community consensus, real people's experiences.

Up to 6 searches for complex questions. Stop when contradicting search returns nothing new.

## Stop Rules

- stop when contradicting evidence search returns nothing the verdict hasn't already addressed
- stop when search only repeats generic sector commentary

## Return-To-Graph Rules

Go back to the graph when search:

- reveals a new clean node candidate
- reveals a second-order effect worth testing structurally
- contradicts the current causal story

Then return to the orchestration loop and decide the next move explicitly.

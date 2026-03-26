# Web Grounding

Read this file when the current unknown is better answered by external evidence than by another graph move.

Search is a peer tool inside the loop, but not the dominant one. Graph structure stays primary.

Web grounding never replaces a clear graph answer. It only clarifies freshness, mechanism, or realism around that answer.

## When To Use Web Next

Use web as the next move when:

- the graph already suggests a mechanism, but you need current evidence
- the question is about `latest`, `recently`, or `why now`
- a bridge candidate needs validation
- a company, sector, or asset needs current-state grounding

Do not use web next when:

- the user asked a literal driver or parent-membership question
- the graph already answered the direct question and the remaining gap is only that the answer feels unintuitive
- the only reason to search is to find a more familiar narrative than the one the graph surfaced

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

Good:

- `Spotify podcast advertising monetization latest`
- `New York Times digital subscription growth latest`
- `startup software funding hiring 2026`
- `Ethereum ETF flows latest`

Bad:

- `Spotify stock price`
- `Ethereum price`
- `graph.neighbors news`

## What To Extract

After each useful result, keep only:

- `graph_fact`
- `searched_mechanism`
- `state_now`
- `counter-evidence`
- `inference`

If the web result conflicts with the graph-backed answer, keep both instead of letting one erase the other:

- `graph_fact`: what the graph literally says
- `web_state`: what dated external evidence suggests now
- `tension`: whether the interpretation is aligned, challenged, or unresolved

## Stop Rules

- stop after 1 baseline search plus 1-2 focused searches
- stop when search only repeats generic sector commentary
- stop when repeated results do not change the next graph question

## Return-To-Graph Rules

Go back to the graph when search:

- reveals a new clean node candidate
- reveals a second-order effect worth testing structurally
- contradicts the current causal story

Then return to the orchestration loop and decide the next move explicitly.

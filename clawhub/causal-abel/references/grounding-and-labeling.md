# Grounding And Labeling

Read this file whenever you need to map user language into executable Abel nodes or turn nodes back into user-facing prose.

## Grounding Order

1. If the input is already `<ticker>.price` or `<ticker>.volume`, keep it unchanged.
2. Bare equity and ETF tickers default to `.price`.
3. Bare crypto aliases expand to `*USD.price`.
4. Use manual mapping first for obvious company names and familiar proxy anchors.
5. Use `extensions.abel.query_node` for fuzzy names, broad concepts, Chinese phrases, or multilingual labels. **If query_node returns irrelevant results for broad life-decision concepts** (e.g., "tech skills that survive AI" returns random tokens), skip to manual mapping of sector-level proxies and shift to web-primary sooner. Don't waste graph calls on noisy queries.
6. Merge manual recall and `query_node`, then shortlist 2-5 candidates.
7. Run `extensions.abel.node_description` on that shortlist.
8. For life-decision concepts, map to environmental proxies — the graph models economic conditions, not personal outcomes. See `references/capillary-mapping.md` for the discovery protocol.
9. When a proxy node returns 503, use capillary grafting before falling back to web. See `references/capillary-mapping.md`.
10. If there is no honest mapping even at the environmental level and no capillary grafts exist, stop instead of forcing a guessed node.

## Quick Rules

- `.price` means price
- `.volume` means volume or participation
- switch to `.volume` only when the question is truly about activity or liquidity
- prefer `ETHUSD.price`, `SOLUSD.price`, `BTCUSD.price`
- treat `BTCUSD.price` as a weak bridge unless fresh probes show otherwise

## What `node_description` Is For

Use `extensions.abel.node_description` for two jobs:

1. disambiguation on the final shortlist
2. answer rendering before you write the visible response

Do not treat it as a substitute for graph work.

## Main-Answer Label Rule

The user-facing answer should default to:

- company names
- sectors
- industries
- products
- economic roles

Good: company names, sectors, industries, products, economic roles.

**HARD RULE for life decisions:** The verdict layer must contain ZERO tickers. Translate every node into its economic role before writing. Raw prediction numbers become directional language ("positive", "cooling", "expanding").

Avoid in the main answer: raw node IDs, ticker symbols, decimal predictions. Use the `node_description` display name or a plain-language economic role instead.


## Search Query Rule

When you move to web search:

- search the company or industry names from `node_description`
- search the mechanism in plain language
- do not search raw `*.price` node ids

Good:

- `Spotify podcast monetization latest`
- `New York Times digital subscriptions latest`
- `Coinbase Ethereum ETF flows latest`

Bad:

- `Spotify stock price news`
- `Ethereum price why`

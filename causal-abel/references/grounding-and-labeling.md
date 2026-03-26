# Grounding And Labeling

Read this file whenever you need to map user language into executable Abel nodes or turn nodes back into user-facing prose.

## Grounding Order

1. If the input is already `<ticker>_close` or `<ticker>_volume`, keep it unchanged.
2. Bare equity and ETF tickers default to `_close`.
3. Bare crypto aliases expand to `*USD_close`.
4. Use manual mapping first for obvious company names and familiar proxy anchors.
5. Use `extensions.abel.query_node` for fuzzy names, broad concepts, Chinese phrases, or multilingual labels.
6. Merge manual recall and `query_node`, then shortlist 2-5 candidates.
7. Run `extensions.abel.node_description` on that shortlist.
8. If there is no honest mapping, stop instead of forcing a guessed node.

## Quick Rules

- `_close` means price
- `_volume` means volume or participation
- switch to `_volume` only when the question is truly about activity or liquidity
- prefer `ETHUSD_close`, `SOLUSD_close`, `BTCUSD_close`
- treat `BTCUSD_close` as a weak bridge unless fresh probes show otherwise

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

Good examples:

- `The New York Times and other subscription publishers`
- `audio distribution platforms`
- `enterprise software names with recurring revenue`
- `labor marketplace proxies`

Avoid in the main answer:

- `SPOT_close`
- `ETHUSD_close`
- `NVDA`


## Search Query Rule

When you move to web search:

- search the company or industry names from `node_description`
- search the mechanism in plain language
- do not search raw `*_close` node ids

Good:

- `Spotify podcast monetization latest`
- `New York Times digital subscriptions latest`
- `Coinbase Ethereum ETF flows latest`

Bad:

- `SPOT_close news`
- `ETHUSD_close why`

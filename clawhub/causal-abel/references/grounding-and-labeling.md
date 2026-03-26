# Grounding And Labeling

Read this file whenever you need to map user language into executable Abel nodes or turn nodes back into user-facing prose.

## Grounding Order

1. If the input is already `<ticker>.price` or `<ticker>.volume`, keep it unchanged.
2. Bare equity and ETF tickers default to `.price`.
3. Bare crypto aliases expand to `*USD.price`.
4. Use manual mapping first for obvious company names and familiar proxy anchors.
5. Use `extensions.abel.query_node` for fuzzy names, broad concepts, Chinese phrases, or multilingual labels.
6. Merge manual recall and `query_node`, then shortlist 2-5 candidates.
7. Run `extensions.abel.node_description` on that shortlist.
8. If there is no honest mapping, stop instead of forcing a guessed node.

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

Good examples:

- `The New York Times and other subscription publishers`
- `audio distribution platforms`
- `enterprise software names with recurring revenue`
- `labor marketplace proxies`

Avoid in the main answer:

- `SPOT.price`
- `ETHUSD.price`
- `NVDA`


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

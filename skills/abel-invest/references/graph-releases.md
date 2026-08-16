# Graph Release Selection

Abel Invest uses one Abel-edge provider for both graph generations. V3 and V4
are release choices, not separate plugins.

## V3 Default

Omit `--graph-release` to retain the existing V3 discovery, symbol feed,
adjusted market-data, and `asof_series("close"|"volume")` behavior. This is the
compatibility default.

## V4 Opt-In

Create a reviewed JSON file using the Edge contract:

```json
{
  "contract": "abel-edge.graph-release/v1",
  "provider": "abel",
  "graph_ref": {
    "graph_id": "abel-main",
    "graph_version": "CausalNodeV4"
  }
}
```

If the release has an immutable release ID or receipt, include it as required
by the Edge contract. Start the session with:

```bash
<command_prefix> init-session --ticker <TICKER> --exp-id <exp-id> \
  --graph-release path/to/v4-graph-release.json
```

The session freezes the configuration in `graph_release.json`. Discovery and
frontier expansion pass it only to Edge. Abel Invest must not call CAP,
`day_bar`, graph-package storage, or provider-internal APIs.

## Typed Drivers

Edge discovery v2 supplies a `driver_ref` for every V4 driver:

- `kind=symbol`: adjusted market history. Preserve `symbol` and `field`; Edge
  owns the data route.
- `kind=canonical_node`: an exact case-sensitive node ID. Preserve the complete
  reference and use the Edge-generated point-in-time series spec.

Canonical-node preparation emits a `point_in_time_series` feed with field
`value`. Runtime strategy code reads that feed through
`asof_series("value")`. It must not convert the ID to a ticker, uppercase it,
guess a source, forward-fill missing graph observations, or call CAP directly.

## Gate

V4 is usable only when Edge doctor confirms CAP returns scalar node-series
rows: exact `node_id`, `mode=node_series`, a finite `value`, and one UTC
visibility `timestamp` per row. Raw record collections are diagnostic data, not
a canonical backtest feed, and must fail closed.

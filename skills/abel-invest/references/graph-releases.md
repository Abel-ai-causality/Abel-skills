# Graph Release Selection

Abel Invest uses one Abel-edge provider for both graph generations. V3 and V4
are release choices, not separate plugins.

## V3 Default

Omit `--graph-release` to retain the existing V3 discovery, symbol feed,
adjusted market-data, and `asof_series("close"|"volume")` behavior. This is the
compatibility default.

## V4 Opt-In

V4 requires the Abel-edge release containing the typed graph-release and
`target_ref` contracts. Merge and publish the provider change before releasing
this consumer; capability absence fails with an installation error instead of
falling back to V3 parsing.

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

Abel Invest classifies this contract into exactly three states:

- no release or a validated `CausalNodeV3` release: legacy V3 behavior;
- a validated `CausalNodeV4` release: typed V4 behavior;
- an invalid or unknown release: fail closed.

Release provenance does not by itself enable V4 behavior. An explicit V3 pin
remains frontier, dependency, and data-manifest schema v1. Its release metadata
is retained for later frontier calls, but its symbol normalization and bars
behavior stay unchanged.

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

Edge also supplies a typed `target_ref`. Its `node_id` is the exact CAP query
target, and `ticker`, `target_asset`, and `target_node` are checked as flat
projections of that descriptor. Abel Invest never fills, reparses, or repairs
missing V4 target identity. A conflict fails session creation. Session targets
remain symbol targets; canonical nodes are supported as exact drivers and
frontier-expansion anchors.

Both symbol and canonical V4 node IDs are preserved byte-for-byte. V4 chooses
dependency and data-manifest schema v2 from the validated graph version, so a
market-only V4 branch is still v2. Each selected symbol driver uses bars and
each canonical driver uses its prepared point-in-time scalar series.

The requested, frozen, returned, dependency, and manifest graph releases must
normalize to the same Edge configuration SHA-256. Missing provenance, digest
drift, or a different returned release fails closed.

## Gate

V4 is usable only when Edge doctor confirms CAP returns scalar node-series
rows: exact `node_id`, `mode=node_series`, a finite `value`, and one UTC
visibility `timestamp` per row. Raw record collections are diagnostic data, not
a canonical backtest feed, and must fail closed.

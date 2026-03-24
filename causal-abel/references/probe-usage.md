# Probe Usage

Use this file for `cap_probe.py` details and reusable command patterns after the routing decision is already clear.

## Authorization First

- Do not run the bundled probe against live Abel APIs until an Abel user API key is available in session state, `--api-key`, or `.env.skills`.
- If the key is missing, start the OAuth handoff from `setup-guide.md` first and persist the resulting key before probing.
- By default, `cap_probe.py` reads `<skill-root>/.env.skills`, so treat it as an authorized probe, not an anonymous public probe.

## Bundled Script

Prefer the bundled probe script over ad hoc payload construction.

Primary script:

- `scripts/cap_probe.py`

Deterministic subcommands:

- `capabilities`
- `normalize-node`
- `methods`
- `observe`
- `neighbors`
- `paths`
- `markov-blanket`
- `intervene-do`
- `traverse-parents`
- `traverse-children`
- `validate-connectivity`
- `abel-markov-blanket`
- `counterfactual-preview`
- `intervene-time-lag`
- `verb` for arbitrary CAP verbs
- `route` for arbitrary Abel route aliases

## Common Direct Calls

Run these from the skill root:

```bash
BASE_URL="https://cap.abel.ai"

python scripts/cap_probe.py --base-url "$BASE_URL" capabilities
python scripts/cap_probe.py normalize-node NVDA
python scripts/cap_probe.py normalize-node NVDA_volume
python scripts/cap_probe.py --base-url "$BASE_URL" methods
python scripts/cap_probe.py --base-url "$BASE_URL" methods observe.predict traverse.parents
python scripts/cap_probe.py --base-url "$BASE_URL" methods observe.predict --detail full --include-examples
python scripts/cap_probe.py --base-url "$BASE_URL" observe NVDA_close
python scripts/cap_probe.py --base-url "$BASE_URL" neighbors NVDA_close --scope children --max-neighbors 5
python scripts/cap_probe.py --base-url "$BASE_URL" paths NVDA_close AMD_close --max-paths 3
python scripts/cap_probe.py --base-url "$BASE_URL" markov-blanket NVDA_close --max-neighbors 10
python scripts/cap_probe.py --base-url "$BASE_URL" intervene-do NVDA_close 0.05 --outcome-node AMD_close
python scripts/cap_probe.py --base-url "$BASE_URL" validate-connectivity NVDA_close AMD_close SOXX_close
python scripts/cap_probe.py --base-url "$BASE_URL" intervene-time-lag NVDA_close 0.05 --outcome-node AMD_close --horizon-steps 24 --model linear
```

Proxy routing still uses the same script. The difference is which anchors you choose and how you compare them.

Pressure-test rule:

- Treat `intervene-do`, `intervene-time-lag`, and `counterfactual-preview` as pressure-test surfaces.
- Run them after the graph and search loop has already exposed the key mechanism.
- Prefer one strong pressure test over many weak ones.
- If a live pressure test would be low-signal, give the user 2-3 concrete next-step probes instead of forcing one.

Short-term trend rule:

- `observe.predict` is a lightweight observational trend / pressure read for one node.
- For evolving server-specific predictive surfaces, check `meta.methods` first instead of assuming the local wrapper is current.
- Prefer `extensions.abel.observe_predict_resolved_time` when `meta.methods` says it exists because it returns the resolved target timestamp alongside the same prediction value and drivers.
- Call newly added or unstable extension verbs through the generic `verb` path.
- In proxy-routed comparisons, run this on the main 2-5 anchor tickers once the anchor set is stable.
- Use the sign and relative magnitude as a short-term pressure comparison.
- Treat returned drivers as noisy hints for follow-up, not as trusted narrative anchors.

Normalization rule:

- `normalize-node` is the safest first step when a prompt gives a bare ticker and you want deterministic probe input.
- Equity and ETF tickers default to `_close`.
- `_close` means close price. `_volume` means close volume.
- Crypto probes should use `*USD_close` or `*USD_volume`, for example `ETHUSD_close`, `SOLUSD_close`, or `BTCUSD_volume`.
- The bundled normalizer rewrites common bare crypto aliases such as `BTC`, `ETH`, `SOL`, `XRP`, `DOGE`, `ADA`, and `AVAX` into `*USD_<suffix>`.
- Use `--default-suffix volume` only when the question is genuinely about volume or participation.
- Free-form phrases such as `Spotify` or `music streaming` are not normalized automatically; map them to a ticker first.
- Recent validation: `BTCUSD_close` currently behaves like an isolated node on the public graph.
  - `graph.neighbors(scope=parents)` -> empty
  - `graph.neighbors(scope=children)` -> empty
  - sampled `graph.paths` checks to common anchors -> disconnected
  - Practical rule: do not spend time trying to use `BTCUSD_close` as a bridge node unless the graph behavior changes.

For capability discovery, avoid redundant full dumps:

- Use `capabilities` to inventory the mounted surface.
- Use `methods <verb...>` when you need method metadata for a small set of verbs.
- Prefer server-side filtering through `params.verbs` over fetching every method and trimming it later with `jq`.

## Generic Fallbacks

```bash
python scripts/cap_probe.py --base-url "$BASE_URL" verb extensions.abel.validate_connectivity --params-json '{"variables":["NVDA_close","AMD_close","SOXX_close"]}'
python scripts/cap_probe.py --base-url "$BASE_URL" route extensions/abel/counterfactual_preview --params-json '{"intervene_node":"NVDA_close","intervene_time":"2024-01-01T00:00:00Z","observe_node":"AMD_close","observe_time":"2024-01-02T00:00:00Z","intervene_new_value":0.05}'
```

For narrower output, use `--pick-fields` and `--compact`.

Examples:

```bash
python scripts/cap_probe.py methods observe.predict traverse.parents --pick-fields result.methods --compact
python scripts/cap_probe.py methods observe.predict --pick-fields result.methods.0.arguments,result.methods.0.result_fields
python scripts/cap_probe.py methods extensions.abel.observe_predict_resolved_time --detail full
python scripts/cap_probe.py verb extensions.abel.observe_predict_resolved_time --params-json '{"target_node":"SPOT_close"}' --pick-fields result.resolved_target_time,result.prediction,result.drivers --compact
```

## Validation

Probe the live surface first:

```bash
python scripts/cap_probe.py capabilities
python scripts/cap_probe.py methods observe.predict
python scripts/cap_probe.py observe NVDA_close
python scripts/cap_probe.py paths NVDA_close AMD_close --max-paths 3
```

For implementation changes beyond probing, verify the affected routing, auth, and command examples directly in the tracked skill docs and scripts.

## Bridge-Node Triage

When a bridge node keeps reappearing across path checks, inspect its neighborhood before you build a story around it.

- Repeated bridge nodes can still be transmission noise.
- In recent proxy-routing probes, `SIM_close` and `MOOOUSD_close` appeared repeatedly across media/content anchor pairs.
- Their parent/child neighborhoods were still dominated by microcap or crypto-heavy names, which is a strong sign that they are bridge noise, not user-facing narrative anchors.
- Practical rule:
  - repeated bridge + semantically rich neighborhood -> inspect further
  - repeated bridge + microcap/crypto soup neighborhood -> summarize as transmission noise and move on

## Endpoint Notes

- The current public CAP surface answers on `https://cap.abel.ai/cap`.
- `https://cap-sit.abel.ai/cap` is the SIT variant when you need staging.
- The probe accepts base URLs such as `https://cap.abel.ai` and resolves them to `/cap`.
- `https://api.abel.ai/echo/` is used for OAuth and business API flows in `setup-guide.md`; it is not the default CAP probe base.
- If `.env.skills` does not yet contain `ABEL_API_KEY`, pause here and complete the OAuth handoff before using these examples.

## See Also

- `../SKILL.md` for the short agent-facing framework
- `question-routing.md` for choosing direct versus proxy-routed analysis and picking verbs
- `../assets/report-template.md` for presenting findings without centering command details

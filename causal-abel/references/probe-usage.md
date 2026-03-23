# Probe Usage

Use this file for `cap_probe.py` details and reusable command patterns after the routing decision is already clear.

## Authorization First

- Do not run the bundled probe against live Abel APIs until an Abel user API key is available in session state, `--api-key`, or `.env.skills`.
- If the key is missing, start the OAuth handoff from `setup-guide.md` first and persist the resulting key before probing.
- `cap_probe.py` loads `causal-abel/.env.skills` by default when run from the repo root and should be treated as an authorized probe, not an anonymous public probe.

## Bundled Script

Prefer the bundled probe script over ad hoc payload construction.

Primary script:
- From the repo root: `causal-abel/scripts/cap_probe.py`
- From inside the skill directory: `scripts/cap_probe.py`

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

```bash
BASE_URL="https://cap.abel.ai"

python causal-abel/scripts/cap_probe.py --base-url "$BASE_URL" capabilities
python causal-abel/scripts/cap_probe.py normalize-node NVDA
python causal-abel/scripts/cap_probe.py normalize-node NVDA_volume
python causal-abel/scripts/cap_probe.py --base-url "$BASE_URL" methods
python causal-abel/scripts/cap_probe.py --base-url "$BASE_URL" methods observe.predict traverse.parents
python causal-abel/scripts/cap_probe.py --base-url "$BASE_URL" methods observe.predict --detail full --include-examples
python causal-abel/scripts/cap_probe.py --base-url "$BASE_URL" observe NVDA_close
python causal-abel/scripts/cap_probe.py --base-url "$BASE_URL" neighbors NVDA_close --scope children --max-neighbors 5
python causal-abel/scripts/cap_probe.py --base-url "$BASE_URL" paths NVDA_close AMD_close --max-paths 3
python causal-abel/scripts/cap_probe.py --base-url "$BASE_URL" markov-blanket NVDA_close --max-neighbors 10
python causal-abel/scripts/cap_probe.py --base-url "$BASE_URL" intervene-do NVDA_close 0.05 --outcome-node AMD_close
python causal-abel/scripts/cap_probe.py --base-url "$BASE_URL" validate-connectivity NVDA_close AMD_close SOXX_close
python causal-abel/scripts/cap_probe.py --base-url "$BASE_URL" intervene-time-lag NVDA_close 0.05 --outcome-node AMD_close --horizon-steps 24 --model linear
```

Proxy routing still uses the same script. The difference is which anchors you choose and how you compare them.

Normalization rule:

- `normalize-node` is the safest first step when a prompt gives a bare ticker and you want deterministic probe input.
- Bare tickers default to `_close`.
- Use `--default-suffix volume` only when the question is genuinely about volume or participation.
- Free-form phrases such as `Spotify` or `music streaming` are not normalized automatically; map them to a ticker first.

For capability discovery, avoid redundant full dumps:

- Use `capabilities` to inventory the mounted surface.
- Use `methods <verb...>` when you need method metadata for a small set of verbs.
- Prefer server-side filtering through `params.verbs` over fetching every method and trimming it later with `jq`.

## Generic Fallbacks

```bash
python causal-abel/scripts/cap_probe.py --base-url "$BASE_URL" verb extensions.abel.validate_connectivity --params-json '{"variables":["NVDA_close","AMD_close","SOXX_close"]}'
python causal-abel/scripts/cap_probe.py --base-url "$BASE_URL" route extensions/abel/counterfactual_preview --params-json '{"intervene_node":"NVDA_close","intervene_time":"2024-01-01T00:00:00Z","observe_node":"AMD_close","observe_time":"2024-01-02T00:00:00Z","intervene_new_value":0.05}'
```

For narrower output, use `--pick-fields` and `--compact`.

Examples:

```bash
python causal-abel/scripts/cap_probe.py methods observe.predict traverse.parents --pick-fields result.methods --compact
python causal-abel/scripts/cap_probe.py methods observe.predict --pick-fields result.methods.0.arguments,result.methods.0.result_fields
```

## Validation

Probe the live surface first:

```bash
python causal-abel/scripts/cap_probe.py capabilities
python causal-abel/scripts/cap_probe.py methods observe.predict
python causal-abel/scripts/cap_probe.py observe NVDA_close
python causal-abel/scripts/cap_probe.py paths NVDA_close AMD_close --max-paths 3
```

For implementation changes beyond probing, verify the affected routing, auth, and command examples directly in the tracked skill docs and scripts.

Endpoint note:

- The current public CAP surface answers on `https://cap.abel.ai/cap`.
- `https://cap-sit.abel.ai/cap` is the SIT variant when you need staging.
- The probe accepts base URLs such as `https://cap.abel.ai` and resolves them to `/cap`.
- `https://api.abel.ai/echo/` is used for OAuth and business API flows in `setup-guide.md`; it is not the default CAP probe base.
- If `.env.skills` does not yet contain `ABEL_API_KEY`, pause here and complete the OAuth handoff before using these examples.

## See Also

- `../SKILL.md` for the short agent-facing framework
- `question-routing.md` for choosing direct versus proxy-routed analysis and picking verbs
- `../assets/report-template.md` for presenting findings without centering command details

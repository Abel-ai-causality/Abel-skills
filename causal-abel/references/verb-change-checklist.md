# Verb Change Checklist

Use this file when adding or materially changing a CAP verb in the Abel wrapper.

## Decide The Layer

- Protocol-generic request/response shape: `cap_protocol/core/contracts.py`
- Abel-only extension contract: `abel_cap_server/cap/contracts/extensions.py`
- Abel-side compatibility exports: `abel_cap_server/cap/contracts/__init__.py`

## Edit Sequence

1. Add or update tests in `tests/test_cap_graph.py` and any smaller focused test file if present.
2. Add/update request and response models.
3. Add/update adapter logic under `abel_cap_server/cap/adapters/`.
4. Register the verb in `abel_cap_server/cap/catalog.py`.
5. Expose a matching service method in `abel_cap_server/cap/service.py`.
6. Add/update gateway client methods in `abel_cap_server/clients/abel_gateway_client.py`.
7. Verify `POST /api/v1/cap` dispatch still works through the shared registry.
8. Re-check capability-card output and extension notes.

## Gateway Mapping Rules

- Keep Abel HTTP paths centralized in `abel_cap_server/clients/abel_gateway_client.py`.
- Read base URL from `Settings.cap_upstream_base_url`.
- Use `Authorization: Bearer {token}`.
- Forward caller auth header upstream when provided; otherwise fall back to `CAP_GATEWAY_API_KEY`.

Current mapping:
- `observe.predict` -> `POST /v1/predict`
- `intervene.do` -> `POST /v1/intervene`
- `graph.neighbors`, `graph.markov_blanket`, `traverse.*` -> `POST /v1/explain`
- `graph.paths` -> `GET /v1/schema/paths`
- `extensions.abel.validate_connectivity` -> `POST /v1/validate`
- `extensions.abel.counterfactual_preview` -> `POST /v1/counterfactual`
- `extensions.abel.intervene_time_lag` -> `POST /v1/intervene`

## Capability Card Checks

- `/.well-known/cap.json` and `meta.capabilities` must match semantically.
- Supported verbs should come from registry metadata.
- Update extension namespace notes only when public behavior actually changed.
- Keep conformance claims honest.

## Disclosure Checks

- Hidden fields must stay stripped from public responses.
- Do not expose raw internal stats or confidence internals unless the public contract explicitly allows them.
- Re-run tests that assert hidden-field removal and summary-safe output.

## See Also

- `../SKILL.md` for the short agent-facing framework
- `repo-map.md` for the files that own each public surface
- `capability-layers.md` for deciding whether a behavior belongs in CAP core or `extensions.abel.*`

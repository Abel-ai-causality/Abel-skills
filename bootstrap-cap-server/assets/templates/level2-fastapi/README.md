# __SERVER_TITLE__

Minimal CAP Level 2 scaffold generated from the `bootstrap-cap-server` skill.

## Install

```bash
uv sync --extra dev
```

## Run

```bash
uv run uvicorn __PACKAGE_NAME__.app:app --reload
```

## Test

```bash
uv run pytest
```

## Example Requests

```bash
curl -s http://127.0.0.1:8000/cap \
  -X POST \
  -H 'content-type: application/json' \
  -d '{
    "cap_version": "0.2.2",
    "request_id": "req-meta",
    "verb": "meta.methods",
    "params": {"detail": "compact"}
  }'
```

```bash
curl -s http://127.0.0.1:8000/cap \
  -X POST \
  -H 'content-type: application/json' \
  -d '{
    "cap_version": "0.2.2",
    "request_id": "req-neighbors",
    "verb": "graph.neighbors",
    "params": {"node_id": "__SAMPLE_NEIGHBOR_NODE_ID__", "scope": "__SAMPLE_NEIGHBOR_SCOPE__"}
  }'
```

```bash
curl -s http://127.0.0.1:8000/cap \
  -X POST \
  -H 'content-type: application/json' \
  -d '{
    "cap_version": "0.2.2",
    "request_id": "req-paths",
    "verb": "graph.paths",
    "params": {
      "source_node_id": "__SAMPLE_PATH_SOURCE_NODE_ID__",
      "target_node_id": "__SAMPLE_PATH_TARGET_NODE_ID__",
      "max_paths": 3
    }
  }'
```

## Notes

- This scaffold includes `graph.paths`.
- Start by editing `__PACKAGE_NAME__/adapters/graph_adapter.py` and `__PACKAGE_NAME__/graph_metadata.py`.
- Replace the example graph adapter in `__PACKAGE_NAME__/adapters/graph_adapter.py` with the real graph or causal runtime.
- Wire registry behavior in `__PACKAGE_NAME__/handlers/` and capability disclosure in `__PACKAGE_NAME__/capability.py`.
- Update graph metadata in `__PACKAGE_NAME__/graph_metadata.py`.
- Re-check that the capability card still matches the mounted verbs and the runtime's real semantics.
- The scaffold targets a single deployed graph by default and does not require `context.graph_ref`.
- Use `graph_version` in provenance and capability metadata. Add `context.graph_ref` later only if a specific deployment needs explicit version pinning.
__AUTH_NOTES__
__PREDICTOR_NOTES__
__INTERVENTION_NOTES__

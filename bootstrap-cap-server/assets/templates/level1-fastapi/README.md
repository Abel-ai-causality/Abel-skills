# __SERVER_TITLE__

Minimal CAP Level 1 scaffold generated from the `bootstrap-cap-server` skill.

## Install

```bash
uv sync --extra dev
```

## Run

```bash
uv run uvicorn __PACKAGE_NAME__.app:app --reload
```

Then inspect:

- `http://127.0.0.1:8000/.well-known/cap.json`
- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`

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
    "params": {"node_id": "revenue", "scope": "parents"}
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
      "source_node_id": "marketing_spend",
      "target_node_id": "revenue",
      "max_paths": 3
    }
  }'
```

## Notes

- This scaffold exposes a small honest CAP surface.
- Start by editing `__PACKAGE_NAME__/adapters/graph_adapter.py` and `__PACKAGE_NAME__/graph_metadata.py`.
- Replace the example graph adapter in `__PACKAGE_NAME__/adapters/graph_adapter.py` with the real graph or runtime adapter.
- Wire registry behavior in `__PACKAGE_NAME__/handlers/` and capability disclosure in `__PACKAGE_NAME__/capability.py`.
- Update graph metadata in `__PACKAGE_NAME__/graph_metadata.py`.
- Keep the mounted verbs and the capability card aligned.
- The scaffold targets a single deployed graph by default and does not require `context.graph_ref`.
- Use `graph_version` in provenance and capability metadata. Add `context.graph_ref` later only if a specific deployment needs explicit version pinning.
__AUTH_NOTES__
__PREDICTOR_NOTES__
__INTERVENTION_NOTES__
[[IF_INCLUDE_PATHS]]
- The scaffold also mounts `graph.paths`, even though Level 1 does not require it.
[[END_IF_INCLUDE_PATHS]]

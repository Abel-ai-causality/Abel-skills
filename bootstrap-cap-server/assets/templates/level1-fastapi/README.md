# __SERVER_TITLE__

Minimal CAP Level 1 scaffold generated from the `bootstrap-cap-server` skill.

## Install

```bash
pip install -e ".[dev]"
```

## Run

```bash
uvicorn __PACKAGE_NAME__.app:app --reload
```

Then inspect:

- `http://127.0.0.1:8000/.well-known/cap.json`
- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`

## Test

```bash
pytest
```

## Notes

- This scaffold exposes a small honest CAP surface.
- Start by editing `__PACKAGE_NAME__/adapters/graph_adapter.py` and `__PACKAGE_NAME__/graph_metadata.py`.
- Replace the example graph adapter in `__PACKAGE_NAME__/adapters/graph_adapter.py` with the real graph or runtime adapter.
- Wire registry behavior in `__PACKAGE_NAME__/handlers/` and capability disclosure in `__PACKAGE_NAME__/capability.py`.
- Update graph metadata in `__PACKAGE_NAME__/graph_metadata.py`.
- Keep the mounted verbs and the capability card aligned.
__AUTH_NOTES__
__GRAPH_REF_NOTES__
__PREDICTOR_NOTES__
__INTERVENTION_NOTES__
[[IF_INCLUDE_PATHS]]
- The scaffold also mounts `graph.paths`, even though Level 1 does not require it.
[[END_IF_INCLUDE_PATHS]]

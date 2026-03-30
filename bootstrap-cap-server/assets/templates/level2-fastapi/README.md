# __SERVER_TITLE__

Minimal CAP Level 2 scaffold generated from the `bootstrap-cap-server` skill.

## Install

```bash
pip install -e ".[dev]"
```

## Run

```bash
uvicorn __PACKAGE_NAME__.app:app --reload
```

## Test

```bash
pytest
```

## Notes

- This scaffold includes `graph.paths`.
- Start by editing `__PACKAGE_NAME__/adapters/graph_adapter.py` and `__PACKAGE_NAME__/graph_metadata.py`.
- Replace the example graph adapter in `__PACKAGE_NAME__/adapters/graph_adapter.py` with the real graph or causal runtime.
- Wire registry behavior in `__PACKAGE_NAME__/handlers/` and capability disclosure in `__PACKAGE_NAME__/capability.py`.
- Update graph metadata in `__PACKAGE_NAME__/graph_metadata.py`.
- Re-check that the capability card still matches the mounted verbs and the runtime's real semantics.
__AUTH_NOTES__
__GRAPH_REF_NOTES__
__PREDICTOR_NOTES__
__INTERVENTION_NOTES__

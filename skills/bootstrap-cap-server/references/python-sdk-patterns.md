# Python SDK Patterns

Use the published package, not local source-tree imports. Generated docs should assume a `uv` workflow even though runtime shape may vary.

## Install

```bash
uv add "cap-protocol[server]"
```

## Core Imports

Typical server scaffold imports look like:

```python
from fastapi import FastAPI, Request

from cap.core import (
    CAPABILITY_CARD_SCHEMA_URL,
    CapabilityAuthentication,
    CapabilityCard,
    CapabilityGraphMetadata,
    CapabilityProvider,
    CapabilitySupportedVerbs,
)
from cap.server import (
    CAPHandlerSuccessSpec,
    CAPProvenanceContext,
    CAPProvenanceHint,
    CAPVerbRegistry,
    META_CAPABILITIES_CONTRACT,
    META_METHODS_CONTRACT,
    GRAPH_NEIGHBORS_CONTRACT,
    GRAPH_MARKOV_BLANKET_CONTRACT,
    GRAPH_PATHS_CONTRACT,
    OBSERVE_PREDICT_CONTRACT,
    INTERVENE_DO_CONTRACT,
    build_fastapi_cap_dispatcher,
    register_cap_exception_handlers,
)
```

Adjust the imports to match the verbs you actually mount.

## Server Shape

The public server shape should stay simple:

- `GET /.well-known/cap.json`
- `POST /cap`
- one `CAPVerbRegistry`
- one capability-card builder
- one provenance context provider

For this bootstrap skill, keep auth out of the default scaffold. Start with `authentication.type = "none"` and let later coding work add gateway or API-key logic if the user actually needs it.

## Registry Pattern

Register verbs explicitly. Do not hide mounted verbs behind dynamic magic if that makes capability disclosure harder to trust.

Keep:

- discovery verbs always explicit
- optional verbs mounted only when the runtime supports them
- capability-card verb lists derived from the mounted registry

## Capability Card Pattern

Build:

- `supported_verbs.core` from `registry.verbs_for_surface("core")`
- `supported_verbs.convenience` from `registry.verbs_for_surface("convenience")`

Use the active mounted surface to keep `meta.capabilities` and `meta.methods` aligned.

## `graph_ref`

`context.graph_ref` is an optional shared request-context field in CAP, not a default bootstrap requirement.

For the default bootstrap case:

- omit `graph_ref` from examples
- keep the scaffold focused on one deployed graph
- disclose `graph_version` through provenance and capability metadata

Only add `graph_ref` handling when a specific deployment genuinely needs explicit graph selection or version pinning. Do not invent selector complexity just because the schema allows it.

## Output Bias

When bootstrapping, prefer a small runnable project over a maximal code dump. A good first output usually includes:

- app entrypoint
- runtime adapter interface
- capability-card builder
- tests
- one example request

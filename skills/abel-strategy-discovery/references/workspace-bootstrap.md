# Workspace Bootstrap

`abel-strategy-discovery` is workspace-first.

- Install should prepare the default workspace base.
- Runtime should reuse an existing workspace root before creating a new one.
- The strategy runtime owns the order of branch preparation and legality checks.
- Auth should reuse existing Abel auth first and fall back to `abel-auth` only when needed.

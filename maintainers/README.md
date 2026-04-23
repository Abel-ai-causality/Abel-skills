# Maintainer Sources

`maintainers/skills/` is the maintainer-owned source tree for the full Abel
skills collection.

`skills/` is the rendered public install tree.

Ask-specific rendering helpers still live under `maintainers/abel-ask/`, but
they should read from `maintainers/skills/abel-ask` and render into
`skills/abel-ask` or `dist/`.

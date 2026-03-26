# Capability Discovery Module

Read this file as the live-surface module for `causal-abel`. This is not a peer usage route. It is the required way to verify what the live server actually supports.

## Use This Module For

- what verbs are live right now
- whether an extension verb is mounted
- what params a method accepts
- how the current server differs from a local wrapper
- how to verify capabilities before using the other routes

## Default Sequence

1. run `meta.capabilities` for inventory
2. run `meta.methods` only for the verbs actually under discussion
3. use the generic `verb` path for newer extension surfaces
4. avoid whole-surface dumps unless the user explicitly asks for them

## Rules

- treat the live server as truth
- do not infer mounted verbs from old docs or wrappers
- prefer a small targeted list of verbs over dumping every method
- summarize in user-facing language first, then list exact verb names if needed

## Output Rule

- lead with what is available or not available
- use concrete verb names and argument highlights
- keep protocol and schema detail scoped to what the user asked

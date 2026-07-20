# WP2-UP-v2 qualification

This campaign supersedes `WP2-UPQ-v1` as the downstream prerequisite.  The v1
model was mathematically sound, but its lock omitted consumed upstream inputs
and its collision gate established only pointwise finiteness.  V2 adds a
JAX-autodifferentiated reference path, full consumed-input locking and hash
checks, an on-shell collision limit, and integration through the selected
binary collision in fictitious time.

The external split remains a compositional conformance split whose source
states predate this implementation.  It is not described as an unseen
scientific holdout.

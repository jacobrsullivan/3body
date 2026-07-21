# WP3-MULTI-CAND-v2

This campaign searches the qualified three-body model in the separately locked
285-column physical-quotient Reynolds library. It reuses the exact v1
development/calibration corpus and leaves the 24-case publication reserve
sealed unless a later candidate-specific qualification is independently
specified and locked.

The execution sequence is:

```bash
./validation-external/wp3-multi-candidate-v2/run_search.sh test
./validation-external/wp3-multi-candidate-v2/run_search.sh freeze
./validation-external/wp3-multi-candidate-v2/run_search.sh execute
./validation-external/wp3-multi-candidate-v2/run_search.sh finalize
```

Each state-changing stage is one-shot. Freeze requires a clean worktree;
execute verifies the frozen lock and writes raw evidence with interpretation
prohibited; the publication gate is evaluated before final reporting.

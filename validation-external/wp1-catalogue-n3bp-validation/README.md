# WP1-CAT-N3BP-v1

This campaign generates a bounded 169-member planar Newtonian three-body
catalogue on a frozen two-dimensional mass grid. It begins from one disclosed
published equal-mass root, then performs native correction and continuation
without loading external evaluation rows. Exact-mass SJTU rows enter only
after the native candidate payload is frozen.

A final `PASS` qualifies this one family patch, not independent root discovery,
spatial families, completeness, or a general N3BP catalogue.

The enforced order is:

1. Establish and commit a source-free repository state: the numerical selected
   SJTU patch, qualification corpus, and every split result/evaluation must be
   absent. `sources/manifest.json` remains as non-numerical provenance metadata.
2. `./run_qualification.sh generate`. The command fails if any numerical
   external evidence is present.
3. Commit the native payload, then `./run_qualification.sh freeze-candidate`.
   Candidate freeze requires the same source-free state and a clean worktree.
4. Commit the candidate lock. Restore the exact manifest-pinned SJTU patch,
   then run `./run_qualification.sh build` to derive the deterministic corpus.
5. `./run_qualification.sh prepare`. This first executes the focused WP1 tests
   and writes `reports/wp1_cat_n3bp_v1_focused_tests.json`, then evaluates
   development and calibration.
6. Commit all prequalification evidence, including the focused-test receipt,
   then `./run_qualification.sh freeze`. Freeze verifies the receipt's command,
   tested-code/input hashes, specification hash, integrity hash, PASS status,
   and full runtime fingerprint before including it in lock scope.
7. Commit the full lock, then execute `holdout` exactly once. Holdout execution
   and evaluation require exact equality with every full-lock runtime field and
   refuse existing holdout outputs.
8. `./run_qualification.sh finalize`.

To repeat a pre-freeze preparation, explicitly remove the old focused-test
receipt and split outputs first. A holdout output is not a rerunnable cache.

`WP1_CAT_WORKERS` controls row/split process parallelism and does not alter
continuation lineage or sorted output ordering.

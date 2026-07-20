# Candidate-specific sealed qualification gate

This gate consumes the locked `WP3-UP-CAND-v1` result.  It does not contain or
retrieve publication-reserve source rows.  With zero candidates it records a
terminal `NOT_TRIGGERED_NO_CANDIDATE` decision and requires the reserve to stay
sealed.  A future positive search result would require a new candidate-specific
specification and lock before any custodian execution.

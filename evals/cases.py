"""Golden evaluation set: questions + the invariants a trustworthy answer must satisfy.

Assertions are behavioral/structural (not brittle exact-string matches) so they survive model
nondeterminism. Each case names the checks (see evals/scorers.py) it must pass."""

DEMO_Q = ("What neuromodulation is being trialed for anorexia nervosa, "
          "and is any of it FDA-cleared for that use?")
OVERCLAIM = "rTMS is FDA-cleared to treat anorexia nervosa."

CASES = [
    {
        "id": "anorexia_cross_source",
        "question": DEMO_Q,
        "stress_claims": [OVERCLAIM],
        "reject_contains": OVERCLAIM[:20],
        "checks": ["answer_nonempty", "cross_source_present", "all_supported_cited",
                   "citations_resolve", "negatives_scoped", "overclaim_rejected",
                   "ran_on_meterless", "receipts_present"],
    },
    {
        # generalization sanity check (live only) — a different condition must still ground,
        # cite, route through Meterless, and avoid unscoped universal negatives.
        "id": "mdd_invariants",
        "question": ("What neuromodulation devices are FDA-cleared, and which are being "
                     "trialed for major depressive disorder?"),
        "stress_claims": [],
        "reject_contains": None,
        "checks": ["answer_nonempty", "all_supported_cited", "citations_resolve",
                   "negatives_scoped", "ran_on_meterless", "receipts_present"],
    },
]

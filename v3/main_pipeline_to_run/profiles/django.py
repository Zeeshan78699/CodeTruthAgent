"""
CodeTruth UAT profile - Django.

Frozen from OBSERVED diagnostics (2026-07-06) - every value came from a real run,
none guessed:
  run_m1                              -> Django / MVC / APPROVED (health SOUND)
  run_m3 --query dead-code            -> 3345 candidates
  who-calls QuerySet.filter           -> 3 direct callers (identities below)
  change_impact QuerySet.filter       -> 3 direct / 4 affected / depth 3 / 0 guesses
  who-calls Least.__init__            -> 0 callers (honest-empty)

Django differs from flask in a GOOD way: QuerySet.filter has real cross-class,
cross-module callers (incl. a test-defined subclass) - flask had none.

PENDING: IMPACT-CLASS-001 needs
  run_m3 --query depends-on-class django.db.models.query.QuerySet
(Django's QuerySet likely has NON-ZERO external dependents, unlike flask's 0 -
freeze whatever the run actually shows.)
"""

QS = "django.db.models.query.QuerySet"
# a method with no in-repo callers (confirmed 0 via who-calls) - honest-empty case
LEAST = "django.db.models.functions.comparison.Least.__init__"

# the three OBSERVED direct callers of QuerySet.filter (order-independent check)
FILTER_CALLERS = [
    f"{QS}.contains",
    f"{QS}.get",
    "tests.custom_managers.models.CustomQuerySet.filter",
]

PROFILE = {
    "repo": "django",
    "tests": {
        "HEALTH-001": {
            "kind": "health",
            "expected": {"rating": "SOUND"},
        },

        "DEADCODE-001": {
            "kind": "dead_code",
            "expected": {"candidate_count": 3345},
        },

        # Change impact (populated) - engine-direct, identity-checked.
        "IMPACT-METHOD-001": {
            "kind": "impact_method",
            "target": f"{QS}.filter",
            "expected": {"direct_callers": FILTER_CALLERS, "affected_count": 4},
        },

        # Change impact (honest-empty) - 0 callers = known-unknown, never "safe".
        "IMPACT-METHOD-002": {
            "kind": "impact_method",
            "requirement": "Phase 5 - Engineering Scenario: Change Impact (Truth Boundary / honest-empty).",
            "target": LEAST,
            "expected": {"direct_callers": [], "affected_count": 0},
        },

        # Flagship parity (populated) - must match the engine's 3 callers / 4 affected.
        "CHANGE-IMPACT-001": {
            "kind": "change_impact",
            "requirement": "Phase 5 - Engineering Scenario: Change Impact (flagship tool, parity).",
            "target": f"{QS}.filter",
            "expected": {"direct_callers": FILTER_CALLERS, "affected_count": 4},
        },

        # Flagship parity (honest-empty).
        "CHANGE-IMPACT-002": {
            "kind": "change_impact",
            "requirement": "Phase 5 - Engineering Scenario: Change Impact (flagship tool, Truth Boundary).",
            "target": LEAST,
            "expected": {"direct_callers": [], "affected_count": 0},
        },

        # Class impact / safe refactoring. UNLIKE flask (0 external dependents),
        # Django's QuerySet has REAL external dependents - 13 in-repo callers
        # outside the class (mostly Django's own test suite exercising the ORM).
        # Same depends_on_class query, a legitimately different frozen value:
        # the generalization signal. 99 methods enumerated (counted); count == 13.
        "IMPACT-CLASS-001": {
            "kind": "impact_class",
            "target": QS,
            "expected": {"external_dependents_count": 13, "methods_count": 99},
        },

        # ---- Product front-door: Zero-Guess Truth Boundary demo (under UAT) ----
        # Verified-impact case: QuerySet.filter has 3 real callers.
        "TRUTH-BOUNDARY-001": {
            "kind": "truth_boundary",
            "requirement": "Phase 5 - Product Front-Door: Truth Boundary (verified-impact case).",
            "target": f"{QS}.filter",
            "expected": {"verdict": "VERIFIED_IMPACT",
                         "direct_callers": FILTER_CALLERS,
                         "direct_count": 3},
        },
        # Honest-empty case: Least.__init__ has 0 callers -> KNOWN-UNKNOWN, never "safe".
        "TRUTH-BOUNDARY-002": {
            "kind": "truth_boundary",
            "requirement": "Phase 5 - Product Front-Door: Truth Boundary (honest-empty case).",
            "target": LEAST,
            "expected": {"verdict": "KNOWN_UNKNOWN", "direct_count": 0},
        },
    },
}

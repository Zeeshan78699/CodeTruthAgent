"""
CodeTruth UAT profile - Flask.

Frozen from the validated flask baseline (uat_evidence/20260706T082356Z).
Every value here was OBSERVED from a real run, never guessed - that discipline
lives in how a profile is filled, not in the (generic) engine.
"""

# Shared constant - one of the reasons a Python profile beats JSON.
FLASK = "flask.app.Flask"

PROFILE = {
    "repo": "flask",
    "tests": {
        # Repository health: integrity, not coverage.
        "HEALTH-001": {
            "kind": "health",
            "expected": {"rating": "SOUND"},
        },

        # Change impact (populated): dispatch_request has exactly 1 verified caller.
        "IMPACT-METHOD-001": {
            "kind": "impact_method",
            "target": f"{FLASK}.dispatch_request",
            "expected": {
                "direct_callers": [f"{FLASK}.full_dispatch_request"],
                "affected_count": 3,
            },
        },

        # Change impact (honest-empty): 0 callers = known-unknown, never "safe".
        "IMPACT-METHOD-002": {
            "kind": "impact_method",
            "requirement": "Phase 5 - Engineering Scenario: Change Impact (Truth Boundary / honest-empty).",
            "target": f"{FLASK}.send_static_file",
            "expected": {"direct_callers": [], "affected_count": 0},
        },

        # Dead-code CANDIDATES (bounded, never a verdict). 139 frozen for flask.
        "DEADCODE-001": {
            "kind": "dead_code",
            "expected": {"candidate_count": 139},
        },

        # Class impact / safe refactoring. Flask has 30 methods and - honestly -
        # 0 external dependents (all resolved callers are internal; external
        # test callers use dynamic receivers, correctly unresolved).
        "IMPACT-CLASS-001": {
            "kind": "impact_class",
            "target": FLASK,
            "expected": {"external_dependents_count": 0, "methods_count": 30},
        },

        # Flagship tool parity (populated) - must match the engine exactly.
        "CHANGE-IMPACT-001": {
            "kind": "change_impact",
            "requirement": "Phase 5 - Engineering Scenario: Change Impact (flagship tool, parity).",
            "target": f"{FLASK}.dispatch_request",
            "expected": {
                "direct_callers": [f"{FLASK}.full_dispatch_request"],
                "affected_count": 3,
            },
        },

        # Flagship tool parity (honest-empty).
        "CHANGE-IMPACT-002": {
            "kind": "change_impact",
            "requirement": "Phase 5 - Engineering Scenario: Change Impact (flagship tool, Truth Boundary).",
            "target": f"{FLASK}.send_static_file",
            "expected": {"direct_callers": [], "affected_count": 0},
        },

        # ---- Product front-door: Zero-Guess Truth Boundary demo (under UAT) ----
        # Verified-impact case: the tool finds the real caller.
        "TRUTH-BOUNDARY-001": {
            "kind": "truth_boundary",
            "requirement": "Phase 5 - Product Front-Door: Truth Boundary (verified-impact case).",
            "target": f"{FLASK}.dispatch_request",
            "expected": {"verdict": "VERIFIED_IMPACT",
                         "direct_callers": [f"{FLASK}.full_dispatch_request"],
                         "direct_count": 1},
        },
        # Honest-empty case: 0 callers -> KNOWN-UNKNOWN, NEVER "safe to delete".
        # tb_never_asserts_safe is the check that keeps the marketing claim honest.
        "TRUTH-BOUNDARY-002": {
            "kind": "truth_boundary",
            "requirement": "Phase 5 - Product Front-Door: Truth Boundary (honest-empty case).",
            "target": f"{FLASK}.send_static_file",
            "expected": {"verdict": "KNOWN_UNKNOWN", "direct_count": 0},
        },
    },
}

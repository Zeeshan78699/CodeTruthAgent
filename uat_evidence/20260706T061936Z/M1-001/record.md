# UAT Acceptance Record - M1-001

**Status:** PASS  
**Pre-registered:** yes (criteria fixed in run_module_uat.py TESTS[] before the run)  
**Maturity status:** Validated

| Field | Value |
|---|---|
| Test ID | M1-001 |
| Objective | Module 1 alone understands the repository: emits a governance decision and a non-empty identity with bounded confidence. |
| Requirement | Phase 2 - Module 1 Repository Cognition. |
| Entry point | run_m1.run_module1 |
| Repository | C:\repos\v3\flask |
| Canonical root | C:\AI_Project\CodeTruthAgent |
| Started (UTC) | 2026-07-06T06:19:58.683337+00:00 |
| Finished (UTC) | 2026-07-06T06:20:00.361900+00:00 |
| Duration (s) | 1.68 |
| Checks passed | 4/4 |

## Scenario (what this test verifies)
GIVEN only Module 1 and a repository, WHEN cognition runs, THEN it produces a governance decision and a non-empty identity (application type, framework, architecture) with a bounded confidence - with no downstream modules involved.

## Expected result
status=COMPLETE; gate in {APPROVED, REVIEW_REQUIRED, BLOCKED}; identity fields non-empty; confidence in [0,1]. (Identity CORRECTNESS is out of scope - Phase 2.)

## Preconditions
- CODETRUTH_ROOT resolves to a folder containing the `v3` package.
- Target repository exists and is readable.

## Steps
1. Pin CODETRUTH_ROOT and load the entry point (run_m1.run_module1).
2. Run the entry point on the target repository.
3. Score the returned result against the pre-registered checks.
4. Persist raw output (result.json) and this record.

## Expected vs Actual
| Check | Expected | Observed | Result |
|---|---|---|---|
| m1_status_complete | status == COMPLETE | status=COMPLETE | PASS |
| m1_gate_decided | gate in {APPROVED, REVIEW_REQUIRED, BLOCKED} | gate=APPROVED | PASS |
| m1_identity_present | non-empty application_type, framework, architecture | application_type=WEB_APPLICATION, framework=Flask, architecture=LIBRARY | PASS |
| m1_confidence_bounded | confidence is numeric in [0.0, 1.0] | confidence=1.0 | PASS |

## Evidence
- `result.json` - raw runner output for C:\repos\v3\flask
- this record (`record.md`)

## Disposition
- **Status:** PASS
- **Severity:** N/A
- **Root cause:** -
- **Resolution:** -
- **Regression required:** no

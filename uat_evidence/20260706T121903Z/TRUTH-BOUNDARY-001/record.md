# UAT Acceptance Record - TRUTH-BOUNDARY-001

**Status:** PASS  
**Pre-registered:** yes (criteria fixed in run_module_uat.py TESTS[] before the run)  
**Maturity status:** Impl - Pending UAT

| Field | Value |
|---|---|
| Test ID | TRUTH-BOUNDARY-001 |
| Objective | truth_boundary scenario for flask |
| Requirement | Phase 5 - Product Front-Door: Truth Boundary (verified-impact case). |
| Entry point | v3.repository_reasoning.truth_boundary_demo.classify |
| Repository | C:\repos\v3\flask |
| Canonical root | C:\AI_Project\CodeTruthAgent |
| Started (UTC) | 2026-07-06T12:21:33.758571+00:00 |
| Finished (UTC) | 2026-07-06T12:21:51.304085+00:00 |
| Duration (s) | 17.55 |
| Checks passed | 6/6 |

## Scenario (what this test verifies)
GIVEN the front-door demo on flask.app.Flask.dispatch_request, WHEN it has 0 verified callers, THEN CodeTruth reports KNOWN-UNKNOWN (never 'safe to delete'); when it has callers, it reports them as verified edges - proving zero-guess behavior.

## Expected result
kind=truth_boundary; target=flask.app.Flask.dispatch_request; verdict=VERIFIED_IMPACT; direct_callers=['flask.app.Flask.full_dispatch_request']; direct_count=1; frozen before the run; identity/consistency-level checks.

## Preconditions
- CODETRUTH_ROOT resolves to a folder containing the `v3` package.
- Target repository exists and is readable.

## Steps
1. Pin CODETRUTH_ROOT and load the entry point (v3.repository_reasoning.truth_boundary_demo.classify).
2. Run the entry point on the target repository.
3. Score the returned result against the pre-registered checks.
4. Persist raw output (result.json) and this record.

## Expected vs Actual
| Check | Expected | Observed | Result |
|---|---|---|---|
| tb_resolved | target resolved (verdict not NOT_FOUND) | verdict=VERIFIED_IMPACT | PASS |
| tb_guesses_zero | guesses == 0 | guesses=0 | PASS |
| tb_never_asserts_safe | CodeTruth reading never asserts 'safe to delete' | 'safe to delete' asserted in CodeTruth reading? no | PASS |
| tb_verdict | verdict == VERIFIED_IMPACT | verdict=VERIFIED_IMPACT (expected VERIFIED_IMPACT) | PASS |
| tb_direct_identity | direct_callers == ['flask.app.Flask.full_dispatch_request'] | direct_callers=['flask.app.Flask.full_dispatch_request'] (expected ['flask.app.Flask.full_dispatch_request']; order-independent) | PASS |
| tb_direct_count | direct_count == 1 | direct_count=1 (expected 1) | PASS |

## Evidence
- `result.json` - raw runner output for C:\repos\v3\flask
- this record (`record.md`)

## Disposition
- **Status:** PASS
- **Severity:** N/A
- **Root cause:** -
- **Resolution:** -
- **Regression required:** no

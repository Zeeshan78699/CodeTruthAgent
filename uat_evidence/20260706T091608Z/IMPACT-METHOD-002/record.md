# UAT Acceptance Record - IMPACT-METHOD-002

**Status:** PASS  
**Pre-registered:** yes (criteria fixed in run_module_uat.py TESTS[] before the run)  
**Maturity status:** Impl - Pending UAT

| Field | Value |
|---|---|
| Test ID | IMPACT-METHOD-002 |
| Objective | impact_method scenario for flask |
| Requirement | Phase 5 - Engineering Scenario: Change Impact (Truth Boundary / honest-empty). |
| Entry point | reasoning_queries.who_calls / impact_of (engine-direct) |
| Repository | C:\repos\v3\flask |
| Canonical root | C:\AI_Project\CodeTruthAgent |
| Started (UTC) | 2026-07-06T09:17:03.148047+00:00 |
| Finished (UTC) | 2026-07-06T09:17:19.421626+00:00 |
| Duration (s) | 16.27 |
| Checks passed | 6/6 |

## Scenario (what this test verifies)
GIVEN a developer about to change flask.app.Flask.send_static_file, WHEN they ask 'what verifiably breaks?', THEN CodeTruth returns the verified direct callers and call-reachable set - identity-checked, no guessing.

## Expected result
kind=impact_method; target=flask.app.Flask.send_static_file; direct_callers=[]; affected_count=0; frozen before the run; identity/consistency-level checks.

## Preconditions
- CODETRUTH_ROOT resolves to a folder containing the `v3` package.
- Target repository exists and is readable.

## Steps
1. Pin CODETRUTH_ROOT and load the entry point (reasoning_queries.who_calls / impact_of (engine-direct)).
2. Run the entry point on the target repository.
3. Score the returned result against the pre-registered checks.
4. Persist raw output (result.json) and this record.

## Expected vs Actual
| Check | Expected | Observed | Result |
|---|---|---|---|
| impact_resolved | who_calls and impact_of both returned | resolved=True target=flask.app.Flask.send_static_file | PASS |
| impact_target | target IS flask.app.Flask.send_static_file | target=flask.app.Flask.send_static_file (expected flask.app.Flask.send_static_file) | PASS |
| impact_direct_consistent | direct_callers length == who_calls count | direct_n=0, count_field=0 | PASS |
| impact_reachable_consistent | affected_callers length == impact_of count | affected_n=0, count_field=0 | PASS |
| impact_direct_identity | direct_callers == [] | direct_callers=[] (expected []) | PASS |
| impact_affected_count | affected_count == 0 | affected_count=0 (expected 0) | PASS |

## Evidence
- `result.json` - raw runner output for C:\repos\v3\flask
- this record (`record.md`)

## Disposition
- **Status:** PASS
- **Severity:** N/A
- **Root cause:** -
- **Resolution:** -
- **Regression required:** no

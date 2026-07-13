# UAT Acceptance Record - IMPACT-METHOD-001

**Status:** PASS  
**Pre-registered:** yes (criteria fixed in run_module_uat.py TESTS[] before the run)  
**Maturity status:** Impl - Pending UAT

| Field | Value |
|---|---|
| Test ID | IMPACT-METHOD-001 |
| Objective | Change Impact (method): before modifying a method, show its verified blast radius over the reasoning-resolved call graph. |
| Requirement | Phase 5 - Engineering Scenario: Change Impact (method). |
| Entry point | codetruth_report._impact (RQ who-calls / impact-of) |
| Repository | C:\repos\v3\flask |
| Canonical root | C:\AI_Project\CodeTruthAgent |
| Started (UTC) | 2026-07-06T06:33:06.799928+00:00 |
| Finished (UTC) | 2026-07-06T06:33:25.324140+00:00 |
| Duration (s) | 18.52 |
| Checks passed | 2/2 |

## Scenario (what this test verifies)
GIVEN a developer about to change Flask.dispatch_request, WHEN they ask 'what verifiably breaks?', THEN CodeTruth returns the direct callers, the transitive affected set, and sample call chains computed over the verified call graph - no guessing.

## Expected result
target resolves in the call index (result not None); impact is well-formed {int direct, int transitive, list sample}. Caller COUNTS are observed evidence, reported as-is (this scenario proves the analysis runs and is well-formed, not a specific magnitude).

## Preconditions
- CODETRUTH_ROOT resolves to a folder containing the `v3` package.
- Target repository exists and is readable.

## Steps
1. Pin CODETRUTH_ROOT and load the entry point (codetruth_report._impact (RQ who-calls / impact-of)).
2. Run the entry point on the target repository.
3. Score the returned result against the pre-registered checks.
4. Persist raw output (result.json) and this record.

## Expected vs Actual
| Check | Expected | Observed | Result |
|---|---|---|---|
| impact_target_resolved | target found in call index (result is not None) | resolved=True target=flask.app.Flask.dispatch_request | PASS |
| impact_wellformed | impact = {int direct, int transitive, list sample} | direct=5, transitive=6, sample_n=5 | PASS |

## Evidence
- `result.json` - raw runner output for C:\repos\v3\flask
- this record (`record.md`)

## Disposition
- **Status:** PASS
- **Severity:** N/A
- **Root cause:** -
- **Resolution:** -
- **Regression required:** no

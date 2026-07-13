# UAT Acceptance Record - CHANGE-IMPACT-001

**Status:** PASS  
**Pre-registered:** yes (criteria fixed in run_module_uat.py TESTS[] before the run)  
**Maturity status:** Impl - Pending UAT

| Field | Value |
|---|---|
| Test ID | CHANGE-IMPACT-001 |
| Objective | change_impact scenario for flask |
| Requirement | Phase 5 - Engineering Scenario: Change Impact (flagship tool, parity). |
| Entry point | v3.repository_reasoning.change_impact.analyze |
| Repository | C:\repos\v3\flask |
| Canonical root | C:\AI_Project\CodeTruthAgent |
| Started (UTC) | 2026-07-06T12:20:57.385242+00:00 |
| Finished (UTC) | 2026-07-06T12:21:15.763873+00:00 |
| Duration (s) | 18.38 |
| Checks passed | 5/5 |

## Scenario (what this test verifies)
GIVEN a developer running the FLAGSHIP change_impact tool on flask.app.Flask.dispatch_request, WHEN they ask 'what verifiably breaks?', THEN the tool reports exactly the engine's verified answer (parity), with zero guesses.

## Expected result
kind=change_impact; target=flask.app.Flask.dispatch_request; direct_callers=['flask.app.Flask.full_dispatch_request']; affected_count=3; frozen before the run; identity/consistency-level checks.

## Preconditions
- CODETRUTH_ROOT resolves to a folder containing the `v3` package.
- Target repository exists and is readable.

## Steps
1. Pin CODETRUTH_ROOT and load the entry point (v3.repository_reasoning.change_impact.analyze).
2. Run the entry point on the target repository.
3. Score the returned result against the pre-registered checks.
4. Persist raw output (result.json) and this record.

## Expected vs Actual
| Check | Expected | Observed | Result |
|---|---|---|---|
| flagship_no_error | analyze() returned without error | error=none | PASS |
| flagship_target | resolved target IS flask.app.Flask.dispatch_request | resolved target=flask.app.Flask.dispatch_request (expected flask.app.Flask.dispatch_request) | PASS |
| flagship_direct_identity | direct_callers == ['flask.app.Flask.full_dispatch_request'] | direct_callers=['flask.app.Flask.full_dispatch_request'], direct_count=1 (expected ['flask.app.Flask.full_dispatch_request']; order-independent) | PASS |
| flagship_affected_count | affected_count == 3 | affected_count=3, affected_n=3 (expected 3) | PASS |
| flagship_zero_guesses | scope.guesses == 0 | guesses=0 | PASS |

## Evidence
- `result.json` - raw runner output for C:\repos\v3\flask
- this record (`record.md`)

## Disposition
- **Status:** PASS
- **Severity:** N/A
- **Root cause:** -
- **Resolution:** -
- **Regression required:** no

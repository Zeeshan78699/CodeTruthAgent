# UAT Acceptance Record - IMPACT-METHOD-001

**Status:** PASS  
**Pre-registered:** yes (criteria fixed in run_module_uat.py TESTS[] before the run)  
**Maturity status:** Impl - Pending UAT

| Field | Value |
|---|---|
| Test ID | IMPACT-METHOD-001 |
| Objective | Change Impact (populated): before modifying a method, show its verified blast radius over the reasoning-resolved call graph. |
| Requirement | Phase 5 - Engineering Scenario: Change Impact (method). |
| Entry point | reasoning_queries.who_calls / impact_of (engine-direct) |
| Repository | C:\repos\v3\flask |
| Canonical root | C:\AI_Project\CodeTruthAgent |
| Started (UTC) | 2026-07-06T08:24:25.295833+00:00 |
| Finished (UTC) | 2026-07-06T08:24:38.331691+00:00 |
| Duration (s) | 13.04 |
| Checks passed | 5/5 |

## Scenario (what this test verifies)
GIVEN a developer about to change Flask.dispatch_request, WHEN they ask 'what verifiably breaks?', THEN CodeTruth returns the verified direct callers and the call-reachable affected set over the verified call graph - no guessing, and identity-checked.

## Expected result
who_calls and impact_of both return; direct_callers has exactly 1 entry and it IS flask.app.Flask.full_dispatch_request; each list length matches its query count field. Identity-level, not shape-only - a wrong caller or count fails this test (this is the upgrade the helper-bug incident demanded).

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
| impact_resolved | who_calls and impact_of both returned | resolved=True target=flask.app.Flask.dispatch_request | PASS |
| impact_direct_consistent | direct_callers list length == who_calls count field | direct_callers_n=1, count_field=1 | PASS |
| impact_direct_is_one | exactly 1 direct caller (identity-checked below) | direct_callers=['flask.app.Flask.full_dispatch_request'] (expected 1) | PASS |
| impact_direct_identity | the caller IS flask.app.Flask.full_dispatch_request | 'flask.app.Flask.full_dispatch_request' present? True | direct_callers=['flask.app.Flask.full_dispatch_request'] | PASS |
| impact_reachable_consistent | affected_callers length == impact_of count field | affected_callers_n=3, count_field=3 | PASS |

## Evidence
- `result.json` - raw runner output for C:\repos\v3\flask
- this record (`record.md`)

## Disposition
- **Status:** PASS
- **Severity:** N/A
- **Root cause:** -
- **Resolution:** -
- **Regression required:** no

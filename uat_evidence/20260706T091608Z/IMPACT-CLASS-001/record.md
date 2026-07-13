# UAT Acceptance Record - IMPACT-CLASS-001

**Status:** PASS  
**Pre-registered:** yes (criteria fixed in run_module_uat.py TESTS[] before the run)  
**Maturity status:** Impl - Pending UAT

| Field | Value |
|---|---|
| Test ID | IMPACT-CLASS-001 |
| Objective | impact_class scenario for flask |
| Requirement | Phase 5 - Engineering Scenario: Safe Refactoring (class impact). |
| Entry point | reasoning_queries.depends_on_class (engine-direct) |
| Repository | C:\repos\v3\flask |
| Canonical root | C:\AI_Project\CodeTruthAgent |
| Started (UTC) | 2026-07-06T09:17:35.618959+00:00 |
| Finished (UTC) | 2026-07-06T09:17:51.894831+00:00 |
| Duration (s) | 16.28 |
| Checks passed | 7/7 |

## Scenario (what this test verifies)
GIVEN a developer about to refactor flask.app.Flask, WHEN they ask 'what depends on this class?', THEN CodeTruth returns the in-repo callers of its methods (excluding its own), honestly reporting 0 when callers are internal/dynamic.

## Expected result
kind=impact_class; target=flask.app.Flask; external_dependents_count=0; methods_count=30; frozen before the run; identity/consistency-level checks.

## Preconditions
- CODETRUTH_ROOT resolves to a folder containing the `v3` package.
- Target repository exists and is readable.

## Steps
1. Pin CODETRUTH_ROOT and load the entry point (reasoning_queries.depends_on_class (engine-direct)).
2. Run the entry point on the target repository.
3. Score the returned result against the pre-registered checks.
4. Persist raw output (result.json) and this record.

## Expected vs Actual
| Check | Expected | Observed | Result |
|---|---|---|---|
| class_query | query == depends_on_class | query=depends_on_class | PASS |
| class_target_echoed | target echoes flask.app.Flask | target=flask.app.Flask (expected flask.app.Flask) | PASS |
| class_lists_present | methods and external_dependents are lists | methods_is_list=True(n=30), external_is_list=True(n=0) | PASS |
| class_boundary_stated | boundary note present (Truth Boundary) | boundary_present=True | PASS |
| class_count_consistent | count == number of external_dependents | count=0, external_dependents_n=0 | PASS |
| class_external_count | external dependents == 0 | external_dependents count=0 (expected 0) | PASS |
| class_methods_count | methods == 30 | methods_n=30 (expected 30) | PASS |

## Evidence
- `result.json` - raw runner output for C:\repos\v3\flask
- this record (`record.md`)

## Disposition
- **Status:** PASS
- **Severity:** N/A
- **Root cause:** -
- **Resolution:** -
- **Regression required:** no

# UAT Acceptance Record - IMPACT-CLASS-001

**Status:** PASS  
**Pre-registered:** yes (criteria fixed in run_module_uat.py TESTS[] before the run)  
**Maturity status:** Impl - Pending UAT

| Field | Value |
|---|---|
| Test ID | IMPACT-CLASS-001 |
| Objective | impact_class scenario for django |
| Requirement | Phase 5 - Engineering Scenario: Safe Refactoring (class impact). |
| Entry point | reasoning_queries.depends_on_class (engine-direct) |
| Repository | C:\repos\v3\django |
| Canonical root | C:\AI_Project\CodeTruthAgent |
| Started (UTC) | 2026-07-06T11:49:59.323708+00:00 |
| Finished (UTC) | 2026-07-06T12:00:30.879842+00:00 |
| Duration (s) | 631.56 |
| Checks passed | 7/7 |

## Scenario (what this test verifies)
GIVEN a developer about to refactor django.db.models.query.QuerySet, WHEN they ask 'what depends on this class?', THEN CodeTruth returns the in-repo callers of its methods (excluding its own), honestly reporting 0 when callers are internal/dynamic.

## Expected result
kind=impact_class; target=django.db.models.query.QuerySet; external_dependents_count=13; methods_count=99; frozen before the run; identity/consistency-level checks.

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
| class_target_echoed | target echoes django.db.models.query.QuerySet | target=django.db.models.query.QuerySet (expected django.db.models.query.QuerySet) | PASS |
| class_lists_present | methods and external_dependents are lists | methods_is_list=True(n=99), external_is_list=True(n=13) | PASS |
| class_boundary_stated | boundary note present (Truth Boundary) | boundary_present=True | PASS |
| class_count_consistent | count == number of external_dependents | count=13, external_dependents_n=13 | PASS |
| class_external_count | external dependents == 13 | external_dependents count=13 (expected 13) | PASS |
| class_methods_count | methods == 99 | methods_n=99 (expected 99) | PASS |

## Evidence
- `result.json` - raw runner output for C:\repos\v3\django
- this record (`record.md`)

## Disposition
- **Status:** PASS
- **Severity:** N/A
- **Root cause:** -
- **Resolution:** -
- **Regression required:** no

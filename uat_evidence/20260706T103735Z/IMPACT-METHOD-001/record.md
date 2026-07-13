# UAT Acceptance Record - IMPACT-METHOD-001

**Status:** PASS  
**Pre-registered:** yes (criteria fixed in run_module_uat.py TESTS[] before the run)  
**Maturity status:** Impl - Pending UAT

| Field | Value |
|---|---|
| Test ID | IMPACT-METHOD-001 |
| Objective | impact_method scenario for django |
| Requirement | Phase 5 - Engineering Scenario: Change Impact (method). |
| Entry point | reasoning_queries.who_calls / impact_of (engine-direct) |
| Repository | C:\repos\v3\django |
| Canonical root | C:\AI_Project\CodeTruthAgent |
| Started (UTC) | 2026-07-06T11:08:23.914823+00:00 |
| Finished (UTC) | 2026-07-06T11:18:17.542618+00:00 |
| Duration (s) | 593.63 |
| Checks passed | 6/6 |

## Scenario (what this test verifies)
GIVEN a developer about to change django.db.models.query.QuerySet.filter, WHEN they ask 'what verifiably breaks?', THEN CodeTruth returns the verified direct callers and call-reachable set - identity-checked, no guessing.

## Expected result
kind=impact_method; target=django.db.models.query.QuerySet.filter; direct_callers=['django.db.models.query.QuerySet.contains', 'django.db.models.query.QuerySet.get', 'tests.custom_managers.models.CustomQuerySet.filter']; affected_count=4; frozen before the run; identity/consistency-level checks.

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
| impact_resolved | who_calls and impact_of both returned | resolved=True target=django.db.models.query.QuerySet.filter | PASS |
| impact_target | target IS django.db.models.query.QuerySet.filter | target=django.db.models.query.QuerySet.filter (expected django.db.models.query.QuerySet.filter) | PASS |
| impact_direct_consistent | direct_callers length == who_calls count | direct_n=3, count_field=3 | PASS |
| impact_reachable_consistent | affected_callers length == impact_of count | affected_n=4, count_field=4 | PASS |
| impact_direct_identity | direct_callers == ['django.db.models.query.QuerySet.contains', 'django.db.models.query.QuerySet.get', 'tests.custom_managers.models.CustomQuerySet.filter'] | direct_callers=['django.db.models.query.QuerySet.contains', 'django.db.models.query.QuerySet.get', 'tests.custom_managers.models.CustomQuerySet.filter'] (expected ['django.db.models.query.QuerySet.contains', 'django.db.models.query.QuerySet.get', 'tests.custom_managers.models.CustomQuerySet.filter']; order-independent) | PASS |
| impact_affected_count | affected_count == 4 | affected_count=4 (expected 4) | PASS |

## Evidence
- `result.json` - raw runner output for C:\repos\v3\django
- this record (`record.md`)

## Disposition
- **Status:** PASS
- **Severity:** N/A
- **Root cause:** -
- **Resolution:** -
- **Regression required:** no

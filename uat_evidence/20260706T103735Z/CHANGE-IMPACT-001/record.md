# UAT Acceptance Record - CHANGE-IMPACT-001

**Status:** PASS  
**Pre-registered:** yes (criteria fixed in run_module_uat.py TESTS[] before the run)  
**Maturity status:** Impl - Pending UAT

| Field | Value |
|---|---|
| Test ID | CHANGE-IMPACT-001 |
| Objective | change_impact scenario for django |
| Requirement | Phase 5 - Engineering Scenario: Change Impact (flagship tool, parity). |
| Entry point | v3.repository_reasoning.change_impact.analyze |
| Repository | C:\repos\v3\django |
| Canonical root | C:\AI_Project\CodeTruthAgent |
| Started (UTC) | 2026-07-06T11:29:10.571344+00:00 |
| Finished (UTC) | 2026-07-06T11:39:31.072063+00:00 |
| Duration (s) | 620.50 |
| Checks passed | 5/5 |

## Scenario (what this test verifies)
GIVEN a developer running the FLAGSHIP change_impact tool on django.db.models.query.QuerySet.filter, WHEN they ask 'what verifiably breaks?', THEN the tool reports exactly the engine's verified answer (parity), with zero guesses.

## Expected result
kind=change_impact; target=django.db.models.query.QuerySet.filter; direct_callers=['django.db.models.query.QuerySet.contains', 'django.db.models.query.QuerySet.get', 'tests.custom_managers.models.CustomQuerySet.filter']; affected_count=4; frozen before the run; identity/consistency-level checks.

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
| flagship_target | resolved target IS django.db.models.query.QuerySet.filter | resolved target=django.db.models.query.QuerySet.filter (expected django.db.models.query.QuerySet.filter) | PASS |
| flagship_direct_identity | direct_callers == ['django.db.models.query.QuerySet.contains', 'django.db.models.query.QuerySet.get', 'tests.custom_managers.models.CustomQuerySet.filter'] | direct_callers=['django.db.models.query.QuerySet.contains', 'django.db.models.query.QuerySet.get', 'tests.custom_managers.models.CustomQuerySet.filter'], direct_count=3 (expected ['django.db.models.query.QuerySet.contains', 'django.db.models.query.QuerySet.get', 'tests.custom_managers.models.CustomQuerySet.filter']; order-independent) | PASS |
| flagship_affected_count | affected_count == 4 | affected_count=4, affected_n=4 (expected 4) | PASS |
| flagship_zero_guesses | scope.guesses == 0 | guesses=0 | PASS |

## Evidence
- `result.json` - raw runner output for C:\repos\v3\django
- this record (`record.md`)

## Disposition
- **Status:** PASS
- **Severity:** N/A
- **Root cause:** -
- **Resolution:** -
- **Regression required:** no

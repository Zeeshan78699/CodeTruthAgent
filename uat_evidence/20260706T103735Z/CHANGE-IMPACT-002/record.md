# UAT Acceptance Record - CHANGE-IMPACT-002

**Status:** PASS  
**Pre-registered:** yes (criteria fixed in run_module_uat.py TESTS[] before the run)  
**Maturity status:** Impl - Pending UAT

| Field | Value |
|---|---|
| Test ID | CHANGE-IMPACT-002 |
| Objective | change_impact scenario for django |
| Requirement | Phase 5 - Engineering Scenario: Change Impact (flagship tool, Truth Boundary). |
| Entry point | v3.repository_reasoning.change_impact.analyze |
| Repository | C:\repos\v3\django |
| Canonical root | C:\AI_Project\CodeTruthAgent |
| Started (UTC) | 2026-07-06T11:39:31.085178+00:00 |
| Finished (UTC) | 2026-07-06T11:49:59.319708+00:00 |
| Duration (s) | 628.23 |
| Checks passed | 5/5 |

## Scenario (what this test verifies)
GIVEN a developer running the FLAGSHIP change_impact tool on django.db.models.functions.comparison.Least.__init__, WHEN they ask 'what verifiably breaks?', THEN the tool reports exactly the engine's verified answer (parity), with zero guesses.

## Expected result
kind=change_impact; target=django.db.models.functions.comparison.Least.__init__; direct_callers=[]; affected_count=0; frozen before the run; identity/consistency-level checks.

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
| flagship_target | resolved target IS django.db.models.functions.comparison.Least.__init__ | resolved target=django.db.models.functions.comparison.Least.__init__ (expected django.db.models.functions.comparison.Least.__init__) | PASS |
| flagship_direct_identity | direct_callers == [] | direct_callers=[], direct_count=0 (expected []; order-independent) | PASS |
| flagship_affected_count | affected_count == 0 | affected_count=0, affected_n=0 (expected 0) | PASS |
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

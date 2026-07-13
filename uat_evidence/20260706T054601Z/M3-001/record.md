# UAT Acceptance Record - M3-001

**Status:** PASS  
**Pre-registered:** yes (criteria fixed in run_module_uat.py TESTS[] before the run)  
**Maturity status:** Validated

| Field | Value |
|---|---|
| Test ID | M3-001 |
| Objective | Module 3 alone reasons over structure: produces phase 3A/3B results with zero guesses and no fabricated confidence. |
| Requirement | Phase 4 - Module 3 Repository Reasoning. |
| Entry point | v3.repository_reasoning.module3_pipeline.run_module3 |
| Repository | C:\repos\v3\flask |
| Canonical root | C:\AI_Project\CodeTruthAgent |
| Started (UTC) | 2026-07-06T05:46:26.582013+00:00 |
| Finished (UTC) | 2026-07-06T05:46:43.359272+00:00 |
| Duration (s) | 16.78 |
| Checks passed | 4/4 |

## Preconditions
- CODETRUTH_ROOT resolves to a folder containing the `v3` package.
- Target repository exists and is readable.

## Steps
1. Pin CODETRUTH_ROOT and load the entry point (v3.repository_reasoning.module3_pipeline.run_module3).
2. Run the entry point on the target repository.
3. Score the returned result against the pre-registered checks.
4. Persist raw output (result.json) and this record.

## Expected vs Actual
| Check | Expected | Observed | Result |
|---|---|---|---|
| m3_phases_present | report has phase_3a and phase_3b | phase_3a=y, phase_3b=y | PASS |
| m3_zero_guesses | truth_boundary.guesses == 0 | guesses=0 | PASS |
| m3_no_fabricated_confidence | truth_boundary.numeric_confidence_scores == 0 | numeric_confidence_scores=0 | PASS |
| m3_3a_resolution_reported | phase_3a reports attr_calls_total over baseline | attr_calls_total=18/2506 baseline | PASS |

## Evidence
- `result.json` - raw runner output for C:\repos\v3\flask
- this record (`record.md`)

## Disposition
- **Status:** PASS
- **Severity:** N/A
- **Root cause:** -
- **Resolution:** -
- **Regression required:** no

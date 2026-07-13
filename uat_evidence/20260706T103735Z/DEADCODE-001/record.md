# UAT Acceptance Record - DEADCODE-001

**Status:** PASS  
**Pre-registered:** yes (criteria fixed in run_module_uat.py TESTS[] before the run)  
**Maturity status:** Impl - Pending UAT

| Field | Value |
|---|---|
| Test ID | DEADCODE-001 |
| Objective | dead_code scenario for django |
| Requirement | Phase 5 - Engineering Scenario: Dead Code Candidates / Technical Debt. |
| Entry point | reasoning_queries.dead_code |
| Repository | C:\repos\v3\django |
| Canonical root | C:\AI_Project\CodeTruthAgent |
| Started (UTC) | 2026-07-06T10:58:30.303226+00:00 |
| Finished (UTC) | 2026-07-06T11:08:23.883007+00:00 |
| Duration (s) | 593.58 |
| Checks passed | 6/6 |

## Scenario (what this test verifies)
GIVEN a repository accumulating unused code, WHEN a developer asks 'what looks unused?', THEN CodeTruth returns functions with no inbound internal edge, LABELED as CANDIDATES with an explicit boundary - not a deletion verdict.

## Expected result
kind=dead_code; candidate_count=3345; frozen before the run; identity/consistency-level checks.

## Preconditions
- CODETRUTH_ROOT resolves to a folder containing the `v3` package.
- Target repository exists and is readable.

## Steps
1. Pin CODETRUTH_ROOT and load the entry point (reasoning_queries.dead_code).
2. Run the entry point on the target repository.
3. Score the returned result against the pre-registered checks.
4. Persist raw output (result.json) and this record.

## Expected vs Actual
| Check | Expected | Observed | Result |
|---|---|---|---|
| deadcode_query | query == dead_code | query=dead_code | PASS |
| deadcode_candidates_list | candidates is a list | candidates_is_list=True, n=3345 | PASS |
| deadcode_count_consistent | count == len(candidates) | count=3345, len(candidates)=3345 | PASS |
| deadcode_labeled_candidates | label == CANDIDATES (not a verdict) | label=CANDIDATES | PASS |
| deadcode_boundary_stated | boundary note present (Truth Boundary) | boundary_present=True | PASS |
| deadcode_candidate_count | count == 3345 | count=3345 (expected 3345) | PASS |

## Evidence
- `result.json` - raw runner output for C:\repos\v3\django
- this record (`record.md`)

## Disposition
- **Status:** PASS
- **Severity:** N/A
- **Root cause:** -
- **Resolution:** -
- **Regression required:** no

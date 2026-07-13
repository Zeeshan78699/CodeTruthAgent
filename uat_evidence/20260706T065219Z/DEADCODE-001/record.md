# UAT Acceptance Record - DEADCODE-001

**Status:** PASS  
**Pre-registered:** yes (criteria fixed in run_module_uat.py TESTS[] before the run)  
**Maturity status:** Impl - Pending UAT

| Field | Value |
|---|---|
| Test ID | DEADCODE-001 |
| Objective | Dead Code Candidates: list functions with no inbound internal call edge as CANDIDATES for review - never labeled confirmed dead code, since static analysis cannot prove unreachability in dynamic frameworks like Flask. |
| Requirement | Phase 5 - Engineering Scenario: Dead Code Candidates / Technical Debt. |
| Entry point | v3.repository_reasoning.reasoning_queries.dead_code |
| Repository | C:\repos\v3\flask |
| Canonical root | C:\AI_Project\CodeTruthAgent |
| Started (UTC) | 2026-07-06T06:53:14.036896+00:00 |
| Finished (UTC) | 2026-07-06T06:53:26.962090+00:00 |
| Duration (s) | 12.93 |
| Checks passed | 5/5 |

## Scenario (what this test verifies)
GIVEN a repository accumulating unused code, WHEN a developer asks 'what looks unused?', THEN CodeTruth returns functions with no inbound internal call edge, LABELED as CANDIDATES with an explicit boundary that entry points, framework callbacks, and dynamic dispatch may appear falsely - narrowing the search, not authorizing deletion.

## Expected result
query=dead_code; candidates is a list; count == len(candidates); label == CANDIDATES; a boundary note is present. The tool surfaces candidates and refuses to call them dead - the human decides.

## Preconditions
- CODETRUTH_ROOT resolves to a folder containing the `v3` package.
- Target repository exists and is readable.

## Steps
1. Pin CODETRUTH_ROOT and load the entry point (v3.repository_reasoning.reasoning_queries.dead_code).
2. Run the entry point on the target repository.
3. Score the returned result against the pre-registered checks.
4. Persist raw output (result.json) and this record.

## Expected vs Actual
| Check | Expected | Observed | Result |
|---|---|---|---|
| deadcode_query | query == dead_code | query=dead_code | PASS |
| deadcode_candidates_list | candidates is a list | candidates_is_list=True, n=139 | PASS |
| deadcode_count_consistent | count == len(candidates) | count=139, len(candidates)=139 | PASS |
| deadcode_labeled_candidates | label == CANDIDATES (not a deletion verdict) | label=CANDIDATES | PASS |
| deadcode_boundary_stated | explicit boundary note present (Truth Boundary) | boundary_present=True | PASS |

## Evidence
- `result.json` - raw runner output for C:\repos\v3\flask
- this record (`record.md`)

## Disposition
- **Status:** PASS
- **Severity:** N/A
- **Root cause:** -
- **Resolution:** -
- **Regression required:** no

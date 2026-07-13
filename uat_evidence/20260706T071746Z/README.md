# CodeTruth V3 - UAT/SIT Evidence Pack (20260706T071746Z)

**Overall:** ALL PASS  (4/4 tests passed)

Deterministic, pre-registered UAT/SIT evidence for the CodeTruth platform (Modules 1-3). Criteria were frozen before the run (`spec_snapshot.json`); the pipeline is AI-model-free and reports zero fabrications by construction.

## Contents
| File | Purpose |
|---|---|
| `manifest.json` | Environment, timestamps, code + analyzed-repo git provenance |
| `VERSION.json` | Declared platform/module versions + observed git anchor |
| `spec_snapshot.json` | Frozen pre-registered UAT criteria (goalposts) |
| `summary.json` | Machine-readable results |
| `SUMMARY.md` | Human-readable results |
| `checksums.sha256` | Integrity hashes for all evidence files |
| `<TEST-ID>/result.json` | Raw runner output per test |
| `<TEST-ID>/record.md` | Per-test acceptance record |

## Verify integrity
```
sha256sum -c checksums.sha256
```

## Reproduce
```
python run_module_uat.py <repo_path>
```
Repositories analyzed in this run: C:\repos\v3\flask

## Honest bounds
- These records test **integrity and shape** (pipeline completes, gate decided, zero guesses), not application-type correctness or resolution coverage - those are tracked separately.
- `git: unavailable` in the manifest means the path was not a git checkout at run time; it is never a fabricated value.

*CodeTruth - proves what it can, flags what it can't, never guesses.*
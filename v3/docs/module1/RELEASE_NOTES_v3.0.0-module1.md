# CodeTruth Agent V3 — Module 1: Repository Cognition Engine

**Tag:** `v3.0.0-module1`

## Summary

Module 1 is a deterministic, rule-based engine that scans a software
repository and reports its application type, primary framework,
technology stack, languages, build systems, and file inventory —
along with a governance gate decision (V3-003) used by later modules
in the CodeTruth Agent V3 pipeline.

This release covers Module 1 only: the Repository Cognition Engine.
It does not modify repositories and makes no code-change decisions.

## Validation

Run against 69 real, cloned, open-source repositories spanning 39
distinct application types — from 35 files (python-sgp4) to 61,850
files (Zephyr RTOS), including repositories with no Python code at all
(Redis, Nginx, Go, Rust, U-Boot).

```
69 repositories scanned
69/69 = 100% discovery score
69/69 = correct application type
69/69 = correct primary framework (or correctly "No Framework Detected")
69/69 = governance gate APPROVED
 0/69 = crashes
 0/69 = skipped
57/69 = 100% classification score
12/69 = 75% classification score ("No Framework Detected" — correct
        by design for non-Python system software: Redis, Nginx, Go,
        Rust, FreeCAD, LibreCAD, Shapely, rclpy, gst-python, u-boot,
        gnuradio, CodeTruthAgent)
35/35 unit tests pass
441,660 total files scanned
```

Full per-repository results: `FULL_DOMAIN_SUMMARY.md`
(also available as `.json` / `.csv`).

## What's Included

- `v3/repository_cognition/` — engine source
  (`cognition_engine.py`, `cognition_report.py`, `report_writer.py`,
  `framework_signatures.py`)
- `v3/tests/test_module1_cognition.py` — 35 unit tests
- `v3/tests/scan_all_repos_v3.py` — 69-repository validation script
- `v3/outputs/real_scans/` — per-repository scan reports (`.txt`/`.md`)
  and `FULL_DOMAIN_SUMMARY.{md,json,csv}`
- `v3/docs/module1/` — documentation:
  - `MODULE1_CAPABILITY_PROOF.md`
  - `MODULE1_DOCUMENTATION.md`
  - `MODULE1_TEST_REGISTER.md`
  - `MODULE1_EXTENSION_GUIDE.md`
  - `MODULE1_REAL_WORLD_PROBLEM.md`

## Notes

- "No Framework Detected" is a genuine, correct result for
  repositories that have no Python package framework dependency —
  it is not an error or a gap.
- All classification knowledge lives in `framework_signatures.py` and
  related tables; extending to new application types or frameworks
  does not require changes to the core engine (see
  `MODULE1_EXTENSION_GUIDE.md`).

## Next

Module 2 — Repository Graph Engine (adjacency-dict storage, two-pass
build) is next, using Module 1's output as its starting point.

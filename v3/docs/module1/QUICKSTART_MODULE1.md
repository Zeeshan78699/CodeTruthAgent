# CodeTruth Agent V3 — Module 1
## Quick Start Guide

---

## Requirements

- Python 3.10+
- No external dependencies (standard library only)

---

## Running a Scan

From the `v3/` directory:

```python
from repository_cognition import RepositoryCognitionEngine, ReportWriter

# Point this at any local repository path
report = RepositoryCognitionEngine("/path/to/your/repo").scan()

writer = ReportWriter(report)
writer.print_console()              # prints formatted report to terminal
writer.save_txt("output/scan.txt")  # plain text report
writer.save_markdown("output/scan.md")  # Markdown report
```

If `v3/` is installed as a package (`pip install .`), import as
`from v3.repository_cognition import ...` instead.

---

## Scanning Multiple Repositories

`v3/tests/scan_all_repos_v3.py` is a ready-made batch scanner. Edit the
`REPOS` list at the top of the file to point at your repositories, then:

```bash
python v3/tests/scan_all_repos_v3.py
```

This writes per-repository `.txt`/`.md` reports plus a combined
`FULL_DOMAIN_SUMMARY.{md,json,csv}` to `v3/outputs/real_scans/`.

---

## Reading the Output

### Classification section

```
Application Type:      Web Application
Primary Framework:     Django
Discovery Score:       100%
Classification:        100%
```

- **Application Type** — one of 46 supported categories (web app, ML
  pipeline, firmware, ERP system, etc.)
- **Primary Framework** — the main framework detected, or **"No
  Framework Detected"**
- **Discovery Score** — how completely the repository's files/assets
  were inventoried. 100% is the expected result for any repository.
- **Classification Score** — confidence in the type/framework result:
  - **100%** = application type and a primary framework were both
    determined
  - **75%** = application type is correct, but **no Python framework
    dependency exists** in this repository. This is the *correct*
    result for C/C++ system software (e.g. Redis, Nginx, Go, Rust) —
    not an error.

### Governance Gate

```
GOVERNANCE GATE — V3-003
  Status   : APPROVED
  Decision : Pipeline may proceed to Module 2
```

`APPROVED` means the scan completed and downstream tooling may use
this report. `BLOCKED` indicates a scan failure (see the `ERROR`
section of the report for details).

---

## Interpreting "No Framework Detected"

If you see:

```
Primary Framework:     No Framework Detected
Classification:        75%
```

This means Module 1 correctly determined the application type, but
found no Python package that represents "the framework" of this
repository — which is expected for:

- Non-Python system software (Redis, Nginx, Go compiler, Rust
  compiler, U-Boot)
- CAD/GIS tools without a dominant Python framework (FreeCAD, LibreCAD,
  Shapely)
- Bindings/wrappers without their own pip package (gst-python, rclpy)

This is **not a bug** and does not need to be "fixed" by the user.

---

## Unknown File Extensions

The "WARNINGS & DIAGNOSTICS" section may list file extensions not yet
in the language registry, e.g.:

```
UNKNOWN EXTENSIONS (3 found — not yet in registry):
.in  .pyi  .typed
```

These do not affect the discovery score. They're informational —
see `MODULE1_EXTENSION_GUIDE.md` if you want to add them.

---

## Running the Test Suite

```bash
python v3/tests/test_module1_cognition.py
```

Expected: `35/35 tests passed`.

---

## More

- Architecture details: `MODULE1_DOCUMENTATION.md`
- Full validation results: `MODULE1_CAPABILITY_PROOF.md`
- Adding new application types/frameworks: `MODULE1_EXTENSION_GUIDE.md`

# CodeTruth Agent V3 — Module 1: Repository Cognition Engine

Independent AI research project. GPLv3.

## What it does

Module 1 scans a software repository and answers a basic but
foundational question: **"What kind of repository is this?"**

Given a path to a repository, it produces:

- **Application type** (one of 46 supported types — web app, ML
  pipeline, firmware, quantum computing, ERP system, drone/UAV, etc.)
- **Primary framework** (e.g. Django, Qiskit, Odoo — or "No Framework
  Detected" when none exists, which is itself a meaningful, correct
  result for C/C++ system software)
- **Technology stack, languages, build systems**
- **Entry points, configuration files, documentation, test
  directories**
- **Discovery score** and **classification score**
- A **governance gate decision (V3-003)** — APPROVED / BLOCKED

It performs no network access and makes no modifications to the
scanned repository.

## Example

```bash
python -c "
from v3.repository_cognition import RepositoryCognitionEngine, ReportWriter
report = RepositoryCognitionEngine('/path/to/repo').scan()
ReportWriter(report).print_console()
"
```

Output (abridged):

```
CLASSIFICATION
  Application Type:      Web Application
  Primary Framework:     Django
  Discovery Score:       100%
  Classification:        100%

GOVERNANCE GATE — V3-003
  Status   : APPROVED
  Decision : Pipeline may proceed to Module 2
```

## Validation

Run against 69 real, cloned, open-source repositories spanning 39
application types, from 35 files (python-sgp4) to 61,850 files
(Zephyr RTOS):

```
69/69 = 100% discovery score
69/69 = correct application type
69/69 = correct primary framework (or correctly "No Framework Detected")
69/69 = governance gate APPROVED
 0/69 = crashes
35/35 = unit tests pass
441,660 total files scanned
```

Full results: [`v3/docs/module1/MODULE1_CAPABILITY_PROOF.md`](v3/docs/module1/MODULE1_CAPABILITY_PROOF.md)

## How it works (brief)

Classification combines three signal sources:

1. **Package/dependency signals** — from `requirements.txt`,
   `pyproject.toml`, `setup.py`, etc.
2. **Import signals** — `import` statements parsed via `ast` from a
   sample of source files.
3. **Content pattern signals** — for non-Python-package repositories
   (C/C++ firmware, hardware bindings), specific identifying files are
   checked directly.

Primary framework resolution then runs a three-pass process
(self-name match → type match → priority fallback), with generic
utility packages (Click, Requests, Pytest, etc.) excluded from
ever being selected as the *primary* framework.

Full details: [`v3/docs/module1/MODULE1_DOCUMENTATION.md`](v3/docs/module1/MODULE1_DOCUMENTATION.md)

## Documentation

- [`MODULE1_REAL_WORLD_PROBLEM.md`](v3/docs/module1/MODULE1_REAL_WORLD_PROBLEM.md) — the problem this solves, and how
- [`MODULE1_DOCUMENTATION.md`](v3/docs/module1/MODULE1_DOCUMENTATION.md) — architecture and scoring
- [`MODULE1_CAPABILITY_PROOF.md`](v3/docs/module1/MODULE1_CAPABILITY_PROOF.md) — full 69-repo validation table
- [`MODULE1_TEST_REGISTER.md`](v3/docs/module1/MODULE1_TEST_REGISTER.md) — test suite + issues found/fixed
- [`MODULE1_EXTENSION_GUIDE.md`](v3/docs/module1/MODULE1_EXTENSION_GUIDE.md) — how to add new types/frameworks

## Project Structure

```
v3/
├── repository_cognition/   # Module 1 source
│   ├── cognition_engine.py
│   ├── cognition_report.py
│   ├── report_writer.py
│   └── framework_signatures.py
├── tests/
│   ├── test_module1_cognition.py   # 35 unit tests
│   └── scan_all_repos_v3.py        # 69-repo validation script
├── outputs/real_scans/              # per-repo reports + summary
└── docs/module1/                    # documentation (this README links here)
```

## Status

Module 1 is complete and frozen as of `v3.0.0-module1`.
Module 2 (Repository Graph Engine) is next.

## License

GPLv3 — see `LICENSE`.

## Author

Zeeshan Saud — Independent AI Researcher, UAE
github.com/Zeeshan78699/CodeTruthAgent

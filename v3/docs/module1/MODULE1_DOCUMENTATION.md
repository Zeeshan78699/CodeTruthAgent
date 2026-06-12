# CodeTruth Agent V3 — Module 1
## Repository Cognition Engine — Documentation

---

## 1. Purpose

Module 1 is the first stage of the CodeTruth Agent V3 pipeline. Before
any code-modification governance can happen, the system must first
understand what kind of repository it is looking at: what the
application does, what framework it is built on, what languages and
build systems are present, and how large/complex it is.

Module 1 produces this understanding as a structured report and a
governance gate decision (V3-003) that determines whether the pipeline
may proceed to Module 2.

---

## 2. What Module 1 Produces

For a given repository path, Module 1 outputs:

- **Repository identity** — name, path, scan timestamp, one-line purpose
- **Classification** — application type, primary framework, secondary
  frameworks, discovery score, classification score
- **Repository scale** — total files, Python file count, detected test
  suites
- **Discovered assets** — languages, documentation file types, ML model
  files
- **Build systems** — e.g. Make, CMake, Cargo, Setuptools, NPM, Gradle
- **Technology stack** — e.g. Python, Docker, Redis, AWS
- **Entry points** — likely executable/CLI scripts
- **Configuration files**
- **Documentation files**
- **Warnings/diagnostics** — unrecognized file extensions
- **Governance gate decision (V3-003)**

Reports can be saved as `.txt` and `.md`.

---

## 3. How Classification Works

Classification combines three signal sources:

1. **Package/dependency signals** — packages found in `requirements.txt`,
   `pyproject.toml`, `setup.py`, etc., each mapped to an application
   type and a weight.

2. **Import signals** — `import` / `from ... import` statements parsed
   via Python's `ast` module from a sample of source files, mapped the
   same way as package signals.

3. **Content pattern signals** — for repositories that are not primarily
   distributed as a Python package (e.g. C/C++ projects like U-Boot,
   GStreamer, ArduPilot, Kivy, GNU Radio), specific file paths
   (e.g. `common/board_f.c`, `gi/overrides/Gst.py`,
   `ArduCopter/ArduCopter.cpp`) are checked for existence or content.
   These carry a high weight (15) and establish repository identity
   even when no pip package signal is present.

All signals are aggregated into per-type scores. A hierarchy table
resolves competing types — e.g. an `AUDIO_PROCESSING` content-pattern
match suppresses `ML_PIPELINE` signals that would otherwise arise from
`torch` imports used internally.

---

## 4. Primary Framework Resolution

Once the application type is determined, the primary framework name is
resolved using a three-pass approach:

- **Pass 0 — self-name match**: if a detected package's normalized name
  matches the repository's own directory name (accounting for common
  `_py`/`python_` affixes), that package's display name is used
  immediately. This correctly resolves cases like `cvxpy` (not
  `ortools`) and `solana-py` → `Solana` (not `Web3.py`).

- **Pass 1 — type match**: among remaining candidates, prefer a package
  whose own mapped application type matches the repository's determined
  application type. This resolves cases like `astropy` (not `sgp4`,
  even though both map to SPACE_SYSTEM).

- **Pass 2 — priority order fallback**: if neither pass resolves a
  unique answer, fall back to a fixed priority ordering of known
  frameworks (core web frameworks first, then ML, then domain-specific).

All candidate matches use word-boundary regex matching against
dependency file contents, not raw substring matching — this avoids
false positives such as a 2-character package name matching inside
unrelated words.

---

## 5. Discovery Score

The discovery score reflects how completely the engine was able to
inventory the repository's files and assets. A score of 100% means all
files were enumerated and categorized (as a known language/doc type, a
build file, a config file, or flagged as an unrecognized extension for
future registry additions).

A discovery score of 100% does **not** imply every file extension is
in the language registry — unrecognized extensions are reported as
warnings/diagnostics without affecting the discovery score.

---

## 6. Classification Score

The classification score reflects confidence in the application type
and framework determination:

- **100%** — application type and primary framework both resolved with
  high-confidence signals (package/import signals, or a high-weight
  content pattern).
- **75%** — application type resolved, but no primary framework could
  be determined (commonly correct for non-Python system software such
  as Redis, Nginx, LibreCAD, or for bindings without their own pip
  package, such as gst-python, rclpy, shapely).

---

## 7. Governance Gate V3-003

After classification, Module 1 issues a governance gate decision:

```
Status   : APPROVED | BLOCKED
Decision : Pipeline may proceed to Module 2 | Pipeline halted
Rule     : Repository understanding is complete
```

Across the 69-repository validation set, all 69 scans resulted in
APPROVED.

---

## 8. Architecture Notes

- All classification knowledge (package signatures, import signatures,
  content patterns, framework display names, file extension mappings,
  type hierarchy) lives in `framework_signatures.py` and the
  configuration tables inside `cognition_engine.py`.
- Adding support for a new application type or framework does not
  require changes to the core scanning/discovery logic — only additions
  to these signature tables (see MODULE1_EXTENSION_GUIDE.md).
- The engine performs no network access and makes no modifications to
  the scanned repository.

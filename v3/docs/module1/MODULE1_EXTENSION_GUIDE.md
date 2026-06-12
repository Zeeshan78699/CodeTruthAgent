# CodeTruth Agent V3 — Module 1
## Extension Guide

This guide describes how to add support for a new application type,
framework, or language/file extension without modifying the core
scanning engine logic.

---

## 1. Adding a New Package/Import Signal

If a Python package should map to an existing or new application type:

**File:** `framework_signatures.py`

Add an entry to `PACKAGE_SIGNATURES` (for dependency-file detection)
and/or `IMPORT_SIGNATURES` (for `import`-statement detection):

```python
"some_package": ("SOME_APPLICATION_TYPE", weight),
```

- `weight` of `2` is the standard signal strength.
- `weight` of `3` or `4` is used when a package needs to override a
  competing, more generic signal (e.g. `cocotb` at weight 3 for
  FPGA_HARDWARE, `gnuradio` at weight 4 for DSP_TOOL).

---

## 2. Adding a Content-Pattern Signal

For repositories that are not distributed as installable Python
packages (C/C++ projects, firmware, bindings), add an entry to the
content-pattern list in `framework_signatures.py`:

```python
{
    "name": "SomeProject",
    "app_type": "SOME_APPLICATION_TYPE",
    "weight": 15,
    "file_patterns": ["path/to/identifying/file.c", "..."],
    "content_keywords": [],  # empty = file existence alone is sufficient
},
```

Weight 15 is the standard "absolute identity" weight for content
patterns — it establishes the repository's identity even in the
presence of many competing import signals (e.g. torch imports inside
an audio-processing repo).

If `content_keywords` is non-empty, the pattern only fires when the
listed keyword(s) are found inside the matched file.

---

## 3. Adding a New Application Type

1. Add the new type name to the `ApplicationType` enum in
   `cognition_report.py`.
2. Add at least one package/import signal or content pattern (steps 1–2
   above) that maps to the new type.
3. If the new type could be confused with existing types, add an entry
   to the `TYPE_HIERARCHY` dict in `cognition_engine.py` listing which
   competing types should be suppressed when this type's signal fires.
4. Add a framework display name in `_infer_framework_name`'s
   `framework_names` dict if the package's pip name differs from its
   display name (e.g. `"cvxpy": "CVXPY"`).

---

## 4. Adding a New File Extension

**File:** `framework_signatures.py`, `LANGUAGE_EXTENSIONS` dict:

```python
".ext": "Display Name",
```

Each scan report lists unrecognized extensions found in that
repository under "WARNINGS & DIAGNOSTICS" — these are the primary
source for new entries.

Avoid adding extensions that are also common as substrings of other
recognized extensions or that collide with existing entries (e.g.
`.rst` was deliberately removed from `LANGUAGE_EXTENSIONS` because it
collided with both "ReStructuredText" documentation files and an
"ANSYS Results" mapping, causing false ML-model detections).

---

## 5. Adding a New ML Model File Extension

**File:** `framework_signatures.py`, `MODEL_FILE_EXTENSIONS` dict.

Avoid extensions that are too generic to reliably indicate a model file
on their own (e.g. `.xml`, standalone `.bin`) — these were removed
during validation due to false positives across many unrelated
repositories.

---

## 6. Verifying Changes

After any change:

```bash
python v3/tests/test_module1_cognition.py
```

All 35 tests must pass. If the change affects a real repository's
classification, re-run that repository's scan via
`v3/tests/scan_all_repos_v3.py` (or a targeted single-repo scan) and
confirm the expected application type and framework name.

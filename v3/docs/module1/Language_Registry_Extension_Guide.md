# CodeTruth V3 — Language Registry Extension Guide

## Purpose

This guide explains how to add new file extensions to CodeTruth V3 when a new repository domain is scanned and unknown extensions are found.

**Core rule:** Never touch `framework_signatures.py`. All additions go to `language_registry_expansion.py` only.

---

## The Pattern

```
New Repository Scanned
        ↓
Unknown Extensions Found in Output
        ↓
Run Scanner Script
        ↓
Add to language_registry_expansion.py
        ↓
Re-run Test
        ↓
Warning Reduced — Done
```

---

## Step 1 — Identify Unknown Extensions

After running any Module 1 test, look for this in the console output:

```
! 17 file extension(s) not in language registry:
  .dcm, .nii, .hl7 ...
```

Or check the JSON evidence file:

```json
"unknown_file_extensions": [
    ".dcm",
    ".nii",
    ".hl7"
]
```

---

## Step 2 — Run the Scanner Script

Run the scanner against the new repository before editing anything:

```powershell
python v3\tests\module1\classification\scan_unknown_extensions.py C:\repos\v3\pydicom
```

Output:

```
Genuine Unknowns — ADD THESE to language_registry_expansion.py
-----------------------------------------
  .dcm            :   847 files
  .nii            :    23 files
  .hl7            :     5 files

Copy-paste template:
  # ----------------------------------------------------------
  # pydicom — discovered 2026-06-23
  # ----------------------------------------------------------
  ".dcm": "DESCRIPTION HERE",
  ".nii": "DESCRIPTION HERE",
  ".hl7": "DESCRIPTION HERE",
```

The scanner also tells you which extensions are **already covered** by the registry so you do not add duplicates.

---

## Step 3 — Open the Expansion File

Open this file only:

```
v3\repository_cognition\module1_extensions\language_registry_expansion.py
```

Do NOT open or edit:

```
❌ framework_signatures.py     ← Module 1 Core — FROZEN
❌ cognition_engine.py         ← Module 1 Core — FROZEN
❌ cognition_report.py         ← Module 1 Core — FROZEN
```

---

## Step 4 — Add the New Entries

Find the `LANGUAGE_REGISTRY_EXPANSION` dictionary. Scroll to the bottom, above the `# ADD NEW ENTRIES BELOW THIS LINE` comment.

Add a new block following this exact format:

```python
# ----------------------------------------------------------
# Medical Imaging — discovered during pydicom scan (2026-06-23)
# ----------------------------------------------------------
".dcm":  "DICOM Medical Image",
".nii":  "NIfTI Brain Image",
".mgh":  "FreeSurfer Volume Format",
```

**Rules when adding:**

| Rule | Detail |
|---|---|
| Add a comment block | Domain name + discovery date |
| Use lowercase extension | `.dcm` not `.DCM` |
| Add a clear description | What the file type actually is |
| Never duplicate | Check scanner output for already-covered list |
| Never delete existing entries | Only add, never remove |

---

## Step 5 — Re-run the Test

```powershell
python v3\tests\module1\classification\tc_m1_002_medical_repository.py
```

Expected output:

```
LANGUAGE REGISTRY EXPANSION
------------------------------------------------------------
PASS Language Registry Expansion (18 entries)
     Genuine unknown extensions: 0
```

The warning count reduces automatically. No other change is needed.

---

## Domain Reference — What to Add Per Domain

| Domain | Typical Extensions |
|---|---|
| Medical Imaging | `.dcm`, `.nii`, `.nii.gz`, `.mgh`, `.mnc` |
| HL7 / FHIR | `.hl7`, `.fhir` |
| Robotics / ROS2 | `.launch`, `.urdf`, `.xacro`, `.sdf`, `.world` |
| Climate Science | `.nc`, `.grib`, `.grib2`, `.h5`, `.hdf5` |
| FPGA / Hardware | `.v`, `.sv`, `.vhd`, `.vhdl`, `.xdc`, `.bit` |
| Automotive | `.arxml`, `.fibex`, `.ldf`, `.dbc` |
| Aerospace | `.stl`, `.step`, `.iges`, `.nas` |
| Scientific | `.mat`, `.fits`, `.zarr`, `.nc4` |

---

## How the Filter Works

The `filter_genuine_unknown_extensions()` function separates the core warning into two groups:

```python
covered, genuine = filter_genuine_unknown_extensions(
    core_report.unknown_file_extensions
)

# covered  → already in registry → suppress warning
# genuine  → not in registry    → log for investigation
```

This means the core scan warning is never silenced entirely — it is filtered. Only genuinely unknown extensions are shown.

---

## File Locations

| File | Purpose | Editable |
|---|---|---|
| `language_registry_expansion.py` | Extension registry | ✅ Yes |
| `scan_unknown_extensions.py` | Scanner utility | ✅ Yes |
| `framework_signatures.py` | Module 1 Core | ❌ Never |
| `cognition_engine.py` | Module 1 Core | ❌ Never |
| `cognition_report.py` | Module 1 Core | ❌ Never |

---

## Summary

```
Scan → Find → Add to language_registry_expansion.py → Re-run → Done

One file. One rule. No core changes. Ever.
```

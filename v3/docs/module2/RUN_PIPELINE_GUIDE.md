# CodeTruth V3 — How to Run the Full Pipeline

**File:** `pipeline.py`
**Purpose:** Module 1 + Module 2 connected — recommended for production
**Gate:** Module 1 must APPROVE before Module 2 runs

---

## Setup

```powershell
cd C:\AI_Project\CodeTruthAgent
.venv\Scripts\activate
```

---

## Basic Usage

```powershell
python pipeline.py "C:\repos\v3\fastapi"
```

**Actual output:**
```
======================================================================
MODULE 1 — Repository Cognition Engine
======================================================================
Repo: C:\repos\v3\fastapi
  Application Type : API_SERVICE
  Framework        : FastAPI
  Architecture     : MONOLITH
  Confidence       : 1.0
  Gate             : [OK] APPROVED
  Language         : python
======================================================================
MODULE 2 — Repository Graph Intelligence
======================================================================
  Adapter  : PythonAdapter
  Files scanned : 1120
  Functions     : 4590
  Classes       : 692
  Baseline unresolved  : 11413
  Remaining unresolved : 8400
  builtin_type         : 2928
  constructor          : 84
  factory              : 1
  DR total resolved    : 3013
  DR reduction         : 26.4%
  Gate          : [OK] APPROVED
======================================================================
PIPELINE COMPLETE
  M1 Gate  : APPROVED
  M2 Gate  : APPROVED
  Language : python
  Status   : COMPLETE
======================================================================
```

---

## Save Report

```powershell
python pipeline.py "C:\repos\v3\fastapi" --save
```

Creates: `pipeline_report_fastapi.json`

---

## Force Run When REVIEW_REQUIRED

```powershell
python pipeline.py "C:\repos\v3\striplog" --force
```

---

## With Annotation Resolver

```powershell
python pipeline.py "C:\repos\v3\pytorch" --annotation
```

---

## Batch Mode — Multiple Repositories

Create `repos.txt`:
```
C:\repos\v3\fastapi
C:\repos\v3\django
C:\repos\v3\pytorch
# C:\repos\skip_this_one
```

Run:
```powershell
python pipeline.py --batch repos.txt --save
```

---

## Validated Results — 11 Domains

```
Repo        Domain                           Framework    Gate
───────────────────────────────────────────────────────────────
fastapi     API_SERVICE                      FastAPI      ✅
pytorch     ML_PIPELINE                      PyTorch      ✅
django      WEB_APPLICATION                  Django       ✅
biopython   SCIENTIFIC_COMPUTING             BioPython    ✅
OpenMDAO    AEROSPACE_STRUCTURAL_SIMULATION  OpenMDAO     ✅
lasio       WELL_LOGGING                     Lasio        ✅
welleng     DRILLING_SYSTEM                  welleng      ✅
ccxt        FINANCE_SYSTEM                   CCXT         ✅
pandapower  ENERGY_SYSTEM                    pandapower   ✅
poliastro   SPACE_SYSTEM                     poliastro    ✅
pydicom     MEDICAL_SYSTEM                   PyDICOM      ✅
```

---

## Gate Decision Examples

### APPROVED → Module 2 runs

```powershell
python pipeline.py "C:\repos\v3\welleng"
```
```
  Gate   : [OK] APPROVED
  Status : COMPLETE
```

### REVIEW_REQUIRED → Module 2 skipped

```powershell
python pipeline.py "C:\repos\v3\striplog"
```
```
  Gate : [WARN] REVIEW_REQUIRED
  REVIEW_REQUIRED — use --force to run Module 2 anyway.
  Status : REVIEW_REQUIRED
```

### BLOCKED → Module 2 never runs

```powershell
python pipeline.py "C:\repos\broken_repo"
```
```
  Gate : [STOP] BLOCKED
  Status : BLOCKED
```

---

## All Options

```
pipeline.py <repo_path>     Path to repository.
            --save          Save JSON report.
            --json          Print JSON to console.
            --force         Run M2 even if REVIEW_REQUIRED.
            --annotation    Run annotation resolver (Python only).
            --batch FILE    Run on list of repos in text file.
```

---

## Exit Codes

```
0 → COMPLETE
1 → BLOCKED / REVIEW_REQUIRED / ERROR
```

---

## When to Use Which Script

```
run_m1.py    → Just need domain classification
               Checking if a repo is safe to scan

run_m2.py    → Repo already classified
               Known language (you choose adapter)

pipeline.py  → Production use (recommended)
               Unknown repositories
               Full governance required
               AI agent pre-flight check
               Batch processing
```

---

*CodeTruth V3 — AI imagines. CodeTruth checks. Nature tests. Humans decide.*

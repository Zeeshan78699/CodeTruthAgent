# CodeTruth V3 — How to Run Module 1

**File:** `run_m1.py`
**Purpose:** Standalone Module 1 — Repository Cognition Engine
**Requires:** Module 2 NOT required

---

## Setup

```powershell
cd C:\AI_Project\CodeTruthAgent
.venv\Scripts\activate
```

---

## Basic Usage

```powershell
python run_m1.py "C:\repos\v3\fastapi"
```

**Actual output:**
```
======================================================================
CodeTruth V3 — Module 1: Repository Cognition Engine
======================================================================
Repository : C:\repos\v3\fastapi
Started    : 2026-06-28 09:47:41 UTC
----------------------------------------------------------------------
Running cognition engine...
Running domain enhancement...
----------------------------------------------------------------------
RESULTS
----------------------------------------------------------------------
  Application Type : API_SERVICE
  Framework        : FastAPI
  Architecture     : MONOLITH
  Confidence       : 1.0
  Risk Score       : 7/10
  Assumptions      : 994
  Constraints      : 98
----------------------------------------------------------------------
  GOVERNANCE GATE  : ✅  APPROVED
======================================================================
```

---

## Save Report to JSON

```powershell
python run_m1.py "C:\repos\v3\fastapi" --save
```

Creates: `m1_report_fastapi.json`

---

## JSON Output to Console

```powershell
python run_m1.py "C:\repos\v3\fastapi" --json
```

---

## Validated Results by Domain

```
Repository   Domain                           Framework    Gate
──────────────────────────────────────────────────────────────
fastapi      API_SERVICE                      FastAPI      ✅
pytorch      ML_PIPELINE                      PyTorch      ✅
django       WEB_APPLICATION                  Django       ✅
biopython    SCIENTIFIC_COMPUTING             BioPython    ✅
OpenMDAO     AEROSPACE_STRUCTURAL_SIMULATION  OpenMDAO     ✅
lasio        WELL_LOGGING                     Lasio        ✅
welleng      DRILLING_SYSTEM                  welleng      ✅
ccxt         FINANCE_SYSTEM                   CCXT         ✅
pandapower   ENERGY_SYSTEM                    pandapower   ✅
poliastro    SPACE_SYSTEM                     poliastro    ✅
pydicom      MEDICAL_SYSTEM                   PyDICOM      ✅
```

---

## Gate Decision Examples

### APPROVED

```powershell
python run_m1.py "C:\repos\v3\welleng"
```
```
  Application Type : DRILLING_SYSTEM
  Framework        : welleng
  Architecture     : LIBRARY
  Confidence       : 1.0
  GOVERNANCE GATE  : ✅  APPROVED
```

### REVIEW_REQUIRED

```powershell
python run_m1.py "C:\repos\v3\striplog"
```
```
  Application Type : WELL_LOGGING
  GOVERNANCE GATE  : ⚠️  REVIEW_REQUIRED
```

### BLOCKED

```powershell
python run_m1.py "C:\repos\broken_repo"
```
```
  GOVERNANCE GATE  : 🛑  BLOCKED
```

---

## Exit Codes

```
0 → APPROVED
1 → REVIEW_REQUIRED
2 → BLOCKED
```

Use in CI/CD:

```powershell
python run_m1.py "C:\repos\my_repo"
if ($LASTEXITCODE -eq 0) {
    Write-Host "Safe to proceed"
} else {
    Write-Host "Human review needed"
}
```

---

## All Options

```
run_m1.py <repo_path>        Required. Path to repository.
          --json             Print full JSON to console.
          --save             Save JSON report to disk.
```

---

*CodeTruth V3 — AI imagines. CodeTruth checks. Nature tests. Humans decide.*

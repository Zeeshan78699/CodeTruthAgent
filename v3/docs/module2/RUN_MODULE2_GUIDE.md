# CodeTruth V3 — How to Run Module 2

**File:** `run_m2.py`
**Purpose:** Standalone Module 2 — Repository Graph Intelligence
**Requires:** Module 1 NOT required (but no gate check)

---

## Setup

```powershell
cd C:\AI_Project\CodeTruthAgent
.venv\Scripts\activate
```

---

## Basic Usage — Python Repository

```powershell
python run_m2.py "C:\repos\v3\fastapi"
```

**Actual output:**
```
======================================================================
CodeTruth V3 — Module 2: Repository Graph Intelligence
======================================================================
Repository : C:\repos\v3\fastapi
Language   : python
Started    : 2026-06-28 10:42:32 UTC
----------------------------------------------------------------------
Running PythonAdapter...
----------------------------------------------------------------------
GRAPH STATS
----------------------------------------------------------------------
  Functions      : 4590
  Classes        : 692
  Modules parsed : 1120
  Files scanned  : 1120
  Unresolved calls: 11413
----------------------------------------------------------------------
DEEP RESOLUTION
----------------------------------------------------------------------
  Baseline unresolved  : 11413
  Remaining unresolved : 8400

  builtin_type         : 2928
  constructor          : 84
  factory              : 1
  property             : 0
  inheritance          : 0
  annotation           : 0

  DR total resolved    : 3013
  DR reduction         : 26.4%
----------------------------------------------------------------------
  FILES SCANNED    : 1120
  GOVERNANCE GATE  : ✅  APPROVED
======================================================================
```

---

## Specify Language Adapter

```powershell
# Python (default)
python run_m2.py "C:\repos\v3\fastapi"

# C#
python run_m2.py "C:\repos\my_dotnet_app" --language csharp

# Oracle SQL
python run_m2.py "C:\repos\my_sql_repo" --language sql

# Go
python run_m2.py "C:\repos\my_go_service" --language go
```

---

## With Annotation Resolver

```powershell
python run_m2.py "C:\repos\v3\pytorch" --annotation
```

```
ANNOTATION RESOLVER
----------------------------------------------------------------------
  Annotation resolved : 26975
  New reduction pct   : 13.92%
```

---

## Save Report

```powershell
python run_m2.py "C:\repos\v3\fastapi" --save
```

Creates: `m2_report_fastapi.json`

---

## Example by Language

### C# Repository

```powershell
python run_m2.py "C:\repos\my_aspnet_app" --language csharp
```
```
  DR field_type : 28
  Overall pct   : 86.49%
  Framework     : aspnet_core
  Gate          : ✅  APPROVED
```

### Oracle SQL Repository

```powershell
python run_m2.py "C:\repos\my_oracle_db" --language sql
```
```
  Dialect       : oracle_plsql
  Resolution    : 72.0%
  Gate          : ✅  APPROVED
```

### Go Repository

```powershell
python run_m2.py "C:\repos\my_go_api" --language go
```
```
  Module        : github.com/myorg/myapi
  Framework     : net_http
  Resolution    : 30.43%
  Gate          : ✅  APPROVED
```

---

## All Options

```
run_m2.py <repo_path>        Required. Path to repository.
          --language python  Adapter: python/csharp/sql/go (default: python)
          --json             Print full JSON to console.
          --save             Save JSON report to disk.
          --annotation       Run annotation resolver (Python only).
```

---

## Warning: No Gate Check

```
Running run_m2.py without run_m1.py means:
  - No domain classification
  - No pre-flight gate check
  - You choose the adapter manually

For full governance, use pipeline.py instead.
```

---

*CodeTruth V3 — AI imagines. CodeTruth checks. Nature tests. Humans decide.*

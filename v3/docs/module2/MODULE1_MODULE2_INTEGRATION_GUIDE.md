# CodeTruth Agent V3 — Module 1 + Module 2 Integration Guide

**Audience:** Developers connecting Module 1 and Module 2 in a pipeline
**Date:** 2026-06-25
**Version:** v3.0.0-modules-1-2-complete

---

## Overview

Module 1 and Module 2 are designed to run sequentially.
Module 1 must APPROVE a repository before Module 2 scans it.
This guide shows how to connect them in code.

```
Repository Path
      │
      ▼
Module 1 (What is this repo?)
      │
      ├── APPROVED ──────────────────────→ Module 2 (What calls what?)
      │                                          │
      ├── REVIEW_REQUIRED → human review         ▼
      │                                    Full analysis report
      └── BLOCKED ──────────→ stop
```

---

## Minimum Integration — 10 Lines

```python
from v3.repository_cognition import RepositoryCognitionEngine
from v3.repository_cognition.module1_extensions import EnhancedReportBuilder
from v3.repository_graph.languages.python_adapter import PythonAdapter

repo_path = r"C:\repos\your_repo"

# Step 1 — Module 1
report   = RepositoryCognitionEngine(repo_path).scan()
enhanced = EnhancedReportBuilder().build(report, repo_path)
gate     = enhanced.gate.gate_decision

# Step 2 — Gate check
if gate != "APPROVED":
    print(f"Gate: {gate} — Module 2 not run")
else:
    # Step 3 — Module 2
    graph = PythonAdapter().scan(repo_root=repo_path, file_paths=[])
    print(f"Resolved: {graph['deep_resolution']['final']['resolved_by_pipeline']}")
```

---

## Full Integration — Production Pattern

```python
"""
pipeline.py
Full Module 1 → Module 2 integration pipeline.
"""

from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime as dt, UTC
from typing import Any

from v3.repository_cognition import RepositoryCognitionEngine
from v3.repository_cognition.module1_extensions import EnhancedReportBuilder
from v3.repository_graph.languages.python_adapter import PythonAdapter
from v3.repository_graph.languages.sql_adapter import SQLAdapter
from v3.repository_graph.languages.csharp_adapter import CSharpAdapter
from v3.repository_graph.languages.go_adapter import GoAdapter


# ── Adapter registry ─────────────────────────────────────────────────
ADAPTERS = {
    "python":        PythonAdapter,
    "csharp":        CSharpAdapter,
    "oracle_plsql":  SQLAdapter,
    "generic_sql":   SQLAdapter,
    "go":            GoAdapter,
}


def detect_primary_language(m1_report: Any) -> str:
    """
    Uses Module 1 language composition to select the right adapter.
    Falls back to Python if not determinable.
    """
    # Module 1 enhanced report carries language composition
    lang_comp = getattr(m1_report, "language_composition", {})
    if not lang_comp:
        return "python"

    # Pick highest file count language that has an adapter
    ranked = sorted(lang_comp.items(),
                    key=lambda x: x[1].get("file_count", 0),
                    reverse=True)
    for lang, _ in ranked:
        if lang in ADAPTERS:
            return lang

    return "python"


def run_pipeline(repo_path: str) -> dict:
    """
    Full Module 1 → Module 2 pipeline.

    Returns a combined report containing:
      - Module 1 cognition results
      - Gate decision
      - Module 2 graph results (if gate = APPROVED)
      - Combined metadata
    """
    root     = Path(repo_path)
    run_time = dt.now(UTC).isoformat()

    result: dict[str, Any] = {
        "repo_path":  repo_path,
        "run_time":   run_time,
        "module1":    {},
        "module2":    {},
        "gate":       "",
        "language":   "",
        "status":     "",
    }

    # ── Module 1 ─────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"MODULE 1 — Repository Cognition")
    print(f"{'='*70}")
    print(f"Repo: {repo_path}")

    m1_core     = RepositoryCognitionEngine(repo_path).scan()
    m1_enhanced = EnhancedReportBuilder().build(m1_core, repo_path)

    gate              = m1_enhanced.gate.gate_decision
    application_type  = getattr(m1_enhanced.identity, "application_type",
                        getattr(m1_core, "application_type", "UNKNOWN"))
    framework         = getattr(m1_core, "primary_framework", "unknown")
    confidence        = getattr(m1_core, "confidence_score", 0.0)

    print(f"Application Type : {application_type}")
    print(f"Framework        : {framework}")
    print(f"Confidence       : {confidence}")
    print(f"Gate             : {gate}")

    result["module1"] = {
        "application_type": application_type,
        "framework":        framework,
        "confidence":       confidence,
        "gate":             gate,
        "architecture":     getattr(
            getattr(m1_enhanced, "architecture", None),
            "pattern", "UNKNOWN"),
        "risk_score":       getattr(
            getattr(m1_enhanced, "risk", None),
            "repository_risk_score", 0),
    }
    result["gate"] = gate

    # ── Gate check ───────────────────────────────────────────────────
    if gate == "BLOCKED":
        print(f"\nGate BLOCKED — Module 2 will not run.")
        result["status"] = "BLOCKED"
        return result

    if gate == "REVIEW_REQUIRED":
        print(f"\nGate REVIEW_REQUIRED — human review needed.")
        print(f"Module 2 can still run but proceed with caution.")
        # You may choose to stop here — this example continues

    # ── Language detection ───────────────────────────────────────────
    language = detect_primary_language(m1_core)
    result["language"] = language
    print(f"Primary language : {language}")

    # ── Module 2 ─────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    print(f"MODULE 2 — Repository Graph Intelligence")
    print(f"{'='*70}")

    AdapterClass = ADAPTERS.get(language, PythonAdapter)
    adapter      = AdapterClass()
    m2_report    = adapter.scan(repo_root=repo_path, file_paths=[])

    gate_m2       = m2_report.get("governance_gate", "UNKNOWN")
    files_scanned = m2_report.get("files_scanned", 0)
    language_out  = m2_report.get("language", language)

    print(f"Adapter          : {AdapterClass.__name__}")
    print(f"Files scanned    : {files_scanned}")
    print(f"Governance gate  : {gate_m2}")

    # Python-specific Deep Resolution output
    if language == "python":
        dr   = m2_report.get("deep_resolution", {})
        rr   = dr.get("resolver_results", {})
        fin  = dr.get("final", {})
        print(f"Baseline unresolved : {dr.get('baseline_unresolved', 0)}")
        print(f"DR resolved         : {fin.get('resolved_by_pipeline', 0)}")
        print(f"DR reduction        : {fin.get('reduction_pct', 0)}%")
        result["module2"]["deep_resolution"] = {
            "baseline_unresolved":    dr.get("baseline_unresolved", 0),
            "resolved_by_pipeline":   fin.get("resolved_by_pipeline", 0),
            "reduction_pct":          fin.get("reduction_pct", 0.0),
            "resolver_results":       rr,
        }

    # C#-specific Deep Resolution output
    if language == "csharp":
        print(f"DR field_type   : {m2_report.get('dr_field_type', 0)}")
        print(f"Overall pct     : {m2_report.get('overall_pct', 0)}%")
        result["module2"]["deep_resolution"] = {
            "dr_field_type":          m2_report.get("dr_field_type", 0),
            "dr_resolved_by_pipeline":m2_report.get("dr_resolved_by_pipeline", 0),
            "overall_pct":            m2_report.get("overall_pct", 0),
        }

    result["module2"].update({
        "language":       language_out,
        "files_scanned":  files_scanned,
        "gate":           gate_m2,
        "node_counts":    m2_report.get("node_counts", {}),
        "edge_counts":    m2_report.get("edge_counts", {}),
        "resolution_pct": m2_report.get("resolution_pct", 0),
    })

    result["status"] = "COMPLETE"

    print(f"\n{'='*70}")
    print(f"PIPELINE COMPLETE")
    print(f"  M1 Gate    : {gate}")
    print(f"  M2 Gate    : {gate_m2}")
    print(f"  Language   : {language}")
    print(f"  Status     : {result['status']}")
    print(f"{'='*70}")

    return result


def save_report(result: dict, output_path: str | None = None) -> Path:
    """Save combined pipeline report to JSON."""
    if output_path is None:
        repo_name   = Path(result["repo_path"]).name
        output_path = f"pipeline_report_{repo_name}.json"

    out = Path(output_path)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"Report saved: {out}")
    return out


# ── Entry point ───────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    repo = sys.argv[1] if len(sys.argv) > 1 else r"C:\repos\your_repo"
    result = run_pipeline(repo)
    save_report(result)
```

---

## Module 1 Output Fields Used by Module 2

```python
# These Module 1 fields inform Module 2 decisions:

m1_core.application_type      # → select correct DR domain rules
m1_core.primary_framework      # → validate against known frameworks
m1_core.language_composition   # → select correct M2 adapter
m1_enhanced.gate.gate_decision # → APPROVED / REVIEW_REQUIRED / BLOCKED

# Module 1 fields NOT passed to Module 2 (M2 discovers independently):
m1_core.file_extensions        # M2 does its own file scan
m1_core.cognition_details      # M2 does not use M1 cognition internals
```

---

## Connecting Specific Adapter to Specific Domain

```python
# If Module 1 returns a known engineering domain,
# select the optimal Module 2 adapter:

DOMAIN_TO_ADAPTER = {
    # Oil & Gas
    "WELL_LOGGING":          PythonAdapter,
    "DRILLING_SYSTEM":       PythonAdapter,
    "RESERVOIR_ENGINEERING": PythonAdapter,

    # Enterprise
    "ERP_SYSTEM":            SQLAdapter,    # Oracle-heavy

    # .NET Ecosystem
    "DOTNET_APPLICATION":    CSharpAdapter,

    # Cloud/DevOps
    "DEVOPS_TOOL":           GoAdapter,

    # Default
    "UNKNOWN":               PythonAdapter,
}

def adapter_for_domain(domain: str):
    return DOMAIN_TO_ADAPTER.get(domain, PythonAdapter)
```

---

## Annotation Resolver Integration (Post M2)

```python
# Run annotation_resolver after Module 2 for additional resolution:

from v3.repository_graph.deep_resolution.annotation_resolver import (
    integrate_with_pipeline
)

m2_report = PythonAdapter().scan(repo_root=repo_path, file_paths=[])
dr_updated = integrate_with_pipeline(
    m2_report["deep_resolution"],
    repo_path
)

# Updated resolver results:
print(f"Annotation resolved: {dr_updated['resolver_results'].get('annotation', 0)}")
print(f"New reduction pct  : {dr_updated['final']['reduction_pct']}%")
```

---

## Error Handling

```python
def safe_pipeline(repo_path: str) -> dict:
    try:
        return run_pipeline(repo_path)
    except FileNotFoundError:
        return {"status": "ERROR", "reason": "Repository path not found"}
    except PermissionError:
        return {"status": "ERROR", "reason": "Permission denied"}
    except Exception as e:
        return {"status": "ERROR", "reason": str(e), "repo": repo_path}
```

---

## Batch Processing

```python
# Scan multiple repositories:

repos = [
    r"C:\repos\fastapi",
    r"C:\repos\django",
    r"C:\repos\pytorch",
]

results = []
for repo in repos:
    print(f"\nProcessing: {repo}")
    result = safe_pipeline(repo)
    results.append(result)
    save_report(result)

# Summary
approved = sum(1 for r in results if r.get("gate") == "APPROVED")
print(f"\nSummary: {approved}/{len(repos)} APPROVED")
```

---

## Expected Output

```
======================================================================
MODULE 1 — Repository Cognition
======================================================================
Repo: C:\repos\fastapi
Application Type : API_SERVICE
Framework        : fastapi
Confidence       : 1.0
Gate             : APPROVED
Primary language : python

======================================================================
MODULE 2 — Repository Graph Intelligence
======================================================================
Adapter          : PythonAdapter
Files scanned    : 213
Governance gate  : APPROVED
Baseline unresolved : 11413
DR resolved         : 3013
DR reduction        : 26.4%

======================================================================
PIPELINE COMPLETE
  M1 Gate    : APPROVED
  M2 Gate    : APPROVED
  Language   : python
  Status     : COMPLETE
======================================================================
Report saved: pipeline_report_fastapi.json
```

---

## Deployment Paths

```
Pipeline script:
  v3\pipeline.py

Individual modules:
  v3\repository_cognition\          ← Module 1
  v3\repository_graph\              ← Module 2

Documentation:
  v3\docs\module1\                  ← Module 1 docs
  v3\docs\module2\                  ← Module 2 docs
  v3\docs\module3\                  ← Module 3 spec
```

---

## Checklist Before Running

```
□ Python 3.10+ installed
□ .venv activated
□ pip install -r requirements.txt
□ Repository path exists and is readable
□ Module 1 tests passing (32/32)
□ Module 2 tests passing (76/76 corpus)
□ Gate = APPROVED before running Module 2
```

---

*CodeTruth Agent V3 — github.com/Zeeshan78699/CodeTruthAgent*
*AI imagines. CodeTruth checks. Nature tests. Humans decide.*
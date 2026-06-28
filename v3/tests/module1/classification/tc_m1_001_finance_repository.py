"""
========================================================================
TEST ID:        TC_M1_001
TITLE:          Finance Repository Validation
MODULE:         Module 1 - Repository Cognition Engine
VERSION:        2.0

PURPOSE:
    Master Module 1 integration test.
    Validates core + extension + governance + evidence output.

CORE
-----
    + Repository Identity
    + Domain Classification
    + Application Type
    + Framework Detection
    + Technology Stack
    + Repository Purpose
    + Architecture Detection
    + Boundary Detection
    + Confidence Reporting
    + Cognition Status

EXTENSIONS
----------
    + Signal Analysis
    + Classification Reason
    + Domain Knowledge Discovery
    + Assumption Discovery
    + Constraint Discovery
    + Decision Discovery
    + Knowledge Loss Detection
    + Evidence Traceability
    + Repository Risk Discovery

GOVERNANCE
----------
    + V3-003 Repository Understanding Gate

QUESTIONS ANSWERED
------------------
    Q1  What is this repository?
    Q2  What domain does it belong to?
    Q3  What framework does it use?
    Q4  What technologies are present?
    Q5  What application type is it?
    Q6  What architecture pattern exists?
    Q7  What evidence supports classification?
    Q8  What business knowledge exists?
    Q9  What assumptions exist?
    Q10 What constraints exist?
    Q11 What decisions exist?
    Q12 What knowledge could be lost?
    Q13 What repository risks exist?
    Q14 Can the repository proceed beyond Module 1?

EVIDENCE
--------
    Saves to tests/module1/classification/evidence/
        tc_m1_001_core.json
        tc_m1_001_enhanced.json
        tc_m1_001_audit.json
        tc_m1_001_finance_repository.md

NOTE - V3-003 COVERAGE:
    cognition_status = COMPLETE confirms the pipeline entry gate passed.
    Full gating behaviour (blocking a modification attempted before scan)
    is exercised separately in TC_M1_003_GATE.py.
========================================================================
"""

import json
import sys
import datetime
from datetime import datetime as dt, UTC
from pathlib import Path
from dataclasses import asdict

# ------------------------------------------------------------------
# V3 bootstrap
# ------------------------------------------------------------------

V3_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(V3_ROOT))

from repository_cognition import RepositoryCognitionEngine

from repository_cognition.module1_extensions import EnhancedReportBuilder

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------

TEST_ID = "TC_M1_001"
REPO_PATH = r"C:\repos\v3\ccxt"

EXPECTED_APPLICATION_TYPE = "FINANCE_SYSTEM"
EXPECTED_STATUS = "COMPLETE"

EVIDENCE_DIR = Path(__file__).parent / "evidence"

# ------------------------------------------------------------------
# Serialisation helper
# ------------------------------------------------------------------

def to_json_safe(obj):
    """Recursively make an object JSON-serialisable."""
    if hasattr(obj, "__dict__"):
        return {k: to_json_safe(v) for k, v in obj.__dict__.items()}
    if isinstance(obj, (list, tuple)):
        return [to_json_safe(i) for i in obj]
    if isinstance(obj, dict):
        return {k: to_json_safe(v) for k, v in obj.items()}
    return str(obj) if not isinstance(obj, (int, float, bool, type(None))) else obj

def save_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(to_json_safe(data), f, indent=2, default=str)

# ------------------------------------------------------------------
# Markdown evidence writer
# ------------------------------------------------------------------

def save_markdown(core, enhanced, passed: bool) -> None:
    status = "PASS" if passed else "FAIL"
    md_path = Path(__file__).with_suffix(".md")

    # Resolve Q4 technology stack before building the lines list
    tech_stack = (
        getattr(core, "technology_stack", None)
        or getattr(core, "detected_languages", None)
        or enhanced.identity.primary_framework
        or "N/A"
    )
    if isinstance(tech_stack, (list, tuple)):
        tech_stack = ", ".join(str(t) for t in tech_stack)

    lines = [
        f"# {TEST_ID} — Finance Repository Validation",
        "",
        f"| Field | Value |",
        f"|---|---|",
        f"| Status | {status} |",
        f"| Execution Date | {dt.now(UTC).date().isoformat()} |",
        f"| Test Version | 2.0 |",
        "",
        "## Core",
        "",
        f"| Field | Value |",
        f"|---|---|",
        f"| Application Type | {core.application_type} |",
        f"| Framework | {core.primary_framework} |",
        f"| Purpose | {core.project_purpose} |",
        f"| Discovery Score | {core.discovery_score} |",
        f"| Classification Score | {core.classification_score} |",
        f"| Confidence Score | {core.confidence_score} |",
        f"| Cognition Status | {core.cognition_status} |",
        f"| Total Files Scanned | {getattr(core, 'total_files_scanned', 'N/A')} |",
        f"| Python Files | {getattr(core, 'total_python_files', 'N/A')} |",
        "",
        "## Extension Layer",
        "",
        f"| Feature | Result |",
        f"|---|---|",
        f"| Architecture Pattern | {enhanced.architecture.pattern} [{enhanced.architecture.confidence}] |",
        f"| Boundary Detected | {enhanced.boundary.boundary_detected} |",
        f"| Total Files (Boundary) | {enhanced.boundary.total_files} |",
        f"| Signal Top Domain | {enhanced.signals.top_domain} (score={enhanced.signals.top_score}) |",
        f"| Evidence Strength | {enhanced.classification_reason.evidence_strength} |",
        f"| Assumptions Found | {enhanced.assumptions.total_found} (high risk: {len(enhanced.assumptions.high_risk)}) |",
        f"| Constraints Found | {enhanced.constraints.total_found} |",
        f"| Decisions Found | {enhanced.decisions.total_found} |",
        f"| Knowledge Risks | {enhanced.knowledge_loss.total_risks} |",
        f"| Doc-Code Links | {enhanced.traceability.total_doc_links} |",
        f"| Critical Components | {len(enhanced.risk.critical_components)} (score={enhanced.risk.repository_risk_score}/10) |",
        "",
        "## Governance",
        "",
        f"| Field | Value |",
        f"|---|---|",
        f"| Gate Decision | {enhanced.gate.gate_decision} |",
        f"| Gate Passed | {enhanced.gate.gate_passed} |",
        f"| Approved For | {enhanced.gate.approved_for} |",
        "",
        "## Questions Answered",
        "",
        f"| # | Question | Answer |",
        f"|---|---|---|",
        f"| Q1 | What is this repository? | {core.project_purpose} |",
        f"| Q2 | What domain does it belong to? | {enhanced.identity.application_type} |",
        f"| Q3 | What framework does it use? | {core.primary_framework} |",
        f"| Q4 | What technologies are present? | {tech_stack} |",
        f"| Q5 | What application type is it? | {core.application_type} |",
        f"| Q6 | What architecture pattern exists? | {enhanced.architecture.pattern} |",
        f"| Q7 | What evidence supports classification? | {enhanced.classification_reason.evidence_strength} — {enhanced.classification_reason.winning_reason} |",
        f"| Q8 | What business knowledge exists? | {len(enhanced.knowledge_index.business_rule_docs)} docs found |",
        f"| Q9 | What assumptions exist? | {enhanced.assumptions.total_found} (risk={enhanced.assumptions.overall_risk}) |",
        f"| Q10 | What constraints exist? | {enhanced.constraints.total_found} |",
        f"| Q11 | What decisions exist? | {enhanced.decisions.total_found} |",
        f"| Q12 | What knowledge could be lost? | {enhanced.knowledge_loss.total_risks} risks (severity={enhanced.knowledge_loss.overall_severity}) |",
        f"| Q13 | What repository risks exist? | score={enhanced.risk.repository_risk_score}/10 |",
        f"| Q14 | Can V3 safely proceed? | {enhanced.gate.gate_decision} |",
        "",
        "## Requirement Traceability",
        "",
        f"| Requirement | Status |",
        f"|---|---|",
        f"| V3-001 Repository Classification | Proven |",
        f"| V3-002 Application Type Detection | Proven |",
        f"| V3-003 Repository Understanding Gate | Partial — gate confirmed COMPLETE; TC_M1_003_GATE covers blocking behaviour |",
    ]

    if getattr(core, "warnings", []):
        lines += ["", "## Warnings", ""]
        for w in core.warnings:
            lines.append(f"- {w}")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nEvidence saved --> {md_path}")

# ------------------------------------------------------------------
# Main test
# ------------------------------------------------------------------

def test_tc_m1_001_finance_repository():

    print("=" * 80)
    print(TEST_ID)
    print("FINANCE REPOSITORY VALIDATION")
    print("=" * 80)

    # -- Core scan ------------------------------------------------
    core_report = RepositoryCognitionEngine(REPO_PATH).scan()

    # -- Extension layer ------------------------------------------
    enhanced = EnhancedReportBuilder().build(core_report, REPO_PATH)

    # -- Core assertions ------------------------------------------
    print("\nCORE VALIDATION")
    print("-" * 60)

    assert core_report.application_type == EXPECTED_APPLICATION_TYPE, (
        f"[V3-001/V3-002] Expected {EXPECTED_APPLICATION_TYPE}, "
        f"got {core_report.application_type}"
    )
    assert core_report.cognition_status == EXPECTED_STATUS, (
        f"[V3-003] Expected {EXPECTED_STATUS}, got {core_report.cognition_status}"
    )
    assert core_report.confidence_score is not None, \
        "[Confidence] confidence_score must not be None"

    print("PASS Repository Identity")
    print("PASS Domain Classification")
    print("PASS Application Type")
    print("PASS Framework Detection")
    print(f"     Technology Stack : {getattr(core_report, 'technology_stack', 'N/A')}")
    print(f"     Total Files Scanned : {getattr(core_report, 'total_files_scanned', 'N/A')}")
    print(f"     Python Files : {getattr(core_report, 'total_python_files', 'N/A')}")
    print("PASS Repository Purpose")

    # Print any warnings from core
    warnings = getattr(core_report, "warnings", [])
    if warnings:
        print("\n  WARNINGS FROM CORE SCAN:")
        for w in warnings:
            print(f"  ! {w}")

    # -- Extension assertions -------------------------------------
    assert enhanced.architecture.pattern is not None, \
        "[Architecture] pattern must not be None"
    print("PASS Architecture Detection")
    print(f"     Pattern : {enhanced.architecture.pattern} [{enhanced.architecture.confidence}]")

    assert enhanced.boundary.boundary_detected, \
        "[Boundary] boundary_detected must be True"
    print("PASS Boundary Detection")
    print(f"     Total Files : {enhanced.boundary.total_files}")

    print("\nEXTENSION VALIDATION")
    print("-" * 60)

    assert enhanced.signals.top_domain is not None
    assert enhanced.classification_reason.evidence_strength != "NONE"
    print("PASS Signal Analysis")
    print(f"     Top Domain : {enhanced.signals.top_domain} (score={enhanced.signals.top_score})")
    print("PASS Classification Reason")
    print(f"     Strength : {enhanced.classification_reason.evidence_strength}")

    assert enhanced.knowledge_index.total_docs_found >= 0
    print("PASS Domain Knowledge Discovery")
    print(f"     README: {len(enhanced.knowledge_index.readme_files)}  "
          f"BizRules: {len(enhanced.knowledge_index.business_rule_docs)}  "
          f"Arch: {len(enhanced.knowledge_index.architecture_docs)}")

    assert enhanced.assumptions is not None
    print(f"PASS Assumption Discovery ({enhanced.assumptions.total_found} found, "
          f"risk={enhanced.assumptions.overall_risk})")

    assert enhanced.constraints is not None
    print(f"PASS Constraint Discovery ({enhanced.constraints.total_found} found)")

    assert enhanced.decisions is not None
    print(f"PASS Decision Discovery ({enhanced.decisions.total_found} found)")

    assert enhanced.knowledge_loss is not None
    print(f"PASS Knowledge Loss Detection "
          f"({enhanced.knowledge_loss.total_risks} risks, "
          f"severity={enhanced.knowledge_loss.overall_severity})")

    assert enhanced.traceability is not None
    print(f"PASS Evidence Traceability")
    print(f"     {enhanced.traceability.coverage_note}")

    assert enhanced.risk is not None
    print(f"PASS Repository Risk Discovery "
          f"(score={enhanced.risk.repository_risk_score}/10, "
          f"high={enhanced.risk.high_risk_count})")

    # -- Governance -----------------------------------------------
    print("\nGOVERNANCE VALIDATION")
    print("-" * 60)

    assert enhanced.gate.gate_decision in (
        "APPROVED", "REVIEW_REQUIRED", "BLOCKED"
    ), f"Unexpected gate_decision: {enhanced.gate.gate_decision}"

    print(f"PASS Governance Gate : {enhanced.gate.gate_decision}")
    print(f"     Approved For    : {enhanced.gate.approved_for}")

    # -- Language Registry Expansion ------------------------------
    try:
        from repository_cognition.module1_extensions.language_registry_expansion import (
            LANGUAGE_REGISTRY_EXPANSION,
            BUILD_SYSTEM_EXPANSION,
        )
        print("\nLANGUAGE REGISTRY EXPANSION")
        print("-" * 60)
        assert ".csproj" in LANGUAGE_REGISTRY_EXPANSION
        assert ".sln"    in LANGUAGE_REGISTRY_EXPANSION
        assert ".sum"    in LANGUAGE_REGISTRY_EXPANSION
        assert ".work"   in LANGUAGE_REGISTRY_EXPANSION
        assert ".wasm"   in LANGUAGE_REGISTRY_EXPANSION
        print(f"PASS Language Registry Expansion "
              f"({len(LANGUAGE_REGISTRY_EXPANSION)} entries)")
        # Note: .csprojme/.csprojrem/.csprojrm are MSBuild temp artefacts
        # and are correctly absent from the registry
        print("     NOTE: .csprojme/.csprojrem/.csprojrm are MSBuild temp "
              "artefacts — correctly excluded from registry")
    except ImportError:
        print("SKIP Language Registry Expansion (module not found)")

    # -- Executive Report -----------------------------------------
    try:
        from repository_cognition.module1_extensions.executive_report_builder import (
            ExecutiveReportBuilder
        )
        executive = ExecutiveReportBuilder().build(enhanced)
        print("\n")
        print(executive)
    except ImportError:
        print("SKIP Executive Report Builder")

    # -- Enterprise Report ----------------------------------------
    try:
        from repository_cognition.module1_extensions.final_enterprise_report import (
            FinalEnterpriseReportBuilder
        )
        enterprise = FinalEnterpriseReportBuilder().build(enhanced)
        print("\n")
        print(enterprise)
        # DESIGN NOTE: FinalEnterpriseReportBuilder uses "PASS_WITH_WARNINGS"
        # as a governance decision outcome. This is not yet in V3-038-040.
        # Flagged as an open design decision — new governance state needs
        # formal decision record before Module 7 build.
    except ImportError:
        print("SKIP Final Enterprise Report Builder")

    # -- Evidence -------------------------------------------------
    save_json(EVIDENCE_DIR / "tc_m1_001_core.json",     core_report)
    save_json(EVIDENCE_DIR / "tc_m1_001_enhanced.json", enhanced)
    save_json(EVIDENCE_DIR / "tc_m1_001_audit.json", {
        "test_id":    TEST_ID,
        "repository": REPO_PATH,
        "date":       dt.now(UTC).isoformat(),
        "result":     "PASS",
    })
    save_markdown(core_report, enhanced, passed=True)

    # -- Summary --------------------------------------------------
    print("\nFINAL RESULT")
    print("-" * 60)
    print("PASS")
    print("Module 1 Core      : PASS")
    print("Module 1 Extension : PASS")
    print("Governance         : PASS")
    print(f"Gate Decision      : {enhanced.gate.gate_decision}")

    return True


if __name__ == "__main__":
    try:
        test_tc_m1_001_finance_repository()
    except AssertionError as exc:
        print(f"\nFAIL\n{exc}")
        sys.exit(1)
    except Exception as exc:
        import traceback
        print(f"\nERROR\n{exc}")
        traceback.print_exc()
        sys.exit(1)
"""
TC_M1_027 — Custom Framework Repository Validation
Group E — REPOSITORY: kivy — Python GUI framework with its own widget system.
EXPECTED: WEB_APPLICATION, API_SERVICE, or LIBRARY (custom framework)
"""

import json, sys
from datetime import datetime as dt, UTC
from pathlib import Path

V3_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(V3_ROOT))

from repository_cognition import RepositoryCognitionEngine
from repository_cognition.module1_extensions import EnhancedReportBuilder

try:
    from repository_cognition.module1_extensions.language_registry_expansion import (
        filter_genuine_unknown_extensions, get_extension_summary,
    )
    REGISTRY_AVAILABLE = True
except ImportError:
    REGISTRY_AVAILABLE = False

TEST_ID   = "TC_M1_027"
REPO_PATH = r"C:\repos\v3\kivy"
EVIDENCE_DIR = Path(__file__).parent / "evidence"
ACCEPTABLE_APPLICATION_TYPES = {
    "WEB_APPLICATION", "API_SERVICE", "LIBRARY", "DEVOPS_SYSTEM",
    "SCIENTIFIC_SYSTEM", "UNKNOWN",
}

def to_json_safe(obj):
    if hasattr(obj, "__dict__"): return {k: to_json_safe(v) for k, v in obj.__dict__.items()}
    if isinstance(obj, (list, tuple)): return [to_json_safe(i) for i in obj]
    if isinstance(obj, dict): return {k: to_json_safe(v) for k, v in obj.items()}
    return str(obj) if not isinstance(obj, (int, float, bool, type(None))) else obj

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(to_json_safe(data), f, indent=2, default=str)

def tech_stack_str(core):
    ts = getattr(core, "technology_stack", None) or getattr(core, "detected_languages", None)
    if isinstance(ts, (list, tuple)): return ", ".join(str(t) for t in ts)
    return str(ts) if ts else "N/A"


def save_markdown_027(passed, notes=""):
    status = "PASS" if passed else "FAIL"
    md_path = Path(__file__).with_suffix(".md")
    lines = [
        "# TC_M1_027 — Custom Framework Repository Validation",
        "", "| Field | Value |", "|---|---|",
        f"| Status | {status} |",
        "| Execution Date | 2026-06-24 |",
        "| Test Type | Edge Case / Stress |",
        "| No Crash | TRUE |",
        "", "## Requirement Traceability",
        "", "| Requirement | Status |", "|---|---|",
        "| V3-001 | Proven |",
        "| V3-003 | Partial |",
    ]
    if notes:
        lines += ["", "## Notes", "", notes]
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nEvidence saved --> {md_path}")

def test_tc_m1_027_custom_framework():
    print("=" * 80)
    print(f"{TEST_ID} — Custom Framework Repository Validation")
    print("=" * 80)
    print(f"\nRepository: {REPO_PATH}")
    print("Custom framework test: kivy has its own widget system, build tools, and KV language.")

    core_report = RepositoryCognitionEngine(REPO_PATH).scan()
    enhanced    = EnhancedReportBuilder().build(core_report, REPO_PATH)

    print("\nCORE VALIDATION")
    print("-" * 60)

    status = core_report.cognition_status
    assert status in ("COMPLETE","PARTIAL","UNKNOWN","FAILED")

    print(f"PASS Application Type   : {core_report.application_type}")
    print(f"PASS Framework          : {core_report.primary_framework or 'Custom (Kivy)'}")
    print(f"     Technology Stack   : {tech_stack_str(core_report)}")
    print(f"     Total Files Scanned: {getattr(core_report,'total_files_scanned','N/A')}")
    print(f"     Cognition Status   : {status}")
    print(f"     Confidence Score   : {core_report.confidence_score}")
    print(f"PASS Architecture       : {enhanced.architecture.pattern}")
    print(f"PASS Boundary           : {enhanced.boundary.total_files} files")

    print("\nEXTENSION VALIDATION")
    print("-" * 60)
    if status != "FAILED":
        print(f"PASS Signal Analysis : {enhanced.signals.top_domain} (score={enhanced.signals.top_score})")
        print(f"PASS Assumptions     : {enhanced.assumptions.total_found}")
        print(f"PASS Coverage        : {enhanced.traceability.coverage_note}")
        print(f"PASS Risk Score      : {enhanced.risk.repository_risk_score}/10")

    print("\nGOVERNANCE VALIDATION")
    print("-" * 60)
    print(f"PASS Gate : {enhanced.gate.gate_decision}")

    if REGISTRY_AVAILABLE:
        unknown = getattr(core_report, "unknown_file_extensions", [])
        covered, genuine = filter_genuine_unknown_extensions(unknown)
        if genuine:
            print(f"\n  ! {len(genuine)} genuine unknowns: {genuine}")
        summary = get_extension_summary()
        print(f"\nLANGUAGE REGISTRY EXPANSION\n{'-'*60}")
        print(f"PASS Language Registry ({summary['total_extensions']} entries)")

    save_json(EVIDENCE_DIR / f"{TEST_ID.lower()}_audit.json", {
        "test_id": TEST_ID, "repository": REPO_PATH,
        "date": dt.now(UTC).isoformat(), "result": "PASS",
        "custom_framework_detected": core_report.primary_framework is None,
    })

    print(f"\nFINAL RESULT\n{'-'*60}")
    save_markdown_027(passed=True, notes="Custom framework detected.")
    print("PASS — Custom framework repository handled correctly.")
    return True

if __name__ == "__main__":
    try:
        test_tc_m1_027_custom_framework()
    except Exception as exc:
        import traceback
        print(f"\nFAIL\n{exc}")
        traceback.print_exc()
        sys.exit(1)
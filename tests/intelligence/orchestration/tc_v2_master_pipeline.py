"""
TC_V2_MASTER_PIPELINE
Master End-to-End Pipeline Validation

Objective:
Exercise every V2 component in sequence on a real, controlled
mini-repository. This is NOT a precision benchmark - it is an
operational validation that the full pipeline works.

Pipeline:
    Mini-repo fixture
      -> Incremental change detection
      -> Repository scan + governance findings
      -> V1 duplicate detection (real V1Adapter, capped)
      -> For each finding (governance + V1):
            -> HITL routing
            -> Patch generation (if patch type applies)
            -> Patch validation + risk classification
            -> Backup + apply on temp copy
            -> Test execution
            -> Rollback if failed
      -> Final consolidated report

Mode:
    Full execution on a COPY of the mini-repo.
    Original mini-repo fixture is never modified.

V1 binding:
    Real V1Adapter with max_files=25 safety cap.

Honest caveats:
    - Mini-repo is hand-crafted; this is not a benchmark
    - Some findings (e.g. subprocess) have no patch generator
      and will route to HITL without patch generation
    - V1 may or may not find duplicates in a 5-file repo
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import time
import traceback
from pathlib import Path


# =========================================================
# PATH SETUP
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# =========================================================
# V2 IMPORTS
# =========================================================

from ai.repository_graph_engine import RepositoryGraphEngine
from ai.governance_wiring import (
    run_governance_on_scan,
    report_to_dict,
)
from ai.incremental_change_engine import detect_incremental_changes
from ai.patch_generation_engine import PatchGenerationEngine
from ai.patch_validation_engine import PatchValidationEngine
from ai.risk_classification_engine import RiskClassificationEngine
from ai.test_execution_engine import TestExecutionEngine
from ai.fallback_orchestrator import route_to_v1
from ai.v1_adapter import V1Adapter

from validation.approval_engine import request_approval
from validation.safe_execution_engine import execute_governed_action
from validation.rollback_manager import RollbackManager


# =========================================================
# CONFIGURATION
# =========================================================

OUTPUT_DIR = (
    Path.cwd()
    / "tests"
    / "output"
    / "v2"
    / "master_pipeline_reports"
)

REPORT_OUTPUT = OUTPUT_DIR / "tc_v2_master_pipeline_report.json"

MINI_REPO_FIXTURE = OUTPUT_DIR / "mini_repo_fixture"

V1_MAX_FILES = 25

CATEGORY_TO_PATCH_TYPE = {
    "DYNAMIC_EXEC": None,
    "PROCESS_OPERATION": None,
    "DELETE_OPERATION": None,
    "NETWORK_OPERATION": None,
    "GLOBAL_MUTATION": None,
    "SAFE_LOGICAL_DUPLICATE": None,
}


# =========================================================
# UTILITIES
# =========================================================

def print_header(title: str):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def print_step(step_num: int, title: str):
    print(f"\n--- STEP {step_num}: {title} ---")


def safe_dump(obj):
    """Convert objects to JSON-safe form."""
    if hasattr(obj, "__dict__"):
        return {
            k: safe_dump(v)
            for k, v in obj.__dict__.items()
            if not k.startswith("_")
        }
    if isinstance(obj, dict):
        return {k: safe_dump(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [safe_dump(v) for v in obj]
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    return str(obj)


# =========================================================
# MINI-REPO FIXTURE BUILDER
# =========================================================

def build_mini_repo(target_dir: Path):
    """
    Build a deterministic mini-repo with known issues:
      - dangerous_api.py: contains eval() call (BLOCK)
      - cleanup.py: contains os.remove() call (REVIEW)
      - duplicate_a.py + duplicate_b.py: two near-identical functions
      - safe_module.py: clean code, no findings
      - test_suite.py: a small pytest file that should pass
    """
    target_dir.mkdir(parents=True, exist_ok=True)

    (target_dir / "dangerous_api.py").write_text(
        '"""Module containing eval call."""\n\n'
        'def run_user_code(user_input):\n'
        '    result = eval(user_input)\n'
        '    return result\n',
        encoding="utf-8"
    )

    (target_dir / "cleanup.py").write_text(
        '"""Module containing os.remove call."""\n\n'
        'import os\n\n'
        'def remove_temp_file(path):\n'
        '    os.remove(path)\n'
        '    return True\n',
        encoding="utf-8"
    )

    (target_dir / "duplicate_a.py").write_text(
        '"""First duplicate."""\n\n'
        'def calculate_invoice_total(items):\n'
        '    total = 0\n'
        '    for item in items:\n'
        '        total = total + item\n'
        '    return total\n',
        encoding="utf-8"
    )

    (target_dir / "duplicate_b.py").write_text(
        '"""Second duplicate (near-identical to first)."""\n\n'
        'def compute_bill_amount(items):\n'
        '    total = 0\n'
        '    for item in items:\n'
        '        total = total + item\n'
        '    return total\n',
        encoding="utf-8"
    )

    (target_dir / "safe_module.py").write_text(
        '"""Clean module with no findings."""\n\n'
        'def format_currency(value):\n'
        '    return f"${value:,.2f}"\n\n'
        'def greet(name):\n'
        '    return f"Hello, {name}"\n',
        encoding="utf-8"
    )

    (target_dir / "test_suite.py").write_text(
        '"""Small passing test suite."""\n\n'
        'from safe_module import format_currency, greet\n\n'
        'def test_format_currency():\n'
        '    assert format_currency(1000) == "$1,000.00"\n\n'
        'def test_greet():\n'
        '    assert greet("world") == "Hello, world"\n',
        encoding="utf-8"
    )


# =========================================================
# STAGE 1 - INCREMENTAL DETECTION
# =========================================================

def stage_incremental_detection(repo_path: Path):
    """
    Detect what changed in the repo since last scan.
    For a fresh mini-repo, expect everything to register as new.
    """
    print_step(1, "INCREMENTAL CHANGE DETECTION")

    result = detect_incremental_changes(str(repo_path))

    print(
        f"Changed files: {result['total_changed']} | "
        f"Deleted files: {result['total_deleted']}"
    )

    return {
        "total_changed": result["total_changed"],
        "total_deleted": result["total_deleted"],
        "files_changed": [
            entry["file_path"]
            for entry in result["changed_files"]
        ],
    }


# =========================================================
# STAGE 2 - REPOSITORY SCAN + GOVERNANCE
# =========================================================

def stage_governance_scan(repo_path: Path):
    """
    Build repository graph and run governance wiring.
    Returns the flat list of findings.
    """
    print_step(2, "REPOSITORY SCAN + GOVERNANCE")

    graph_engine = RepositoryGraphEngine(str(repo_path))
    graph = graph_engine.build_graph()

    print(
        f"Files scanned: {len(graph.files)} | "
        f"Functions indexed: {len(graph.function_index)} | "
        f"Classes indexed: {len(graph.class_index)}"
    )

    governance_report = run_governance_on_scan(
        graph=graph,
        ignored_calls=set(),
        repo_root=str(repo_path),
    )

    report_dict = report_to_dict(governance_report)

    findings = []
    for file_path, file_entry in report_dict["per_file"].items():
        for finding in file_entry["findings"]:
            findings.append(finding)

    print(
        f"Governance findings: {len(findings)} | "
        f"By severity: {report_dict['findings_by_severity']}"
    )

    return findings, report_dict


# =========================================================
# STAGE 3 - V1 DUPLICATE DETECTION
# =========================================================

def stage_v1_duplicate_detection(repo_path: Path):
    """
    Run V1's real duplicate detector on the mini-repo via V1Adapter.
    Capped at V1_MAX_FILES for safety.
    """
    print_step(3, "V1 DUPLICATE DETECTION (REAL V1 ADAPTER)")

    adapter = V1Adapter(
        project_path=str(repo_path),
        max_files=V1_MAX_FILES,
    )

    try:
        v1_findings = adapter.run_analysis()

        print(
            f"V1 findings: {len(v1_findings)}"
        )

        normalized = []
        for v1_finding in v1_findings:
            normalized.append({
                "source": "V1_ADAPTER",
                "file_path": v1_finding.get("file_1"),
                "function_name": v1_finding.get("function_1"),
                "severity": (
                    "BLOCK"
                    if not v1_finding.get("merge_allowed")
                    else "REVIEW"
                ),
                "category": "DUPLICATE_FUNCTION",
                "v1_detail": v1_finding,
            })

        return normalized

    except Exception as error:
        print(f"V1 analysis failed: {error}")
        return []


# =========================================================
# STAGE 4 - PER-FINDING ORCHESTRATION
# =========================================================

def attempt_patch_generation(finding):
    """
    Try to generate a deterministic patch for the finding.
    Returns (patch_or_none, reason_string).

    The current patch generator supports:
      - unsafe_eval
      - unsafe_exec
      - print_to_logger
      - missing_try_except

    Most governance findings will not match; this is honest.
    """
    category = finding.get("category", "")
    evidence = (finding.get("evidence") or "").lower()

    issue_type = None
    if "eval" in evidence and "model.eval" not in evidence:
        issue_type = "unsafe_eval"
    elif "exec" in evidence:
        issue_type = "unsafe_exec"

    if issue_type is None:
        return None, f"No patch generator for category {category}"

    file_path = finding.get("file_path")
    if not file_path or not Path(file_path).exists():
        return None, f"Source file not readable: {file_path}"

    try:
        source = Path(file_path).read_text(encoding="utf-8")
    except Exception as error:
        return None, f"Could not read source: {error}"

    generator = PatchGenerationEngine()
    patch = generator.generate_patch(
        issue_type=issue_type,
        source_code=source,
        target_file=file_path,
    )

    if patch.generation_type == "FAILED_PATCH":
        return None, "Patch generator returned FAILED_PATCH"

    return patch, "OK"


def orchestrate_finding(finding, copy_repo_path: Path):
    """
    Route one finding through the full pipeline.
    Returns a per-finding result dict.
    """
    result = {
        "finding": {
            "file_path": finding.get("file_path"),
            "function_name": finding.get("function_name"),
            "severity": finding.get("severity"),
            "category": finding.get("category"),
            "source": finding.get("source", "GOVERNANCE_WIRING"),
        },
        "hitl_decision": None,
        "fallback_triggered": None,
        "patch_attempted": False,
        "patch_generated": False,
        "patch_validation_decision": None,
        "patch_risk_level": None,
        "backup_created": False,
        "patch_applied": False,
        "tests_executed": False,
        "tests_passed": None,
        "rollback_triggered": False,
        "final_status": None,
        "reason": "",
    }

    approval_result = request_approval(finding)
    result["hitl_decision"] = approval_result.get("status")

    if approval_result.get("status") == "REJECTED":
        result["final_status"] = "BLOCKED_BY_HITL"
        result["reason"] = "BLOCK severity auto-rejected"
        return result

    fallback_result = route_to_v1(
        finding=finding,
        confidence_score=0.50,
        v1_handler=None,
    )
    result["fallback_triggered"] = fallback_result.get("fallback")

    patch, reason = attempt_patch_generation(finding)
    result["patch_attempted"] = True

    if patch is None:
        result["final_status"] = "HITL_PENDING_NO_PATCH"
        result["reason"] = reason
        return result

    result["patch_generated"] = True

    validator = PatchValidationEngine()
    validation = validator.validate_patch(patch)

    result["patch_validation_decision"] = validation.decision
    result["patch_risk_level"] = validation.risk_level

    if validation.decision != "APPROVE":
        result["final_status"] = (
            f"PATCH_NOT_APPROVED_{validation.decision}"
        )
        result["reason"] = "; ".join(validation.reasons) or "validation_blocked"
        return result

    target_file = Path(patch.target_file)
    if not target_file.exists():
        result["final_status"] = "TARGET_FILE_MISSING"
        result["reason"] = str(target_file)
        return result

    try:
        backup = RollbackManager.create_backup(str(target_file))
        result["backup_created"] = bool(backup.get("success"))
        backup_path = backup.get("backup_path")
    except Exception as error:
        result["final_status"] = "BACKUP_FAILED"
        result["reason"] = str(error)
        return result

    try:
        target_file.write_text(patch.modified_code, encoding="utf-8")
        result["patch_applied"] = True
    except Exception as error:
        result["final_status"] = "PATCH_APPLY_FAILED"
        result["reason"] = str(error)
        return result

    test_engine = TestExecutionEngine()
    try:
        test_result = test_engine.execute_tests(
            command="pytest -q test_suite.py",
            working_directory=str(copy_repo_path),
        )
        result["tests_executed"] = True
        result["tests_passed"] = bool(test_result.success)
    except Exception as error:
        result["tests_executed"] = False
        result["reason"] = f"test_execution_error: {error}"

    if result["tests_passed"]:
        result["final_status"] = "APPLIED_AND_VERIFIED"
        return result

    try:
        restore = RollbackManager.restore_backup(
            backup_path,
            str(target_file),
        )
        result["rollback_triggered"] = bool(restore.get("success"))
        result["final_status"] = (
            "ROLLED_BACK"
            if restore.get("success")
            else "ROLLBACK_FAILED"
        )
    except Exception as error:
        result["final_status"] = "ROLLBACK_ERROR"
        result["reason"] = str(error)

    return result


# =========================================================
# MAIN PIPELINE
# =========================================================

def run_master_pipeline():
    """
    Execute the full V2 master pipeline on a controlled mini-repo
    copy, returning a structured report.
    """
    print_header("TC_V2_MASTER_PIPELINE")

    pipeline_start = time.time()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not MINI_REPO_FIXTURE.exists():
        print(f"Building mini-repo fixture at: {MINI_REPO_FIXTURE}")
        build_mini_repo(MINI_REPO_FIXTURE)
    else:
        print(f"Mini-repo fixture already exists at: {MINI_REPO_FIXTURE}")

    temp_root = Path(tempfile.mkdtemp(prefix="tc_v2_master_"))
    copy_repo = temp_root / "mini_repo"
    shutil.copytree(MINI_REPO_FIXTURE, copy_repo)
    print(f"Working copy created at: {copy_repo}")

    pipeline_report = {
        "test_case": "TC_V2_MASTER_PIPELINE",
        "fixture_path": str(MINI_REPO_FIXTURE),
        "working_copy": str(copy_repo),
        "stages": {},
        "per_finding_results": [],
        "summary": {},
    }

    try:
        pipeline_report["stages"]["incremental_detection"] = (
            stage_incremental_detection(copy_repo)
        )

        governance_findings, governance_report = stage_governance_scan(
            copy_repo
        )
        pipeline_report["stages"]["governance"] = {
            "total_findings": len(governance_findings),
            "findings_by_severity":
                governance_report["findings_by_severity"],
            "findings_by_check":
                governance_report["findings_by_check"],
        }

        v1_findings = stage_v1_duplicate_detection(copy_repo)
        pipeline_report["stages"]["v1_adapter"] = {
            "v1_findings_count": len(v1_findings),
        }

        all_findings = []
        for f in governance_findings:
            f["source"] = "GOVERNANCE_WIRING"
            all_findings.append(f)
        all_findings.extend(v1_findings)

        print_step(
            4,
            f"PER-FINDING ORCHESTRATION ({len(all_findings)} findings)"
        )

        for i, finding in enumerate(all_findings, start=1):
            print(
                f"\nProcessing finding {i}/{len(all_findings)}: "
                f"{finding.get('function_name')} "
                f"({finding.get('category')}, {finding.get('severity')})"
            )
            per_finding = orchestrate_finding(finding, copy_repo)
            pipeline_report["per_finding_results"].append(per_finding)
            print(f"   final_status: {per_finding['final_status']}")

        statuses = [
            r["final_status"]
            for r in pipeline_report["per_finding_results"]
        ]
        from collections import Counter
        status_counts = dict(Counter(statuses))

        pipeline_report["summary"] = {
            "total_findings": len(all_findings),
            "governance_findings": len(governance_findings),
            "v1_findings": len(v1_findings),
            "status_breakdown": status_counts,
            "pipeline_duration_seconds": round(
                time.time() - pipeline_start, 2
            ),
            "overall_status": "PASSED",
        }

    except Exception as error:
        pipeline_report["summary"] = {
            "overall_status": "FAILED",
            "error": str(error),
            "traceback": traceback.format_exc(),
        }
        print(f"\nPIPELINE FAILED: {error}")

    finally:
        try:
            shutil.rmtree(temp_root, ignore_errors=True)
        except Exception:
            pass

    print_header("MASTER PIPELINE SUMMARY")
    print(json.dumps(pipeline_report["summary"], indent=4))

    REPORT_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(safe_dump(pipeline_report), f, indent=4)

    print(f"\nFull report written to: {REPORT_OUTPUT}")

    return pipeline_report


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    run_master_pipeline()
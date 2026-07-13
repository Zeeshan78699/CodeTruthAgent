"""
run_m1.py
CodeTruth Agent V3 — Module 1 Standalone Runner

USAGE:
    python run_m1.py "C:\\repos\\your_repo"
    python run_m1.py "C:\\repos\\your_repo" --json
    python run_m1.py "C:\\repos\\your_repo" --save

WHAT IT DOES:
    Runs Module 1 Repository Cognition Engine on a repository.
    Produces: domain classification, framework detection,
              architecture pattern, governance gate decision.

DOES NOT REQUIRE: Module 2
"""

import sys
import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)
import json
import argparse
from pathlib import Path
from datetime import datetime as dt, UTC

# ---------------------------------------------------------------------------
# Location-robust import bootstrap — finds the folder that CONTAINS the `v3`
# package by walking upward, so this runner works from ANY location (e.g. a
# main_pipeline_to_run/ subfolder or a future final-files layout) without the
# `from v3....` imports breaking. Honours a CODETRUTH_ROOT env override; falls
# back to the original assumption if no marker is found.
# ---------------------------------------------------------------------------
import os
from pathlib import Path


def _find_codetruth_root(start: Path) -> Path:
    env = os.environ.get("CODETRUTH_ROOT")
    if env and (Path(env) / "v3" / "repository_cognition").is_dir():
        return Path(env)
    for parent in [start, *start.parents]:
        if (parent / "v3" / "repository_cognition").is_dir():
            return parent
    return start.parent


CODETRUTH_ROOT = _find_codetruth_root(Path(__file__).resolve().parent)
sys.path.insert(0, str(CODETRUTH_ROOT))          # enables `import v3.<pkg>`
sys.path.insert(0, str(CODETRUTH_ROOT / "v3"))   # enables bare v3-relative imports
V3_ROOT = CODETRUTH_ROOT / "v3"                   # backward-compatible alias


def parse_args():
    parser = argparse.ArgumentParser(
        description="CodeTruth V3 — Module 1 Repository Cognition"
    )
    parser.add_argument(
        "repo_path",
        help="Path to the repository to analyse"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save results to m1_report_{repo_name}.json"
    )
    return parser.parse_args()


def run_module1(repo_path: str) -> dict:
    from v3.repository_cognition import RepositoryCognitionEngine
    from v3.repository_cognition.module1_extensions import EnhancedReportBuilder

    root = Path(repo_path)
    if not root.exists():
        print(f"ERROR: Repository path not found: {repo_path}")
        sys.exit(1)

    print("=" * 70)
    print("CodeTruth V3 — Module 1: Repository Cognition Engine")
    print("=" * 70)
    print(f"Repository : {repo_path}")
    print(f"Started    : {dt.now(UTC).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("-" * 70)

    # Run Module 1 core
    print("Running cognition engine...")
    m1_core = RepositoryCognitionEngine(repo_path).scan()

    # Run enhanced report
    print("Running domain enhancement...")
    m1_enhanced = EnhancedReportBuilder().build(m1_core, repo_path)

    # Extract results
    application_type = getattr(
        getattr(m1_enhanced, "identity", None),
        "application_type",
        getattr(m1_core, "application_type", "UNKNOWN")
    )
    # Apply domain enhancement — corrects engineering repos
    # classified as ML_PIPELINE by core engine
    try:
        from v3.repository_cognition.module1_extensions.domain_signatures import (
            get_enhanced_application_type
        )
        application_type = get_enhanced_application_type(
            application_type, repo_path
        )
    except Exception:
        pass
    # Use enhanced identity framework (priority-corrected)
    _enhanced_fw = getattr(
        getattr(m1_enhanced, "identity", None),
        "primary_framework", None
    )
    framework = _enhanced_fw or getattr(m1_core, "primary_framework", "unknown")
    confidence  = getattr(m1_core, "confidence_score", 0.0)
    gate        = m1_enhanced.gate.gate_decision
    architecture = getattr(
        getattr(m1_enhanced, "architecture", None),
        "pattern", "UNKNOWN"
    )
    risk_score  = getattr(
        getattr(m1_enhanced, "risk", None),
        "repository_risk_score", 0
    )
    assumptions = getattr(
        getattr(m1_enhanced, "assumptions", None),
        "total_found", 0
    )
    constraints = getattr(
        getattr(m1_enhanced, "constraints", None),
        "total_found", 0
    )

    result = {
        "repo_path":       repo_path,
        "run_time":        dt.now(UTC).isoformat(),
        "application_type": application_type,
        "framework":        framework,
        "confidence":       confidence,
        "architecture":     architecture,
        "gate":             gate,
        "risk_score":       risk_score,
        "assumptions":      assumptions,
        "constraints":      constraints,
        "module":           "M1",
        "status":           "COMPLETE",
    }

    print("-" * 70)
    print("RESULTS")
    print("-" * 70)
    print(f"  Application Type : {application_type}")
    print(f"  Framework        : {framework}")
    print(f"  Architecture     : {architecture}")
    print(f"  Confidence       : {confidence}")
    print(f"  Risk Score       : {risk_score}/10")
    print(f"  Assumptions      : {assumptions}")
    print(f"  Constraints      : {constraints}")
    print("-" * 70)

    gate_emoji = {"APPROVED": "✅", "REVIEW_REQUIRED": "⚠️", "BLOCKED": "❌"}.get(gate, "?")
    print(f"  GOVERNANCE GATE  : {gate_emoji}  {gate}")
    print("=" * 70)

    return result


def main():
    args = parse_args()
    result = run_module1(args.repo_path)

    if args.json:
        print(json.dumps(result, indent=2))

    if args.save:
        repo_name = Path(args.repo_path).name
        out_path  = Path(f"m1_report_{repo_name}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"Report saved: {out_path}")

    # Exit code matches gate
    if result["gate"] == "BLOCKED":
        sys.exit(2)
    elif result["gate"] == "REVIEW_REQUIRED":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
"""
pipeline.py
CodeTruth Agent V3 — Combined Module 1 + Module 2 Pipeline

USAGE:
    python pipeline.py "C:\\repos\\your_repo"
    python pipeline.py "C:\\repos\\your_repo" --save
    python pipeline.py "C:\\repos\\your_repo" --json
    python pipeline.py "C:\\repos\\your_repo" --force
    python pipeline.py --batch repos.txt
"""

import sys
import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)
import json
import argparse
from pathlib import Path
from datetime import datetime as dt, UTC

V3_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(V3_ROOT.parent))
sys.path.insert(0, str(V3_ROOT))

GATE_EMOJI = {"APPROVED": "OK", "REVIEW_REQUIRED": "WARN", "BLOCKED": "STOP"}

DOMAIN_TO_LANGUAGE = {
    "ERP_SYSTEM":            "sql",
    "WELL_LOGGING":          "python",
    "DRILLING_SYSTEM":       "python",
    "RESERVOIR_ENGINEERING": "python",
    "FLUIDS_ENGINEERING":    "python",
    "AEROSPACE_STRUCTURAL_SIMULATION": "python",
    "ENERGY_SYSTEM":         "python",
    "SPACE_SYSTEM":          "python",
    "MEDICAL_SYSTEM":        "python",
    "FINANCE_SYSTEM":        "python",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="CodeTruth V3 — Module 1 + Module 2 Pipeline"
    )
    parser.add_argument("repo_path", nargs="?",
                        help="Path to the repository to analyse")
    parser.add_argument("--save", action="store_true",
                        help="Save combined report to JSON")
    parser.add_argument("--json", action="store_true",
                        help="Output results as JSON")
    parser.add_argument("--force", action="store_true",
                        help="Run Module 2 even if gate = REVIEW_REQUIRED")
    parser.add_argument("--annotation", action="store_true",
                        help="Run annotation resolver after DR (Python only)")
    parser.add_argument("--batch", metavar="FILE",
                        help="Run on multiple repos listed in a text file")
    return parser.parse_args()


def detect_language(m1_core) -> str:
    lang_comp = getattr(m1_core, "language_composition", {})
    adapter_langs = {"python", "csharp", "sql", "go"}
    if lang_comp:
        ranked = sorted(
            lang_comp.items(),
            key=lambda x: x[1].get("file_count", 0) if isinstance(x[1], dict) else 0,
            reverse=True,
        )
        for lang, _ in ranked:
            if lang in adapter_langs:
                return lang
    app_type = getattr(m1_core, "application_type", "")
    return DOMAIN_TO_LANGUAGE.get(app_type, "python")


def get_adapter(language: str):
    if language == "csharp":
        from v3.repository_graph.languages.csharp_adapter import CSharpAdapter
        return CSharpAdapter()
    elif language == "sql":
        from v3.repository_graph.languages.sql_adapter import SQLAdapter
        return SQLAdapter()
    elif language == "go":
        from v3.repository_graph.languages.go_adapter import GoAdapter
        return GoAdapter()
    else:
        from v3.repository_graph.languages.python_adapter import PythonAdapter
        return PythonAdapter()


def run_pipeline(repo_path: str, force: bool = False,
                 run_annotation: bool = False) -> dict:
    root = Path(repo_path)
    if not root.exists():
        return {"repo_path": repo_path, "status": "ERROR",
                "reason": "Path not found"}

    result = {
        "repo_path": repo_path,
        "run_time":  dt.now(UTC).isoformat(),
        "module1":   {},
        "module2":   {},
        "gate":      "",
        "language":  "",
        "status":    "",
    }

    # ── MODULE 1 ─────────────────────────────────────────────────────
    print("=" * 70)
    print("MODULE 1 — Repository Cognition Engine")
    print("=" * 70)
    print("Repo: " + repo_path)

    try:
        from v3.repository_cognition import RepositoryCognitionEngine
        from v3.repository_cognition.module1_extensions import EnhancedReportBuilder

        m1_core     = RepositoryCognitionEngine(repo_path).scan()
        m1_enhanced = EnhancedReportBuilder().build(m1_core, repo_path)
        gate        = m1_enhanced.gate.gate_decision
        # Read raw application type from identity
        application_type = getattr(
            getattr(m1_enhanced, "identity", None), "application_type",
            getattr(m1_core, "application_type", "UNKNOWN")
        )
        # Apply domain enhancement directly — overrides ML_PIPELINE
        # for engineering repos (OpenMDAO, pyNastran etc.)
        try:
            from v3.repository_cognition.module1_extensions.domain_signatures import (
                get_enhanced_application_type
            )
            application_type = get_enhanced_application_type(
                application_type, repo_path
            )
        except Exception:
            pass
        _enhanced_fw = getattr(getattr(m1_enhanced, "identity", None), "primary_framework", None)
        framework = _enhanced_fw or getattr(m1_core, "primary_framework", "unknown")
        confidence = getattr(m1_core, "confidence_score", 0.0)
        arch       = getattr(getattr(m1_enhanced, "architecture", None),
                             "pattern", "UNKNOWN")

        result["module1"] = {
            "application_type": application_type,
            "framework":        framework,
            "confidence":       confidence,
            "gate":             gate,
            "architecture":     arch,
        }
        result["gate"] = gate

        print("  Application Type : " + str(application_type))
        print("  Framework        : " + str(framework))
        print("  Architecture     : " + str(arch))
        print("  Confidence       : " + str(confidence))
        print("  Gate             : [" + GATE_EMOJI.get(gate, "?") + "] " + gate)

    except Exception as e:
        print("  Module 1 ERROR: " + str(e))
        result["status"] = "M1_ERROR"
        result["reason"] = str(e)
        return result

    # ── GATE CHECK ───────────────────────────────────────────────────
    if gate == "BLOCKED":
        print("\n  BLOCKED — Module 2 will not run.")
        result["status"] = "BLOCKED"
        return result

    if gate == "REVIEW_REQUIRED" and not force:
        print("\n  REVIEW_REQUIRED — use --force to run Module 2 anyway.")
        result["status"] = "REVIEW_REQUIRED"
        return result

    # ── LANGUAGE DETECTION ───────────────────────────────────────────
    language = detect_language(m1_core)
    result["language"] = language
    print("  Language         : " + language)

    # ── MODULE 2 ─────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("MODULE 2 — Repository Graph Intelligence")
    print("=" * 70)

    try:
        adapter   = get_adapter(language)
        print("  Adapter  : " + adapter.__class__.__name__)
        m2_report = adapter.scan(repo_root=repo_path, file_paths=[])

        gate_m2       = m2_report.get("governance_gate", "UNKNOWN")
        files_scanned = m2_report.get("files_scanned", 0)
        nc = m2_report.get("node_counts", {})
        ec = m2_report.get("edge_counts", {})

        print("  Files scanned : " + str(files_scanned))

        if language == "python":
            def _cg(g): return sum(len(v) if isinstance(v, list) else 1 for v in g.values()) if isinstance(g, dict) else 0
            print("  Functions     : " + str(_cg(m2_report.get("function_graph", {}))))
            print("  Classes       : " + str(_cg(m2_report.get("class_graph", {}))))
            dr   = m2_report.get("deep_resolution", {})
            rr   = dr.get("resolver_results", {})
            fin  = dr.get("final", {})
            base = dr.get("baseline_unresolved", 0)
            res  = fin.get("resolved_by_pipeline", 0)
            rem  = fin.get("remaining_unresolved", max(0, base - res))
            print("  Baseline unresolved  : " + str(base))
            print("  Remaining unresolved : " + str(rem))
            print("  builtin_type         : " + str(rr.get("builtin_type", 0)))
            print("  constructor          : " + str(rr.get("constructor", 0)))
            print("  factory              : " + str(rr.get("factory", 0)))
            print("  DR total resolved    : " + str(res))
            print("  DR reduction         : " + str(fin.get("reduction_pct", 0)) + "%")

            if run_annotation:
                try:
                    from v3.repository_graph.tests.deep_resolution.annotation_resolver import (
                        integrate_with_pipeline
                    )
                except ImportError:
                    from v3.repository_graph.tests.deep_resolution.annotation_resolver import (
                        integrate_with_pipeline
                    )
                dr_updated = integrate_with_pipeline(dr, repo_path)
                ann = dr_updated["resolver_results"].get("annotation", 0)
                print("  Annotation    : +" + str(ann))
                m2_report["deep_resolution"] = dr_updated

        elif language == "csharp":
            print("  DR field_type : " + str(m2_report.get("dr_field_type", 0)))
            print("  Overall pct   : " + str(m2_report.get("overall_pct", 0)) + "%")

        elif language == "sql":
            print("  Dialect       : " + str(m2_report.get("dialect", "N/A")))
            print("  Resolution    : " + str(m2_report.get("resolution_pct", 0)) + "%")

        elif language == "go":
            print("  Module        : " + str(m2_report.get("module_name", "N/A")))
            print("  Framework     : " + str(m2_report.get("framework", "N/A")))
            print("  Resolution    : " + str(m2_report.get("resolution_pct", 0)) + "%")

        print("  Gate          : [" + GATE_EMOJI.get(gate_m2, "?") + "] " + gate_m2)

        result["module2"] = {
            "language":       language,
            "adapter":        adapter.__class__.__name__,
            "files_scanned":  files_scanned,
            "node_counts":    nc,
            "edge_counts":    ec,
            "gate":           gate_m2,
            "resolution_pct": m2_report.get("resolution_pct", 0),
        }

    except Exception as e:
        print("  Module 2 ERROR: " + str(e))
        result["status"] = "M2_ERROR"
        result["reason"] = str(e)
        return result

    result["status"] = "COMPLETE"
    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print("  M1 Gate  : " + result["gate"])
    print("  M2 Gate  : " + result["module2"].get("gate", "N/A"))
    print("  Language : " + language)
    print("  Status   : COMPLETE")
    print("=" * 70)
    return result


def run_batch(batch_file: str, force: bool, run_annotation: bool) -> list:
    repos = [
        line.strip() for line in
        Path(batch_file).read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    print("Batch mode: " + str(len(repos)) + " repositories")
    results = []
    for i, repo in enumerate(repos, 1):
        print("\n[" + str(i) + "/" + str(len(repos)) + "] " + repo)
        result = run_pipeline(repo, force=force, run_annotation=run_annotation)
        results.append(result)

    print("\n" + "=" * 70)
    print("BATCH SUMMARY")
    print("=" * 70)
    complete = 0
    for r in results:
        status = r.get("status", "UNKNOWN")
        name   = Path(r["repo_path"]).name
        flag   = "OK" if status == "COMPLETE" else "FAIL"
        print("  [" + flag + "] " + name.ljust(30) + " " + status)
        if status == "COMPLETE":
            complete += 1
    print("\n  " + str(complete) + "/" + str(len(repos)) + " COMPLETE")
    return results


def main():
    args = parse_args()

    if args.batch:
        results = run_batch(args.batch, args.force, args.annotation)
        if args.save:
            out = Path("batch_pipeline_report.json")
            with open(out, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, default=str)
            print("Batch report saved: " + str(out))
        sys.exit(0)

    if not args.repo_path:
        print("ERROR: provide a repo path or --batch file")
        sys.exit(1)

    result = run_pipeline(
        args.repo_path,
        force=args.force,
        run_annotation=args.annotation,
    )

    if args.json:
        print(json.dumps(result, indent=2, default=str))

    if args.save:
        repo_name = Path(args.repo_path).name
        out_path  = Path("pipeline_report_" + repo_name + ".json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)
        print("Report saved: " + str(out_path))

    sys.exit(0 if result.get("status") == "COMPLETE" else 1)


if __name__ == "__main__":
    main()
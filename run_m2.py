"""
run_m2.py
CodeTruth Agent V3 — Module 2 Standalone Runner

USAGE:
    python run_m2.py "C:\\repos\\your_repo"
    python run_m2.py "C:\\repos\\your_repo" --language python
    python run_m2.py "C:\\repos\\your_repo" --language csharp
    python run_m2.py "C:\\repos\\your_repo" --language sql
    python run_m2.py "C:\\repos\\your_repo" --language go
    python run_m2.py "C:\\repos\\your_repo" --save
    python run_m2.py "C:\\repos\\your_repo" --json

WHAT IT DOES:
    Runs Module 2 Repository Graph Intelligence on a repository.
    Produces: call graph, dependency graph, deep resolution results,
              governance gate decision.

NOTE:
    Running M2 without M1 means no gate check from Module 1.
    You are responsible for selecting the correct language adapter.
    For full governance, use pipeline.py instead.

DOES NOT REQUIRE: Module 1
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

SUPPORTED_LANGUAGES = ["python", "csharp", "sql", "go"]


def parse_args():
    parser = argparse.ArgumentParser(
        description="CodeTruth V3 — Module 2 Repository Graph Intelligence"
    )
    parser.add_argument(
        "repo_path",
        help="Path to the repository to analyse"
    )
    parser.add_argument(
        "--language", "-l",
        default="python",
        choices=SUPPORTED_LANGUAGES,
        help="Language adapter to use (default: python)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save results to m2_report_{repo_name}.json"
    )
    parser.add_argument(
        "--annotation",
        action="store_true",
        help="Run annotation resolver after Deep Resolution (Python only)"
    )
    return parser.parse_args()


def get_adapter(language: str):
    if language == "python":
        from v3.repository_graph.languages.python_adapter import PythonAdapter
        return PythonAdapter()
    elif language == "csharp":
        from v3.repository_graph.languages.csharp_adapter import CSharpAdapter
        return CSharpAdapter()
    elif language == "sql":
        from v3.repository_graph.languages.sql_adapter import SQLAdapter
        return SQLAdapter()
    elif language == "go":
        from v3.repository_graph.languages.go_adapter import GoAdapter
        return GoAdapter()
    else:
        raise ValueError(f"Unsupported language: {language}")


def print_python_dr(report: dict):
    dr       = report.get("deep_resolution", {})
    rr       = dr.get("resolver_results", {})
    fin      = dr.get("final", {})
    baseline = dr.get("baseline_unresolved", 0)
    resolved = fin.get("resolved_by_pipeline", 0)
    remaining = fin.get("remaining_unresolved", max(0, baseline - resolved))
    print("  Baseline unresolved  : " + str(baseline))
    print("  Remaining unresolved : " + str(remaining))
    print("  ")
    print("  builtin_type         : " + str(rr.get("builtin_type", 0)))
    print("  constructor          : " + str(rr.get("constructor", 0)))
    print("  factory              : " + str(rr.get("factory", 0)))
    print("  property             : " + str(rr.get("property", 0)))
    print("  inheritance          : " + str(rr.get("inheritance", 0)))
    print("  annotation           : " + str(rr.get("annotation", 0)))
    print("  ")
    print("  DR total resolved    : " + str(resolved))
    print("  DR reduction         : " + str(fin.get("reduction_pct", 0)) + "%")


def print_csharp_dr(report: dict):
    print(f"  dr_field_type        : {report.get('dr_field_type', 0)}")
    print(f"  dr_interface         : {report.get('dr_interface', 0)}")
    print(f"  dr_di_constructor    : {report.get('dr_di_constructor', 0)}")
    print(f"  DR total resolved    : {report.get('dr_resolved_by_pipeline', 0)}")
    print(f"  Overall resolution   : {report.get('overall_pct', 0)}%")


def print_sql_nodes(report: dict):
    nc = report.get("node_counts", {})
    print(f"  Tables     : {nc.get('tables', 0)}")
    print(f"  Views      : {nc.get('views', 0)}")
    print(f"  Procedures : {nc.get('procedures', 0)}")
    print(f"  Functions  : {nc.get('functions', 0)}")
    print(f"  Triggers   : {nc.get('triggers', 0)}")
    print(f"  Dialect    : {report.get('dialect', 'N/A')}")


def print_go_nodes(report: dict):
    nc = report.get("node_counts", {})
    print(f"  Packages   : {nc.get('packages', 0)}")
    print(f"  Structs    : {nc.get('structs', 0)}")
    print(f"  Interfaces : {nc.get('interfaces', 0)}")
    print(f"  Methods    : {nc.get('methods', 0)}")
    print(f"  Goroutines : {report.get('edge_counts', {}).get('goroutines', 0)}")
    print(f"  Module     : {report.get('module_name', 'N/A')}")
    print(f"  Framework  : {report.get('framework', 'N/A')}")


def run_module2(repo_path: str, language: str, run_annotation: bool) -> dict:
    root = Path(repo_path)
    if not root.exists():
        print(f"ERROR: Repository path not found: {repo_path}")
        sys.exit(1)

    print("=" * 70)
    print("CodeTruth V3 — Module 2: Repository Graph Intelligence")
    print("=" * 70)
    print(f"Repository : {repo_path}")
    print(f"Language   : {language}")
    print(f"Started    : {dt.now(UTC).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("-" * 70)

    adapter = get_adapter(language)
    print(f"Running {adapter.__class__.__name__}...")
    report = adapter.scan(repo_root=repo_path, file_paths=[])

    nc  = report.get("node_counts", {})
    ec  = report.get("edge_counts", {})
    res = report.get("resolution", {})

    print("-" * 70)
    print("GRAPH STATS")
    print("-" * 70)
    if language == "python":
        # Python adapter stores graphs as {module: [items]} dicts
        def count_graph(g):
            if isinstance(g, dict):
                return sum(len(v) if isinstance(v, list) else 1 for v in g.values())
            return 0
        print("  Functions      : " + str(count_graph(report.get("function_graph", {}))))
        print("  Classes        : " + str(count_graph(report.get("class_graph", {}))))
        print("  Modules parsed : " + str(report.get("modules_parsed", 0)))
        print("  Files scanned  : " + str(report.get("files_scanned", 0)))
        unresolved = report.get("unresolved", [])
        print("  Unresolved calls: " + str(len(unresolved) if isinstance(unresolved, list) else 0))
    else:
        print("  Total nodes  : " + str(nc.get("total", 0)))
        print("  Total edges  : " + str(ec.get("total", 0)))

    print("-" * 70)
    print("DEEP RESOLUTION")
    print("-" * 70)
    if language == "python":
        print_python_dr(report)

    elif language == "csharp":
        print_csharp_dr(report)
    elif language == "sql":
        print_sql_nodes(report)
    elif language == "go":
        print_go_nodes(report)

    # Optional annotation resolver
    if run_annotation and language == "python":
        print("-" * 70)
        print("ANNOTATION RESOLVER")
        print("-" * 70)
        try:
            try:
                from v3.repository_graph.tests.deep_resolution.annotation_resolver import (
                    integrate_with_pipeline
                )
            except ImportError:
                from v3.repository_graph.tests.deep_resolution.annotation_resolver import (
                    integrate_with_pipeline
                )
            dr_updated = integrate_with_pipeline(
                report["deep_resolution"], repo_path
            )
            ann = dr_updated["resolver_results"].get("annotation", 0)
            print(f"  Annotation resolved : {ann}")
            print(f"  New reduction pct   : {dr_updated['final']['reduction_pct']}%")
            report["deep_resolution"] = dr_updated
        except Exception as e:
            print(f"  Annotation resolver error: {e}")

    gate = report.get("governance_gate", "UNKNOWN")
    gate_emoji = {"APPROVED": "✅", "REVIEW_REQUIRED": "⚠️", "BLOCKED": "❌"}.get(gate, "?")
    print("-" * 70)
    print(f"  FILES SCANNED    : {report.get('files_scanned', 0)}")
    print(f"  GOVERNANCE GATE  : {gate_emoji}  {gate}")
    print("=" * 70)

    result = {
        "repo_path":    repo_path,
        "language":     language,
        "run_time":     dt.now(UTC).isoformat(),
        "files_scanned": report.get("files_scanned", 0),
        "node_counts":  nc,
        "edge_counts":  ec,
        "resolution":   res,
        "gate":         gate,
        "module":       "M2",
        "status":       "COMPLETE",
    }
    return result


def main():
    args = parse_args()
    result = run_module2(args.repo_path, args.language, args.annotation)

    if args.json:
        print(json.dumps(result, indent=2))

    if args.save:
        repo_name = Path(args.repo_path).name
        out_path  = Path(f"m2_report_{repo_name}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"Report saved: {out_path}")

    sys.exit(0 if result["gate"] in ("APPROVED", "REVIEW_REQUIRED") else 2)


if __name__ == "__main__":
    main()
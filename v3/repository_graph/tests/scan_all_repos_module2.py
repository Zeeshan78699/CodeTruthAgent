"""
scan_all_repos_module2.py
CodeTruth Agent V3 - Module 2 - Full Real-Repo Validation

Runs the Module 2 graph engine against the SAME 69 repos used for Module 1's
validation, and stores results separately as proof - mirroring Module 1's
outputs/real_scans/ convention (per-repo files + FULL_DOMAIN_SUMMARY).

Output location: v3/outputs/module2_graphs/
    - graph_<repo_name>.json       (full graph report per repo)
    - MODULE2_FULL_SUMMARY.csv
    - MODULE2_FULL_SUMMARY.md
    - MODULE2_FULL_SUMMARY.json

Usage:
    1. Set CLONED_REPOS_DIR below to the SAME parent folder that contains
       the 69 cloned repos used in Module 1's scan_all_repos_v3.py
       (the one clone_repos.ps1 populated).
    2. Run: python v3\\repository_graph\\tests\\scan_all_repos_module2.py
"""

import sys
import os
import json
import csv
from collections import Counter

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from v3.repository_graph.graph_engine import build_repository_graph


# ---- EDIT THIS ----
# Parent folder containing the 69 cloned repos from Module 1's validation
# (same folder clone_repos.ps1 / scan_all_repos_v3.py used)
CLONED_REPOS_DIR = r"C:\repos\v3"

OUTPUT_DIR = os.path.join(PROJECT_ROOT, "v3", "outputs", "module2_graphs")


def discover_repo_dirs(parent_dir):
    """Each immediate subdirectory of parent_dir is treated as one repo."""
    if not os.path.isdir(parent_dir):
        return []
    return sorted([
        os.path.join(parent_dir, d) for d in os.listdir(parent_dir)
        if os.path.isdir(os.path.join(parent_dir, d))
    ])


def scan_one(repo_path):
    repo_name = os.path.basename(repo_path.rstrip("\\/"))

    try:
        report = build_repository_graph(repo_path)
    except Exception as e:
        return {
            "repo": repo_name,
            "status": "CRASH",
            "error": f"{type(e).__name__}: {e}",
        }, None

    unresolved_counts = Counter(u["pattern"] for u in report["unresolved"])
    call_resolution_counts = Counter(
        edge["resolution"]
        for edges in report["call_graph"].values()
        for edge in edges
    )
    total_calls = sum(call_resolution_counts.values())
    total_unresolved = len(report["unresolved"])
    total = total_calls + total_unresolved
    resolved_pct = round(100 * total_calls / total, 1) if total else 100.0

    summary = {
        "repo": repo_name,
        "status": "OK",
        "files_scanned": report["files_scanned"],
        "modules_parsed": report["modules_parsed"],
        "functions": sum(len(v) for v in report["function_graph"].values()),
        "classes": sum(len(v) for v in report["class_graph"].values()),
        "external_deps": len(report["dependency_graph"]),
        "resolved_calls": total_calls,
        "unresolved_total": total_unresolved,
        "resolved_pct": resolved_pct,
        "governance_gate": report["governance_gate"],
        "parse_errors": unresolved_counts.get("parse_error", 0),
        "attribute_call": unresolved_counts.get("attribute_call", 0),
        "name_call_unresolved": unresolved_counts.get("name_call_unresolved", 0),
        "self_method_not_found": unresolved_counts.get("self_method_not_found", 0),
    }
    return summary, report


def write_markdown_summary(results, output_path):
    ok_results = [r for r in results if r["status"] == "OK"]
    crash_results = [r for r in results if r["status"] != "OK"]

    total_files = sum(r["files_scanned"] for r in ok_results)
    total_functions = sum(r["functions"] for r in ok_results)
    total_classes = sum(r["classes"] for r in ok_results)
    total_crashes = len(crash_results)
    total_parse_errors = sum(r["parse_errors"] for r in ok_results)
    approved_count = sum(1 for r in ok_results if r["governance_gate"] == "APPROVED")

    lines = []
    lines.append("# Module 2 — Full Repository Validation Summary")
    lines.append("")
    lines.append("**CodeTruth Agent V3 — Module 2 — Repository Graph Engine**")
    lines.append("")
    lines.append("This validation runs the SAME repo set used for Module 1's "
                  "69-repo validation, to provide a comparable proof point.")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|---|---|")
    lines.append(f"| Total repos scanned | {len(results)} |")
    lines.append(f"| Repos with 0 crashes | {len(ok_results)} / {len(results)} |")
    lines.append(f"| Crashes | {total_crashes} |")
    lines.append(f"| Governance APPROVED | {approved_count} / {len(ok_results)} |")
    lines.append(f"| Total files scanned | {total_files} |")
    lines.append(f"| Total functions found (V3-004) | {total_functions} |")
    lines.append(f"| Total classes found (V3-005) | {total_classes} |")
    lines.append(f"| Total parse errors (syntax) | {total_parse_errors} |")
    lines.append("")

    if crash_results:
        lines.append("## Crashes")
        lines.append("")
        lines.append("| Repo | Error |")
        lines.append("|---|---|")
        for r in crash_results:
            lines.append(f"| {r['repo']} | {r['error']} |")
        lines.append("")

    lines.append("## Per-Repo Results")
    lines.append("")
    lines.append("| Repo | Files | Functions | Classes | Ext Deps | "
                  "Resolved Calls | Unresolved | Resolved % | Gate |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for r in ok_results:
        lines.append(
            f"| {r['repo']} | {r['files_scanned']} | {r['functions']} | "
            f"{r['classes']} | {r['external_deps']} | {r['resolved_calls']} | "
            f"{r['unresolved_total']} | {r['resolved_pct']}% | {r['governance_gate']} |"
        )
    lines.append("")

    lines.append("## Notes / Explanation")
    lines.append("")
    lines.append("- **\"Unresolved\" is dominated by `attribute_call`** — method "
                  "calls on local variables whose type isn't statically tracked "
                  "(e.g. `lines.append(x)`). This is a documented limitation "
                  "(see MODULE2_DOCUMENTATION.md section 8), not a defect.")
    lines.append("- **\"Resolved %\" is expected to be in the 15-40% range** "
                  "across most repos due to the above. The meaningful proof "
                  "point is: 0 crashes, governance APPROVED, and 0 unresolved "
                  "items in categories that D-001/D-002/D-003 were designed "
                  "to fix (`name_call_unresolved`, `self_method_not_found` "
                  "should be near-zero across all repos).")
    lines.append("- **Parse errors** indicate files with genuine Python syntax "
                  "errors (e.g. Python 2 syntax in a Python 3 scan) - these are "
                  "logged and skipped, not crashes.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*CodeTruth Agent V3 — Module 2 — Repository Graph Engine*")
    lines.append("*github.com/Zeeshan78699/CodeTruthAgent*")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    repo_dirs = discover_repo_dirs(CLONED_REPOS_DIR)
    if not repo_dirs:
        print(f"No repos found in {CLONED_REPOS_DIR}")
        print("Edit CLONED_REPOS_DIR at the top of this script to point at "
              "the folder containing your 69 cloned repos from Module 1.")
        sys.exit(1)

    print(f"Found {len(repo_dirs)} repo(s) in {CLONED_REPOS_DIR}")
    print(f"Output will be saved to: {OUTPUT_DIR}\n")

    results = []
    for repo_path in repo_dirs:
        repo_name = os.path.basename(repo_path.rstrip("\\/"))
        print(f"Scanning: {repo_name} ...", end=" ")

        summary, full_report = scan_one(repo_path)
        results.append(summary)

        if summary["status"] == "OK":
            print(f"OK ({summary['files_scanned']} files, "
                  f"{summary['unresolved_total']} unresolved, "
                  f"{summary['governance_gate']})")
            # Save full per-repo report
            out_file = os.path.join(OUTPUT_DIR, f"graph_{repo_name}.json")
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(full_report, f, indent=2, default=str)
        else:
            print(f"CRASH: {summary['error']}")

    # ---- Write summary files ----
    csv_path = os.path.join(OUTPUT_DIR, "MODULE2_FULL_SUMMARY.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "repo", "status", "files_scanned", "modules_parsed", "functions",
            "classes", "external_deps", "resolved_calls", "unresolved_total",
            "resolved_pct", "governance_gate", "parse_errors", "attribute_call",
            "name_call_unresolved", "self_method_not_found", "error",
        ])
        writer.writeheader()
        for r in results:
            row = {k: r.get(k, "") for k in writer.fieldnames}
            writer.writerow(row)

    json_path = os.path.join(OUTPUT_DIR, "MODULE2_FULL_SUMMARY.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    md_path = os.path.join(OUTPUT_DIR, "MODULE2_FULL_SUMMARY.md")
    write_markdown_summary(results, md_path)

    # ---- Print final tally ----
    ok = [r for r in results if r["status"] == "OK"]
    crashed = [r for r in results if r["status"] != "OK"]
    approved = [r for r in ok if r["governance_gate"] == "APPROVED"]

    print()
    print("=" * 60)
    print(f"TOTAL REPOS: {len(results)}")
    print(f"  OK (no crash): {len(ok)}")
    print(f"  CRASHED: {len(crashed)}")
    print(f"  Governance APPROVED: {len(approved)} / {len(ok)}")
    print(f"  Total files scanned: {sum(r['files_scanned'] for r in ok)}")
    print(f"  Total functions found: {sum(r['functions'] for r in ok)}")
    print(f"  Total classes found: {sum(r['classes'] for r in ok)}")
    print("=" * 60)
    print(f"\nResults saved to: {OUTPUT_DIR}")
    print(f"  - MODULE2_FULL_SUMMARY.csv")
    print(f"  - MODULE2_FULL_SUMMARY.json")
    print(f"  - MODULE2_FULL_SUMMARY.md")
    print(f"  - graph_<repo_name>.json (one per repo)")

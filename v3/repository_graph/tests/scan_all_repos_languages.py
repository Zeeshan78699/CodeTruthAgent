"""
scan_all_repos_languages.py
Runs the Java, JavaScript, and C/C++ adapters against ALL 69 repos and
produces a summary - mirrors scan_all_repos_module2.py's pattern, but for
the language adapters (not Python).

Usage:
    python v3\\repository_graph\\tests\\scan_all_repos_languages.py [max_files_per_repo]

max_files_per_repo (optional, default 300): cap per repo per language, to
keep runtime reasonable across 69 repos. Set to 0 for no cap (slow on
large repos like odoo/transformers).

Outputs:
    v3/outputs/module2_graphs/LANGUAGE_ADAPTERS_SUMMARY.json
    v3/outputs/module2_graphs/LANGUAGE_ADAPTERS_SUMMARY.csv
    v3/outputs/module2_graphs/LANGUAGE_ADAPTERS_SUMMARY.md
"""

import sys
import os
import json
import csv
from collections import Counter

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from v3.repository_graph.languages.c_cpp_adapter import CCppAdapter
from v3.repository_graph.languages.javascript_adapter import JavaScriptAdapter
from v3.repository_graph.languages.java_adapter import JavaAdapter


CLONED_REPOS_DIR = r"C:\repos\v3"
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "v3", "outputs", "module2_graphs")

ADAPTERS = {
    "c_cpp": (CCppAdapter(), {".c", ".h", ".cpp", ".cc", ".cxx", ".hpp", ".hh", ".hxx"}),
    "javascript": (JavaScriptAdapter(), {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"}),
    "java": (JavaAdapter(), {".java"}),
}

IGNORE_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "build", "dist"}


def find_files(root, extensions):
    matches = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        for f in filenames:
            if os.path.splitext(f)[1].lower() in extensions:
                matches.append(os.path.join(dirpath, f))
    return matches


def summarize(report):
    unresolved = Counter(u["pattern"] for u in report["unresolved"])
    resolved = Counter(e["resolution"] for edges in report["call_graph"].values() for e in edges)
    total_resolved = sum(resolved.values())
    total_unresolved = sum(unresolved.values())
    total = total_resolved + total_unresolved
    pct = round(100 * total_resolved / total, 1) if total else None
    return {
        "files_with_data": len(report["function_graph"]),
        "functions": sum(len(v) for v in report["function_graph"].values()),
        "classes": sum(len(v) for v in report["class_graph"].values()),
        "external_deps": len(report["dependency_graph"]),
        "resolved_calls": total_resolved,
        "unresolved_calls": total_unresolved,
        "resolved_pct": pct,
        "parse_errors": unresolved.get("parse_error", 0),
    }


if __name__ == "__main__":
    max_files = int(sys.argv[1]) if len(sys.argv) > 1 else 300

    if not os.path.isdir(CLONED_REPOS_DIR):
        print(f"ERROR: {CLONED_REPOS_DIR} not found.")
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    repos = sorted([d for d in os.listdir(CLONED_REPOS_DIR)
                     if os.path.isdir(os.path.join(CLONED_REPOS_DIR, d))])

    results = []

    for repo in repos:
        repo_path = os.path.join(CLONED_REPOS_DIR, repo)
        row = {"repo": repo}

        for lang, (adapter, extensions) in ADAPTERS.items():
            files = find_files(repo_path, extensions)
            row[f"{lang}_files_found"] = len(files)

            if not files:
                row[f"{lang}_summary"] = None
                continue

            scanned = files if max_files == 0 else files[:max_files]
            try:
                report = adapter.scan(repo_path, scanned)
                row[f"{lang}_summary"] = summarize(report)
            except Exception as e:
                row[f"{lang}_summary"] = {"error": f"{type(e).__name__}: {e}"}

        status_bits = []
        for lang in ADAPTERS:
            found = row[f"{lang}_files_found"]
            if found:
                status_bits.append(f"{lang}={found}")
        print(f"Scanning: {repo} ... {', '.join(status_bits) if status_bits else 'no target files'}")

        results.append(row)

    # ---- Write JSON ----
    json_path = os.path.join(OUTPUT_DIR, "LANGUAGE_ADAPTERS_SUMMARY.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    # ---- Write CSV (flattened) ----
    csv_path = os.path.join(OUTPUT_DIR, "LANGUAGE_ADAPTERS_SUMMARY.csv")
    fieldnames = ["repo"]
    for lang in ADAPTERS:
        fieldnames += [
            f"{lang}_files_found", f"{lang}_files_with_data",
            f"{lang}_functions", f"{lang}_classes", f"{lang}_external_deps",
            f"{lang}_resolved_calls", f"{lang}_unresolved_calls",
            f"{lang}_resolved_pct", f"{lang}_parse_errors", f"{lang}_error",
        ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            flat = {"repo": row["repo"]}
            for lang in ADAPTERS:
                flat[f"{lang}_files_found"] = row[f"{lang}_files_found"]
                summ = row.get(f"{lang}_summary")
                if summ and "error" not in summ:
                    for k, v in summ.items():
                        flat[f"{lang}_{k}"] = v
                elif summ and "error" in summ:
                    flat[f"{lang}_error"] = summ["error"]
            writer.writerow(flat)

    # ---- Write Markdown ----
    md_path = os.path.join(OUTPUT_DIR, "LANGUAGE_ADAPTERS_SUMMARY.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Multi-Language Adapter — 69-Repo Summary\n\n")
        f.write("Java/JavaScript/C++ adapters run against the same 69-repo set "
                "used for Module 2's Python validation. Same-file resolution "
                "only (see MODULE2_VALIDATION_SUMMARY.md for scope/limitations).\n\n")

        # Aggregate totals
        for lang in ADAPTERS:
            total_files = sum(r[f"{lang}_files_found"] for r in results)
            repos_with_files = sum(1 for r in results if r[f"{lang}_files_found"] > 0)
            total_funcs = sum((r.get(f"{lang}_summary") or {}).get("functions", 0)
                               for r in results if r.get(f"{lang}_summary") and "error" not in r[f"{lang}_summary"])
            total_resolved = sum((r.get(f"{lang}_summary") or {}).get("resolved_calls", 0)
                                  for r in results if r.get(f"{lang}_summary") and "error" not in r[f"{lang}_summary"])
            total_unresolved = sum((r.get(f"{lang}_summary") or {}).get("unresolved_calls", 0)
                                    for r in results if r.get(f"{lang}_summary") and "error" not in r[f"{lang}_summary"])
            total_errors = sum(1 for r in results if r.get(f"{lang}_summary") and "error" in r[f"{lang}_summary"])
            overall_pct = round(100 * total_resolved / (total_resolved + total_unresolved), 1) \
                if (total_resolved + total_unresolved) else None

            f.write(f"## {lang}\n\n")
            f.write(f"- Repos with {lang} files: {repos_with_files} / {len(results)}\n")
            f.write(f"- Total {lang} files found: {total_files} (capped at {max_files or 'unlimited'} per repo)\n")
            f.write(f"- Total functions extracted: {total_funcs}\n")
            f.write(f"- Total resolved calls: {total_resolved}\n")
            f.write(f"- Total unresolved calls: {total_unresolved}\n")
            f.write(f"- Overall resolved %: {overall_pct}\n")
            f.write(f"- Adapter errors (crashes): {total_errors}\n\n")

        # Per-repo table (only repos with any target files)
        f.write("## Per-Repo Detail (repos with C/C++, JS, or Java files)\n\n")
        f.write("| Repo | C/C++ files | C/C++ resolved% | JS files | JS resolved% | "
                "JS parse_err | Java files | Java resolved% |\n")
        f.write("|---|---|---|---|---|---|---|---|\n")
        for r in results:
            any_files = any(r[f"{lang}_files_found"] > 0 for lang in ADAPTERS)
            if not any_files:
                continue
            c = r.get("c_cpp_summary") or {}
            j = r.get("javascript_summary") or {}
            jv = r.get("java_summary") or {}
            f.write(f"| {r['repo']} "
                    f"| {r['c_cpp_files_found']} | {c.get('resolved_pct', '-')} "
                    f"| {r['javascript_files_found']} | {j.get('resolved_pct', '-')} | {j.get('parse_errors', '-')} "
                    f"| {r['java_files_found']} | {jv.get('resolved_pct', '-')} |\n")

    print(f"\nWritten:\n  {json_path}\n  {csv_path}\n  {md_path}")
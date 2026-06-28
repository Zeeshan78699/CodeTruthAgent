"""
scan_all_repos_with_deep_resolution.py
CodeTruth Agent V3 — Module 2 + Deep Resolution — Full 69-Repo Corpus Runner

Runs the FULL integrated pipeline (Module 2 core + deep_resolution) against
all 69 repos using PythonAdapter().scan() — the same entry point used by
test_real_repo.py — so deep_resolution results are included per repo.

This replaces scan_all_repos_module2.py for the post-deep_resolution
validation pass. scan_all_repos_module2.py used build_repository_graph()
directly (core engine only). This script uses PythonAdapter().scan() which
includes deep_resolution when it is wired into your local build.

Usage:
    python v3\\repository_graph\\tests\\scan_all_repos_with_deep_resolution.py

Edit CLONED_REPOS_DIR to point at the folder containing your 69 cloned repos.

Outputs (v3/outputs/module2_deep_resolution/):
    DEEP_RESOLUTION_FULL_SUMMARY.json   — per-repo results, all metrics
    DEEP_RESOLUTION_FULL_SUMMARY.csv    — flattened, spreadsheet-ready
    DEEP_RESOLUTION_FULL_SUMMARY.md     — human-readable report
"""

import sys
import os
import json
import csv
import time
import warnings
from collections import Counter

warnings.filterwarnings("ignore", category=SyntaxWarning)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from v3.repository_graph.languages.python_adapter import PythonAdapter

# ── EDIT THIS ──────────────────────────────────────────────────────────────────
CLONED_REPOS_DIR = r"C:\repos\v3"
# ──────────────────────────────────────────────────────────────────────────────

OUTPUT_DIR = os.path.join(PROJECT_ROOT, "v3", "outputs", "module2_deep_resolution")

FACTORY_PREFIXES = ("create_", "build_", "get_", "make_", "load_")


def discover_repo_dirs(parent_dir):
    if not os.path.isdir(parent_dir):
        return []
    return sorted([
        os.path.join(parent_dir, d) for d in os.listdir(parent_dir)
        if os.path.isdir(os.path.join(parent_dir, d))
    ])


def factory_diagnostic(report):
    """Count factory-named functions with provable local-class return types.
    This is the precondition factory_return_engine needs to fire."""
    rt = report.get("return_type_table", {})
    candidates = [
        (fid, ti) for fid, ti in rt.items()
        if any(fid.split(".")[-1].lstrip("_").startswith(p) for p in FACTORY_PREFIXES)
    ]
    class_candidates = [(fid, ti) for fid, ti in candidates if ti and ti[0] == "class"]
    return len(candidates), len(class_candidates)


def scan_one(repo_path):
    repo_name = os.path.basename(repo_path.rstrip("\\/"))

    if not os.path.isdir(repo_path):
        return {
            "repo": repo_name,
            "status": "PATH_NOT_FOUND",
            "error": f"Directory not found: {repo_path}",
        }

    try:
        start = time.time()
        report = PythonAdapter().scan(repo_root=repo_path, file_paths=[])
        elapsed = round(time.time() - start, 2)
    except Exception as e:
        return {
            "repo": repo_name,
            "status": "CRASH",
            "error": f"{type(e).__name__}: {e}",
        }

    # ── Core engine metrics ────────────────────────────────────────────────
    unresolved = report.get("unresolved", [])
    unresolved_counts = Counter(u["pattern"] for u in unresolved)
    call_resolution_counts = Counter(
        edge["resolution"]
        for edges in report.get("call_graph", {}).values()
        for edge in edges
    )
    total_resolved_calls = sum(call_resolution_counts.values())
    total_unresolved = len(unresolved)
    total = total_resolved_calls + total_unresolved
    resolved_pct = round(100 * total_resolved_calls / total, 1) if total else 100.0

    # ── Deep resolution metrics ────────────────────────────────────────────
    dr = report.get("deep_resolution", {})
    has_deep_resolution = bool(dr)
    resolver_results = dr.get("resolver_results", {})
    final = dr.get("final", {})
    resolved_by_pipeline = final.get("resolved_by_pipeline", 0)
    remaining_unresolved = final.get("remaining_unresolved", total_unresolved)
    reduction_pct = final.get("reduction_pct", 0.0)

    # ── Factory diagnostic ─────────────────────────────────────────────────
    factory_any, factory_class = factory_diagnostic(report)

    summary = {
        "repo": repo_name,
        "status": "OK",
        "elapsed_s": elapsed,

        # Core engine
        "files_scanned": report.get("files_scanned", 0),
        "modules_parsed": report.get("modules_parsed", 0),
        "functions": sum(len(v) for v in report.get("function_graph", {}).values()),
        "classes": sum(len(v) for v in report.get("class_graph", {}).values()),
        "external_deps": len(report.get("dependency_graph", {})),
        "resolved_calls": total_resolved_calls,
        "unresolved_total": total_unresolved,
        "resolved_pct": resolved_pct,
        "governance_gate": report.get("governance_gate", "UNKNOWN"),
        "parse_errors": unresolved_counts.get("parse_error", 0),
        "attribute_call": unresolved_counts.get("attribute_call", 0),
        "name_call_unresolved": unresolved_counts.get("name_call_unresolved", 0),
        "self_method_not_found": unresolved_counts.get("self_method_not_found", 0),
        "package_root_corrected": report.get("package_root_corrected", False),
        "src_layout_stripped": report.get("src_layout_prefix_stripped", None),
        "return_type_table_size": report.get("return_type_table_size", 0),

        # Deep resolution
        "has_deep_resolution": has_deep_resolution,
        "dr_builtin_type": resolver_results.get("builtin_type", 0),
        "dr_constructor": resolver_results.get("constructor", 0),
        "dr_factory": resolver_results.get("factory", 0),
        "dr_property": resolver_results.get("property", 0),
        "dr_inheritance": resolver_results.get("inheritance", 0),
        "dr_reflection": resolver_results.get("reflection", 0),
        "dr_resolved_by_pipeline": resolved_by_pipeline,
        "dr_remaining_unresolved": remaining_unresolved,
        "dr_reduction_pct": reduction_pct,

        # Factory diagnostic
        "factory_named_any_return": factory_any,
        "factory_named_class_return": factory_class,
    }
    return summary


def write_markdown(results, output_path):
    ok = [r for r in results if r["status"] == "OK"]
    crashed = [r for r in results if r["status"] == "CRASH"]
    not_found = [r for r in results if r["status"] == "PATH_NOT_FOUND"]
    approved = [r for r in ok if r["governance_gate"] == "APPROVED"]
    has_dr = [r for r in ok if r.get("has_deep_resolution")]

    # ── Duplicate-repo detection ────────────────────────────────────────────
    # Two repos with non-trivial content (files_scanned > 5) that produce
    # IDENTICAL files_scanned + functions + classes + resolved_calls +
    # unresolved_total are almost certainly the same underlying clone under
    # two different folder names (wrong clone URL, copy-paste folder, etc).
    # This is a near-zero-probability coincidence at these magnitudes.
    fingerprint_groups = {}
    for r in ok:
        if r["files_scanned"] <= 5:
            continue  # too small to be a meaningful fingerprint
        fp = (r["files_scanned"], r["functions"], r["classes"],
              r["resolved_calls"], r["unresolved_total"])
        fingerprint_groups.setdefault(fp, []).append(r["repo"])
    duplicate_groups = [repos for repos in fingerprint_groups.values() if len(repos) > 1]

    total_files = sum(r["files_scanned"] for r in ok)
    total_functions = sum(r["functions"] for r in ok)
    total_classes = sum(r["classes"] for r in ok)
    total_resolved = sum(r["resolved_calls"] for r in ok)
    total_unresolved = sum(r["unresolved_total"] for r in ok)
    total_dr_resolved = sum(r["dr_resolved_by_pipeline"] for r in ok)
    total_parse_errors = sum(r["parse_errors"] for r in ok)
    pkg_corrected = [r["repo"] for r in ok if r.get("package_root_corrected")]
    src_stripped = [r["repo"] for r in ok if r.get("src_layout_stripped")]

    lines = []
    lines.append("# Module 2 + Deep Resolution — Full 69-Repo Corpus Validation")
    lines.append("")
    lines.append("**CodeTruth Agent V3 — Module 2 — Repository Graph Engine + Deep Resolution Pipeline**")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---|")
    lines.append(f"| Total repos | {len(results)} |")
    lines.append(f"| OK (no crash) | {len(ok)} / {len(results)} |")
    lines.append(f"| Crashes | {len(crashed)} |")
    lines.append(f"| Path not found (skipped) | {len(not_found)} |")
    lines.append(f"| Governance APPROVED | {len(approved)} / {len(ok)} |")
    lines.append(f"| Deep resolution wired | {len(has_dr)} / {len(ok)} repos |")
    lines.append(f"| Total Python files scanned | {total_files:,} |")
    lines.append(f"| Total functions found (V3-004) | {total_functions:,} |")
    lines.append(f"| Total classes found (V3-005) | {total_classes:,} |")
    lines.append(f"| Total resolved calls (core) | {total_resolved:,} |")
    lines.append(f"| Total unresolved (core) | {total_unresolved:,} |")
    lines.append(f"| Total additionally resolved (deep_resolution) | {total_dr_resolved:,} |")
    lines.append(f"| Total parse errors | {total_parse_errors} |")
    lines.append(f"| D-008 package-root corrected | {pkg_corrected} |")
    lines.append(f"| src/-layout stripped | {src_stripped} |")
    lines.append("")

    if duplicate_groups:
        lines.append("## ⚠ DUPLICATE REPO WARNING")
        lines.append("")
        lines.append(
            "The following repo groups produced IDENTICAL files_scanned, "
            "functions, classes, resolved_calls, and unresolved_total. "
            "This is statistically near-impossible by coincidence for repos "
            "with more than a handful of files — it almost always means two "
            "folder names point at the same underlying clone (wrong clone "
            "URL, copy-paste folder, or symlink). **Counts below and any "
            "corpus totals are unreliable until this is resolved** — verify "
            "each group's `git remote -v` and re-clone the incorrect one(s)."
        )
        lines.append("")
        for group in duplicate_groups:
            lines.append(f"- {' == '.join(group)}")
        lines.append("")

    if crashed:
        lines.append("## Crashes")
        lines.append("")
        lines.append("| Repo | Error |")
        lines.append("|---|---|")
        for r in crashed:
            lines.append(f"| {r['repo']} | {r['error']} |")
        lines.append("")

    lines.append("## Per-Repo Results — Core Engine")
    lines.append("")
    lines.append("| Repo | Files | Functions | Classes | Resolved Calls | Unresolved | Resolved% | Gate | D-008 | src/ |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in ok:
        d008 = "✓" if r.get("package_root_corrected") else ""
        src = "✓" if r.get("src_layout_stripped") else ""
        lines.append(
            f"| {r['repo']} | {r['files_scanned']} | {r['functions']} | "
            f"{r['classes']} | {r['resolved_calls']} | {r['unresolved_total']} | "
            f"{r['resolved_pct']}% | {r['governance_gate']} | {d008} | {src} |"
        )
    lines.append("")

    if has_dr:
        lines.append("## Per-Repo Results — Deep Resolution")
        lines.append("")
        lines.append("| Repo | builtin_type | constructor | factory | property | inheritance | reflection | Resolved | Remaining | Reduction% |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|")
        for r in has_dr:
            lines.append(
                f"| {r['repo']} | {r['dr_builtin_type']} | {r['dr_constructor']} | "
                f"{r['dr_factory']} | {r['dr_property']} | {r['dr_inheritance']} | "
                f"{r['dr_reflection']} | {r['dr_resolved_by_pipeline']} | "
                f"{r['dr_remaining_unresolved']} | {r['dr_reduction_pct']}% |"
            )
        lines.append("")
        lines.append("### Honest Yield Disclosure")
        lines.append("")
        lines.append(
            "Deep resolution yield is intentionally uneven across repos. "
            "builtin_type resolves the most (method calls on str/list/dict/etc. variables). "
            "constructor and inheritance resolvers fire substantially only on large, "
            "object-oriented codebases. factory and reflection resolvers show minimal "
            "yield across most repos tested so far. "
            "Every resolution traces back to a provable AST structural source — "
            "no probabilistic guessing."
        )
        lines.append("")

    lines.append("## Layout Correction Summary")
    lines.append("")
    lines.append(f"- **Standard layout** (no correction needed): {len(ok) - len(pkg_corrected) - len(src_stripped)} repos")
    lines.append(f"- **D-008 package-root corrected**: {len(pkg_corrected)} repos — {pkg_corrected}")
    lines.append(f"- **src/-layout stripped**: {len(src_stripped)} repos — {src_stripped}")
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
        print(f"ERROR: No repos found in {CLONED_REPOS_DIR}")
        print("Edit CLONED_REPOS_DIR at the top of this script.")
        sys.exit(1)

    print(f"Found {len(repo_dirs)} repo(s) in {CLONED_REPOS_DIR}")
    print(f"Output: {OUTPUT_DIR}")
    print()

    results = []
    for repo_path in repo_dirs:
        repo_name = os.path.basename(repo_path.rstrip("\\/"))
        print(f"Scanning: {repo_name} ...", end=" ", flush=True)

        summary = scan_one(repo_path)
        results.append(summary)

        if summary["status"] == "OK":
            dr_info = ""
            if summary["has_deep_resolution"]:
                dr_info = (f" | deep_res: {summary['dr_resolved_by_pipeline']} resolved "
                           f"({summary['dr_reduction_pct']}% reduction)")
            print(
                f"OK ({summary['files_scanned']} files, "
                f"{summary['resolved_calls']} resolved, "
                f"{summary['unresolved_total']} unresolved, "
                f"{summary['governance_gate']}){dr_info}"
            )
        else:
            print(f"{summary['status']}: {summary.get('error', '')}")

    # ── Write outputs ──────────────────────────────────────────────────────
    json_path = os.path.join(OUTPUT_DIR, "DEEP_RESOLUTION_FULL_SUMMARY.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    csv_fieldnames = [
        "repo", "status", "elapsed_s", "files_scanned", "modules_parsed",
        "functions", "classes", "external_deps", "resolved_calls",
        "unresolved_total", "resolved_pct", "governance_gate", "parse_errors",
        "attribute_call", "name_call_unresolved", "self_method_not_found",
        "package_root_corrected", "src_layout_stripped", "return_type_table_size",
        "has_deep_resolution",
        "dr_builtin_type", "dr_constructor", "dr_factory", "dr_property",
        "dr_inheritance", "dr_reflection", "dr_resolved_by_pipeline",
        "dr_remaining_unresolved", "dr_reduction_pct",
        "factory_named_any_return", "factory_named_class_return",
        "error",
    ]
    csv_path = os.path.join(OUTPUT_DIR, "DEEP_RESOLUTION_FULL_SUMMARY.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fieldnames)
        writer.writeheader()
        for r in results:
            row = {k: r.get(k, "") for k in csv_fieldnames}
            writer.writerow(row)

    md_path = os.path.join(OUTPUT_DIR, "DEEP_RESOLUTION_FULL_SUMMARY.md")
    write_markdown(results, md_path)

    # ── Final tally ────────────────────────────────────────────────────────
    ok = [r for r in results if r["status"] == "OK"]
    crashed = [r for r in results if r["status"] == "CRASH"]
    approved = [r for r in ok if r["governance_gate"] == "APPROVED"]
    has_dr = [r for r in ok if r.get("has_deep_resolution")]

    # ── Duplicate-repo check (console) ──────────────────────────────────────
    fingerprint_groups = {}
    for r in ok:
        if r["files_scanned"] <= 5:
            continue
        fp = (r["files_scanned"], r["functions"], r["classes"],
              r["resolved_calls"], r["unresolved_total"])
        fingerprint_groups.setdefault(fp, []).append(r["repo"])
    duplicate_groups = [repos for repos in fingerprint_groups.values() if len(repos) > 1]

    print()
    print("=" * 65)
    print(f"TOTAL REPOS         : {len(results)}")
    print(f"OK (no crash)       : {len(ok)}")
    print(f"CRASHED             : {len(crashed)}")
    print(f"Governance APPROVED : {len(approved)} / {len(ok)}")
    print(f"Deep resolution     : {len(has_dr)} / {len(ok)} repos")
    print(f"Total files scanned : {sum(r['files_scanned'] for r in ok):,}")
    print(f"Total resolved calls: {sum(r['resolved_calls'] for r in ok):,}")
    print(f"Total DR resolved   : {sum(r['dr_resolved_by_pipeline'] for r in ok):,}")
    print(f"D-008 corrected     : {[r['repo'] for r in ok if r.get('package_root_corrected')]}")
    print(f"src/ stripped       : {[r['repo'] for r in ok if r.get('src_layout_stripped')]}")
    if duplicate_groups:
        print("=" * 65)
        print("⚠  WARNING: POSSIBLE DUPLICATE REPO CLONES DETECTED")
        for group in duplicate_groups:
            print(f"   {' == '.join(group)}  (identical metrics — check git remote -v)")
        print("   Corpus totals above include this duplication until fixed.")
    print("=" * 65)
    print(f"\nOutputs saved to: {OUTPUT_DIR}")
    print(f"  {json_path}")
    print(f"  {csv_path}")
    print(f"  {md_path}")
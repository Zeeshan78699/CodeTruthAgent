"""
verify_pipeline_integrity.py
Gap 4: Automated Divergence Audit Gate

Cross-references Module 1's per-repo file manifest against Module 2's
MODULE2_FULL_SUMMARY.json to confirm no Python assets are silently dropped
between modules.

Module 1's FULL_DOMAIN_SUMMARY.json (in v3/outputs/real_scans/) is expected
to contain, per repo, a "total_python_files" field (matching
RepositoryCognitionReport.total_python_files).

Module 2's MODULE2_FULL_SUMMARY.json contains "files_scanned" per repo.

ASSERTION: Module1.total_python_files == Module2.files_scanned, for every
repo present in both summaries. Repos present in only one summary are
reported separately (not necessarily a failure - e.g. non-Python repos are
expected to be BLOCKED/absent in Module 2).

Usage:
    python v3/repository_graph/tests/verify_pipeline_integrity.py
"""

import os
import sys
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

MODULE1_SUMMARY = os.path.join(PROJECT_ROOT, "v3", "outputs", "real_scans", "FULL_DOMAIN_SUMMARY.json")
MODULE2_SUMMARY = os.path.join(PROJECT_ROOT, "v3", "outputs", "module2_graphs", "MODULE2_FULL_SUMMARY.json")


def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_module1_counts(data):
    """
    Module 1's FULL_DOMAIN_SUMMARY.json structure may be a list of per-repo
    dicts or a dict keyed by repo name - handle both, looking for a
    "total_python_files" (or "python_files") field and a repo identifier
    ("repository_root", "repo", or "name").
    """
    counts = {}
    if data is None:
        return counts

    records = data.values() if isinstance(data, dict) else data

    for rec in records:
        if not isinstance(rec, dict):
            continue
        repo_name = None
        for key in ("repo", "name", "repository_root"):
            if key in rec:
                repo_name = os.path.basename(str(rec[key]).rstrip("\\/"))
                break
        if repo_name is None:
            continue

        for key in ("total_python_files", "python_files"):
            if key in rec:
                counts[repo_name] = rec[key]
                break

    return counts


def extract_module2_counts(data):
    counts = {}
    if data is None:
        return counts
    for rec in data:
        if rec.get("status") == "OK":
            counts[rec["repo"]] = rec["files_scanned"]
    return counts


def main():
    mod1_data = load_json(MODULE1_SUMMARY)
    mod2_data = load_json(MODULE2_SUMMARY)

    if mod1_data is None:
        print(f"WARNING: Module 1 summary not found at {MODULE1_SUMMARY}")
        print("Cannot run divergence check without Module 1 data.")
        print("(This is informational - Module 2's own results are still valid.)")
        return 0

    if mod2_data is None:
        print(f"ERROR: Module 2 summary not found at {MODULE2_SUMMARY}")
        print("Run scan_all_repos_module2.py first.")
        return 1

    mod1_counts = extract_module1_counts(mod1_data)
    mod2_counts = extract_module2_counts(mod2_data)

    if not mod1_counts:
        print("WARNING: Could not extract per-repo Python file counts from "
              "Module 1's summary (unexpected schema). Skipping divergence check.")
        print(f"Module 1 summary keys/sample: "
              f"{list(mod1_data[0].keys()) if isinstance(mod1_data, list) and mod1_data else mod1_data}")
        return 0

    all_repos = sorted(set(mod1_counts) | set(mod2_counts))

    matches, mismatches, only_in_1, only_in_2 = [], [], [], []

    for repo in all_repos:
        m1 = mod1_counts.get(repo)
        m2 = mod2_counts.get(repo)
        if m1 is not None and m2 is not None:
            if m1 == m2:
                matches.append((repo, m1, m2))
            else:
                mismatches.append((repo, m1, m2))
        elif m1 is not None:
            only_in_1.append((repo, m1))
        else:
            only_in_2.append((repo, m2))

    print("=" * 70)
    print("MODULE 2 - DIVERGENCE AUDIT (Gap 4)")
    print("=" * 70)
    print(f"Repos compared: {len(all_repos)}")
    print(f"  Matching python-file counts: {len(matches)}")
    print(f"  MISMATCHES: {len(mismatches)}")
    print(f"  Only in Module 1 summary: {len(only_in_1)}")
    print(f"  Only in Module 2 summary: {len(only_in_2)}")
    print()

    if mismatches:
        print("MISMATCHES (Module1.total_python_files != Module2.files_scanned):")
        for repo, m1, m2 in mismatches:
            print(f"  {repo}: Module1={m1}  Module2={m2}  (diff={m2 - m1:+d})")
        print()

    if only_in_1:
        print("Only in Module 1 (likely BLOCKED/no-Python in Module 2 - check governance_gate):")
        for repo, m1 in only_in_1:
            print(f"  {repo}: Module1 reports {m1} python files")
        print()

    if only_in_2:
        print("Only in Module 2 (not found in Module 1 summary):")
        for repo, m2 in only_in_2:
            print(f"  {repo}: Module2 scanned {m2} files")
        print()

    print("=" * 70)
    if mismatches:
        print(f"RESULT: {len(mismatches)} divergence(s) found. "
              f"Pipeline integrity NOT fully sealed - investigate above.")
        return 1
    else:
        print(f"RESULT: 0 divergences across {len(matches)} comparable repos. "
              f"Module 1 <-> Module 2 file counts are consistent.")
        return 0


if __name__ == "__main__":
    sys.exit(main())

r"\s""""
Diagnostic — Investigate the 4 Bandit exec/eval findings on Django
that CodeTruth V2 did not flag.

Purpose:
    Bandit caught 3 B102 (exec_used) and 1 B307 (eval_used) findings on
    Django. CodeTruth's scan of the same codebase produced 0 BLOCK-
    severity findings. This script identifies the exact file and line
    of each Bandit finding so we can inspect them by hand and answer:

    "Why didn't CodeTruth flag these?"

How to use:
    python -m tests.intelligence.orchestration.diagnostic_django_exec_eval
"""

import json
from pathlib import Path

BANDIT_REPORT = Path(
    r"tests/output/v2/bandit_django_comparison_reports/bandit_raw_django.json"
)

DJANGO_ROOT = Path(r"C:\scratch\django\django")


def main():
    print("=" * 70)
    print("Diagnostic: Django Bandit exec/eval findings vs CodeTruth")
    print("=" * 70)

    if not BANDIT_REPORT.exists():
        print(f"ERROR: Bandit report not found at {BANDIT_REPORT}")
        return

    with open(BANDIT_REPORT, "r", encoding="utf-8") as f:
        bandit = json.load(f)

    # Filter for exec_used (B102) and eval_used (B307)
    findings = [
        issue for issue in bandit.get("results", [])
        if issue.get("test_id") in ("B102", "B307")
    ]
    print(f"\nFound {len(findings)} Bandit exec/eval findings on Django.\n")

    for i, issue in enumerate(findings, 1):
        filename = issue.get("filename", "")
        line_no = issue.get("line_number", 0)
        test_id = issue.get("test_id", "")
        test_name = issue.get("test_name", "")
        issue_text = issue.get("issue_text", "")
        code_excerpt = issue.get("code", "").strip()

        print(f"[{i}] {test_id} — {test_name}")
        print(f"    File: {filename}")
        print(f"    Line: {line_no}")
        print(f"    Issue: {issue_text}")
        print(f"    Code (Bandit excerpt):")
        for code_line in code_excerpt.split("\n"):
            print(f"        {code_line}")

        # Read the file from disk and show context lines
        try:
            file_path = Path(filename) if Path(filename).is_absolute() else \
                DJANGO_ROOT.parent / filename
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                start = max(0, line_no - 4)
                end = min(len(lines), line_no + 3)
                print(f"    Context (lines {start + 1} to {end}):")
                for ln in range(start, end):
                    marker = ">>>" if ln + 1 == line_no else "   "
                    print(f"        {marker} {ln + 1:5d}: {lines[ln].rstrip()}")
            else:
                print(f"    (Could not open file to show context)")
        except Exception as e:
            print(f"    (Error reading file: {e})")
        print()


if __name__ == "__main__":
    main()
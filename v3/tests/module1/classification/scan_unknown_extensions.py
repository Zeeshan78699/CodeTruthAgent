"""
========================================================================
scan_unknown_extensions.py
CodeTruth Agent V3 — Module 1 Utility

PURPOSE:
    Scans any repository and reports unknown file extensions
    not yet in language_registry_expansion.py.

    Run this BEFORE adding a new domain to the registry.
    It tells you exactly what to add.

USAGE:
    python scan_unknown_extensions.py C:\\repos\\v3\\pydicom
    python scan_unknown_extensions.py C:\\repos\\v3\\rclpy
    python scan_unknown_extensions.py C:\\repos\\v3\\MetPy

OUTPUT:
    Console report + saves scan_results.json
========================================================================
"""

import sys
import json
from pathlib import Path
from collections import Counter
from datetime import datetime, UTC

# ------------------------------------------------------------------
# Bootstrap V3 path
# ------------------------------------------------------------------
V3_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(V3_ROOT))

try:
    from repository_cognition.module1_extensions.language_registry_expansion import (
        LANGUAGE_REGISTRY_EXPANSION,
        filter_genuine_unknown_extensions,
        get_extension_summary,
    )
    REGISTRY_LOADED = True
except ImportError:
    LANGUAGE_REGISTRY_EXPANSION = {}
    REGISTRY_LOADED = False

# ------------------------------------------------------------------
# Scanner
# ------------------------------------------------------------------

def scan_repository(repo_path: str) -> dict:
    root = Path(repo_path)

    if not root.exists():
        print(f"ERROR: Path does not exist: {repo_path}")
        sys.exit(1)

    print(f"\nScanning: {root}")
    print("-" * 60)

    ext_counter: Counter = Counter()
    total_files = 0

    for item in root.rglob("*"):
        if not item.is_file():
            continue
        total_files += 1
        suffix = item.suffix.lower()
        if suffix:
            ext_counter[suffix] += 1

    all_extensions      = list(ext_counter.keys())
    known               = set(LANGUAGE_REGISTRY_EXPANSION.keys())
    covered, genuine    = filter_genuine_unknown_extensions(all_extensions) \
                          if REGISTRY_LOADED \
                          else ([], all_extensions)

    return {
        "repository":       str(root.name),
        "repo_path":        str(root),
        "scan_date":        datetime.now(UTC).isoformat(),
        "total_files":      total_files,
        "total_extensions": len(all_extensions),
        "extension_counts": dict(ext_counter.most_common()),
        "covered_by_registry": sorted(covered),
        "genuine_unknowns":    sorted(genuine),
        "registry_size":       len(LANGUAGE_REGISTRY_EXPANSION),
    }


def print_report(result: dict) -> None:
    sep  = "=" * 70
    sep2 = "-" * 40

    print(f"\n{sep}")
    print(f"CODETRUTH V3 — Extension Scanner")
    print(f"Repository : {result['repository']}")
    print(f"Scan Date  : {result['scan_date'][:10]}")
    print(sep)

    print(f"\nRepository Statistics")
    print(sep2)
    print(f"  Total Files      : {result['total_files']:,}")
    print(f"  Total Extensions : {result['total_extensions']}")

    print(f"\nExtension Registry Coverage")
    print(sep2)
    print(f"  Registry Size    : {result['registry_size']} entries")
    print(f"  Already Covered  : {len(result['covered_by_registry'])}")
    print(f"    {result['covered_by_registry']}")

    print(f"\nGenuine Unknowns — ADD THESE to language_registry_expansion.py")
    print(sep2)

    if result["genuine_unknowns"]:
        for ext in result["genuine_unknowns"]:
            count = result["extension_counts"].get(ext, 0)
            print(f"  {ext:<15} : {count:>5} files")

        print(f"\n  Copy-paste template:")
        print(f"  # ----------------------------------------------------------")
        print(f"  # {result['repository']} — discovered {result['scan_date'][:10]}")
        print(f"  # ----------------------------------------------------------")
        for ext in result["genuine_unknowns"]:
            print(f'  "{ext}": "DESCRIPTION HERE",')
    else:
        print("  None — registry covers all extensions in this repository.")

    print(f"\n{sep}")
    print(f"RESULT: {len(result['genuine_unknowns'])} extension(s) need adding")
    print(sep)


def save_results(result: dict, output_path: Path) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"\nResults saved --> {output_path}")


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scan_unknown_extensions.py <repo_path>")
        print("Example: python scan_unknown_extensions.py C:\\repos\\v3\\pydicom")
        sys.exit(1)

    repo_path = sys.argv[1]
    result    = scan_repository(repo_path)
    print_report(result)

    output_dir = Path(__file__).parent / "evidence"
    output_dir.mkdir(parents=True, exist_ok=True)
    save_results(
        result,
        output_dir / f"scan_{result['repository']}_{result['scan_date'][:10]}.json"
    )

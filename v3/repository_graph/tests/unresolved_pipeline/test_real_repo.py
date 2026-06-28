"""
test_real_repo.py

Quick real-repo test harness for the integrated Module 2 + deep_resolution
pipeline. Run against any real Python repo on disk:

    python test_real_repo.py /path/to/some/repo

Prints the same shape of output used throughout validation so far:
files_scanned, package-root/src-layout correction status, deep_resolution
resolver_results, timing, and a short factory-specific diagnostic (since
that's the resolver still being investigated for real-world value).
"""

import sys
import time
from pathlib import Path


def _find_and_add_project_root():
    """
    Makes this script work no matter which folder it's placed in
    (v3/tests, v3/repository_graph/tests, etc.) - walks up from this
    file's own location until it finds the directory that directly
    contains the v3/ package, then adds THAT to sys.path so
    `from v3.repository_graph...` resolves correctly regardless of
    where the script was invoked from or where it lives on disk.
    """
    here = Path(__file__).resolve().parent
    for candidate in [here, *here.parents]:
        if (candidate / "v3" / "repository_graph").is_dir():
            sys.path.insert(0, str(candidate))
            return
    raise RuntimeError(
        "Could not find the 'v3' package by walking up from this script's "
        "location - make sure this file lives somewhere inside your "
        "CodeTruthAgent project tree."
    )


_find_and_add_project_root()


def main():
    if len(sys.argv) != 2:
        print("Usage: python test_real_repo.py <path_to_repo>")
        sys.exit(1)

    repo_path = sys.argv[1]

    from v3.repository_graph.languages.python_adapter import PythonAdapter

    print(f"Scanning: {repo_path}")
    start = time.time()
    report = PythonAdapter().scan(repo_root=repo_path, file_paths=[])
    elapsed = time.time() - start

    print(f"\n--- Core engine ---")
    print(f"scan() elapsed: {elapsed:.2f}s")
    print(f"files_scanned: {report.get('files_scanned')}")
    print(f"package_root_corrected: {report.get('package_root_corrected')}")
    print(f"src_layout_prefix_stripped: {report.get('src_layout_prefix_stripped')}")
    print(f"unresolved count: {len(report.get('unresolved', []))}")
    print(f"return_type_table_size: {report.get('return_type_table_size')}")

    dr = report.get("deep_resolution", {})
    print(f"\n--- Deep resolution ---")
    print(f"resolver_results: {dr.get('resolver_results')}")
    final = dr.get("final", {})
    print(f"resolved_by_pipeline: {final.get('resolved_by_pipeline')}")
    print(f"remaining_unresolved: {final.get('remaining_unresolved')}")
    print(f"reduction_pct: {final.get('reduction_pct')}%")

    # Factory-specific diagnostic: how many provable-return-type functions
    # are even factory-named AND return a local class (the precondition
    # factory_return_engine needs to ever resolve anything).
    rt = report.get("return_type_table", {})
    factory_prefixes = ("create_", "build_", "get_", "make_", "load_")
    candidates = []
    for full_id, type_info in rt.items():
        bare = full_id.split(".")[-1].lstrip("_")
        if any(bare.startswith(p) for p in factory_prefixes):
            candidates.append((full_id, type_info))

    class_candidates = [c for c in candidates if c[1] and c[1][0] == "class"]
    print(f"\n--- Factory diagnostic ---")
    print(f"Factory-named functions with ANY provable return type: {len(candidates)}")
    print(f"Of those, returning a local CLASS (factory_return_engine's precondition): {len(class_candidates)}")
    for full_id, type_info in class_candidates[:10]:
        print(f"  {full_id} -> {type_info}")


if __name__ == "__main__":
    main()
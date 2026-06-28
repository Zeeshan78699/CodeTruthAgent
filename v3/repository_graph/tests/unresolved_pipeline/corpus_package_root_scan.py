"""
corpus_package_root_scan.py

Runs both package-root detection mechanisms across every repo in a
corpus directory and reports which ones each one actually helps:

  - package_root.detect_package_root()      (D-008, existing, frozen)
  - subtree_naming.detect_src_prefix_to_strip()  (new, today's fix)

Purpose: find out how many of the 69 repos genuinely benefit from the
new src-layout fix, versus it only mattering for Flask. Dynamic by
design - takes any corpus directory, makes no assumption about which
repos are inside it or what their package names are.

Usage:
    python -m v3.repository_graph.tests.unresolved_pipeline.corpus_package_root_scan "C:\\repos\\v3"
"""

import os
import sys
import time
import warnings

# Source files across a large corpus often contain invalid escape
# sequences in string literals (e.g. "\d", "\w" outside raw strings) -
# ast.parse emits a SyntaxWarning for these, which is harmless but
# floods output across 69 repos. Suppressed here only; doesn't affect
# parsing correctness, just console noise.
warnings.filterwarnings("ignore", category=SyntaxWarning)

from v3.repository_graph import package_root
from v3.repository_graph import subtree_naming


def scan_corpus(corpus_dir):
    results = []
    repo_names = sorted(
        d for d in os.listdir(corpus_dir)
        if os.path.isdir(os.path.join(corpus_dir, d)) and not d.startswith(".")
    )

    total = len(repo_names)
    for i, name in enumerate(repo_names, start=1):
        repo_path = os.path.join(corpus_dir, name)
        print(f"[{i}/{total}] Scanning {name}...", flush=True)
        start = time.time()

        entry = {"repo": name, "error": None,
                 "d008_corrected": False, "src_layout_prefix": None}
        try:
            effective_root, root_counts = package_root.detect_package_root_and_counts(repo_path)
            entry["d008_corrected"] = (effective_root != repo_path)

            if not entry["d008_corrected"]:
                # Only meaningful to check when D-008 didn't already
                # fire - same mutual-exclusivity rule python_adapter.py
                # applies. Reuses root_counts already computed above -
                # no second parse pass over the repo's files.
                entry["src_layout_prefix"] = subtree_naming.detect_src_prefix_to_strip(repo_path, root_counts=root_counts)
        except Exception as e:
            entry["error"] = f"{type(e).__name__}: {e}"

        elapsed = round(time.time() - start, 1)
        print(f"    done in {elapsed}s - "
              f"d008={entry['d008_corrected']} src_layout={entry['src_layout_prefix']}"
              f"{' ERROR: ' + entry['error'] if entry['error'] else ''}", flush=True)

        results.append(entry)

    return results


def main(corpus_dir):
    results = scan_corpus(corpus_dir)

    d008_hits = [r for r in results if r["d008_corrected"]]
    src_hits = [r for r in results if r["src_layout_prefix"]]
    neither = [r for r in results if not r["d008_corrected"] and not r["src_layout_prefix"] and not r["error"]]
    errors = [r for r in results if r["error"]]

    print("=" * 80)
    print(f"CORPUS PACKAGE-ROOT SCAN ({len(results)} repos in {corpus_dir})")
    print("=" * 80)
    print(f"D-008 root-shift fires:     {len(d008_hits)}")
    print(f"src-layout fix fires:       {len(src_hits)}")
    print(f"Neither (already correct):  {len(neither)}")
    print(f"Errors during scan:         {len(errors)}")
    print("=" * 80)

    if src_hits:
        print()
        print("Repos the NEW src-layout fix actually helps:")
        for r in src_hits:
            print(f"  - {r['repo']}  (prefix: {r['src_layout_prefix']})")

    if d008_hits:
        print()
        print("Repos D-008's existing fix already helps:")
        for r in d008_hits:
            print(f"  - {r['repo']}")

    if errors:
        print()
        print("Repos that errored during scan:")
        for r in errors:
            print(f"  - {r['repo']}: {r['error']}")

    print("=" * 80)
    return results


if __name__ == "__main__":
    corpus = sys.argv[1] if len(sys.argv) > 1 else r"C:\repos\v3"
    main(corpus)
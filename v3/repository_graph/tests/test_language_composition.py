"""
test_language_composition.py
Quick check for the multi-language scaffold (languages/ package).

Run from project root:
    python v3\\repository_graph\\tests\\test_language_composition.py [optional_repo_path]

If no path given, scans the project root itself.
"""

import sys
import os
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from v3.repository_graph.graph_engine import build_repository_graph
from v3.repository_graph.languages import ADAPTERS, classify_files


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else PROJECT_ROOT

    print("Registered language adapters:")
    for a in ADAPTERS:
        status = "IMPLEMENTED" if a.is_implemented() else "stub (not implemented)"
        print(f"  {a.language_name:<12} {sorted(a.file_extensions)}  -> {status}")
    print()

    print(f"Classifying files under: {target}\n")
    composition = classify_files(target)
    for lang, info in composition.items():
        if lang == "_unclassified":
            print(f"_other_extensions: {info['extensions']}")
        else:
            print(f"{lang:<12} files={len(info['files'])}  "
                  f"implemented={info['adapter'].is_implemented()}")

    print()
    print("Full report's language_composition field (via build_repository_graph):")
    report = build_repository_graph(target)
    print(json.dumps(report["language_composition"], indent=2))
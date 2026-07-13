"""
test_reflection_fix_isolated.py

Standalone, synthetic proof that the reflection_resolver.py fix
(reflection_name extraction) actually works - independent of whether
any of the 69 real-world corpus repos happen to contain this pattern.

0/69 on real repos is plausible (getattr(self, "literal") is a rare
idiom - most code that knows the literal name at write-time just calls
self.method_name() directly). This test settles whether that's because
the fix is correct-but-rarely-triggered, or still broken.

Run from project root:
    python v3\\repository_graph\\tests\\test_reflection_fix_isolated.py
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from v3.repository_graph.languages.python_adapter import PythonAdapter


SYNTHETIC_REPO = {
    "handler.py": (
        "class EventHandler:\n"
        "    def on_click(self):\n"
        "        return 'clicked'\n"
        "\n"
        "    def dispatch(self):\n"
        "        # The exact pattern reflection_resolver.py should now catch:\n"
        "        # literal string, called on self\n"
        "        handler = getattr(self, 'on_click')\n"
        "        return handler()\n"
        "\n"
        "    def dispatch_direct(self):\n"
        "        # Same pattern, inline call - also a literal getattr(self, ...)\n"
        "        return getattr(self, 'on_click')()\n"
    ),
}


def write_files(root, files):
    for rel_path, content in files.items():
        full_path = os.path.join(root, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)


def main():
    tmpdir = tempfile.mkdtemp(prefix="reflection_fix_test_")
    try:
        write_files(tmpdir, SYNTHETIC_REPO)

        report = PythonAdapter().scan(repo_root=tmpdir, file_paths=[])

        dr = report.get("deep_resolution", {})
        resolver_results = dr.get("resolver_results", {})
        reflection_count = resolver_results.get("reflection", 0)

        print("=" * 60)
        print("SYNTHETIC REFLECTION FIX TEST")
        print("=" * 60)
        print(f"files_scanned: {report.get('files_scanned')}")
        print(f"governance_gate: {report.get('governance_gate')}")
        print(f"resolver_results: {resolver_results}")
        print()

        if reflection_count > 0:
            print(f"PASS: dr_reflection = {reflection_count} (expected > 0)")
            print("The fix works. 0/69 on the real corpus means this pattern")
            print("is genuinely rare in those repos, not that the fix is broken.")
        else:
            print("FAIL: dr_reflection = 0 (expected > 0)")
            print("The fix is NOT resolving even this synthetic, textbook-shape")
            print("getattr(self, 'literal')() case. Something is still wrong -")
            print("check that this file actually replaced the deployed copy of")
            print("reflection_resolver.py, and that resolution_pipeline.py is")
            print("passing entries with a populated 'note' field containing")
            print("the literal text 'getattr'.")
            print()
            print("Unresolved entries for manual inspection:")
            for u in report.get("unresolved", []):
                print(f"  pattern={u.get('pattern')} note={u.get('note', '')[:80]}")

        print("=" * 60)

    finally:
        shutil.rmtree(tmpdir)


if __name__ == "__main__":
    main()

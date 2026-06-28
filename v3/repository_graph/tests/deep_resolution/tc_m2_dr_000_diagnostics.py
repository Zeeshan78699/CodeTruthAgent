"""
TC_M2_DR_000 — Deep Resolution Structure Diagnostics
Prints the full report structure from PythonAdapter().scan()
so we can map the correct keys for all resolver tests.
"""
import json, sys, pprint
from pathlib import Path

V3_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(V3_ROOT.parent))
sys.path.insert(0, str(V3_ROOT))

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "builtin_type"

FIXTURE_CODE = '''
def process_data(items: list, config: dict, label: str) -> str:
    items.append("new_item")
    items.extend(["a", "b"])
    value = config.get("key", "default")
    config.update({"new_key": "val"})
    upper = label.upper()
    parts = label.split("_")
    return "_".join(parts)
'''

def create_fixture():
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    (FIXTURE_DIR / "builtin_usage.py").write_text(FIXTURE_CODE)
    (FIXTURE_DIR / "__init__.py").write_text("")

create_fixture()

from v3.repository_graph.languages.python_adapter import PythonAdapter
report = PythonAdapter().scan(repo_root=str(FIXTURE_DIR), file_paths=[])

print("=" * 60)
print("TOP-LEVEL KEYS:")
print(list(report.keys()))

print("\n--- deep_resolution ---")
dr = report.get("deep_resolution", "NOT FOUND")
if isinstance(dr, dict):
    print("deep_resolution keys:", list(dr.keys()))
    for k, v in dr.items():
        print(f"  {k}: {v}")
else:
    print(dr)

print("\n--- All keys with 'dr' or 'resol' ---")
for k, v in report.items():
    if 'dr' in k.lower() or 'resol' in k.lower():
        print(f"  {k}: {v}")

print("\n--- Full report (truncated) ---")
safe = {k: str(v)[:120] for k, v in report.items()}
pprint.pprint(safe)

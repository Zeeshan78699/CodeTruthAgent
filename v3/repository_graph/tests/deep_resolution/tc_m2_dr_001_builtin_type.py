"""TC_M2_DR_001 — Deep Resolution: Builtin Type Resolver"""
import json, sys
from datetime import datetime as dt, UTC
from pathlib import Path

V3_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(V3_ROOT.parent))
sys.path.insert(0, str(V3_ROOT))

TEST_ID      = "TC_M2_DR_001"
EVIDENCE_DIR = Path(__file__).parent / "evidence"
FIXTURE_DIR  = Path(__file__).parent / "fixtures" / "builtin_type"

def to_json_safe(obj):
    if hasattr(obj, "__dict__"): return {k: to_json_safe(v) for k, v in obj.__dict__.items()}
    if isinstance(obj, (list, tuple)): return [to_json_safe(i) for i in obj]
    if isinstance(obj, dict): return {k: to_json_safe(v) for k, v in obj.items()}
    return str(obj) if not isinstance(obj, (int, float, bool, type(None))) else obj

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(to_json_safe(data), f, indent=2)

FIXTURE_CODE = "def process(items: list, config: dict, label: str) -> str:\n    items.append('x')\n    items.extend(['a','b'])\n    items.sort()\n    v = config.get('k','d')\n    config.update({'n':'v'})\n    u = label.upper()\n    p = label.split('_')\n    s = label.strip()\n    return '_'.join(p)\n\ndef transform(d: dict) -> list:\n    out = []\n    for k, v in d.items():\n        out.append(f'{k}={v}')\n    out.sort()\n    return out\n"

def create_fixture():
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    (FIXTURE_DIR / "builtin_usage.py").write_text(FIXTURE_CODE)
    (FIXTURE_DIR / "__init__.py").write_text("")
    print(f"Fixture: {FIXTURE_DIR}")

def save_markdown(passed, result, note=""):
    status = "PASS" if passed else "FAIL"
    md = Path(__file__).with_suffix(".md")
    lines = [
        "# TC_M2_DR_001 — Builtin Type Resolver",
        "", "| Field | Value |", "|---|---|",
        f"| Status | {status} |",
        f"| Date | {dt.now(UTC).date().isoformat()} |",
        "| Resolver | builtin_type |",
        "", "## Results", "", "| Metric | Value |", "|---|---|",
        f"| baseline_unresolved | {result.get('baseline_unresolved', 'N/A')} |",
        f"| dr_builtin_type | {result.get('dr_builtin_type', 'N/A')} |",
        f"| dr_resolved_by_pipeline | {result.get('dr_resolved_by_pipeline', 'N/A')} |",
        f"| dr_reduction_pct | {result.get('dr_reduction_pct', 'N/A')} |",
    ]
    if note:
        lines += ["", "## Notes", "", note]
    lines += [
        "", "## Requirement Traceability",
        "", "| Requirement | Status |", "|---|---|",
        f"| DR-001 Builtin Type Resolver | {status} |",
    ]
    md.write_text("\n".join(lines), encoding="utf-8")
    print(f"Evidence saved --> {md}")

def test_tc_m2_dr_001():
    print("=" * 80)
    print("TC_M2_DR_001 — Deep Resolution: Builtin Type Resolver")
    print("=" * 80)
    create_fixture()

    from v3.repository_graph.languages.python_adapter import PythonAdapter
    report = PythonAdapter().scan(repo_root=str(FIXTURE_DIR), file_paths=[])
    dr   = report.get("deep_resolution", {})
    rr   = dr.get("resolver_results", {})
    fin  = dr.get("final", {})
    cls  = dr.get("classification", {})
    cc   = cls.get("cause_counts", {})

    result = {
        "dr_builtin_type":         rr.get("builtin_type", 0),
        "dr_constructor":          rr.get("constructor", 0),
        "dr_factory":              rr.get("factory", 0),
        "dr_property":             rr.get("property", 0),
        "dr_inheritance":          rr.get("inheritance", 0),
        "dr_reflection":           rr.get("reflection", 0),
        "dr_resolved_by_pipeline": fin.get("resolved_by_pipeline", 0),
        "dr_remaining_unresolved": fin.get("remaining_unresolved", 0),
        "dr_reduction_pct":        fin.get("reduction_pct", 0.0),
        "baseline_unresolved":     dr.get("baseline_unresolved", 0),
        "builtin_like_classified": cc.get("builtin_like", 0),
        "facts_extracted":         dr.get("facts_extracted", 0),
    }

    print("\nRESULTS\n" + "-" * 60)
    print(f"     baseline_unresolved      : {result['baseline_unresolved']}")
    print(f"     dr_builtin_type         : {result['dr_builtin_type']}")
    print(f"     dr_resolved_by_pipeline : {result['dr_resolved_by_pipeline']}")
    print(f"     dr_reduction_pct        : {result['dr_reduction_pct']}")

    print("\nASSERTION\n" + "-" * 60)
    val = result["dr_builtin_type"]
    assert val > 0, f"[DR-001] dr_builtin_type = {val} — resolver not working on fixture"
    print(f"PASS  dr_builtin_type = {val} > 0")
    note = ""

    save_json(EVIDENCE_DIR / f"{TEST_ID.lower()}_result.json", result)
    save_markdown(passed=True, result=result, note=note)
    print("\nFINAL RESULT\n" + "-" * 60 + "\nPASS")
    return True

if __name__ == "__main__":
    try:
        test_tc_m2_dr_001()
    except (AssertionError, Exception) as exc:
        import traceback; traceback.print_exc(); sys.exit(1)

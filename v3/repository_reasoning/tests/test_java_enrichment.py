"""Proves 3A edges merged into the call graph make 3B chain ACROSS files.
Run from /home/claude: python test_java_enrichment.py"""
from v3.repository_reasoning.reasoning_queries import from_adapter_report, build_reverse_index
from v3.repository_reasoning import advanced_reasoning as AR

# Simulate: adapter resolved only same-file A.run -> A.helper. 3A adds the
# cross-file edge A.helper -> B.save. Enriched graph: run -> helper -> save.
BASE = {"call_graph": {
    "modA": [{"caller": "modA.A.run", "callee": "modA.A.helper",
              "lineno": 1, "resolution": "self_method_call"}],
}}
NEW = [{"caller": "modA.A.helper", "callee": "modB.B.save",
        "lineno": 2, "resolution": "java_3a_type_resolved"}]


def run():
    f = []
    # before enrichment: impact of B.save is empty (adapter never linked it)
    before = from_adapter_report(BASE, language="java")
    if before.impact_of("modB.B.save")["count"] != 0:
        f.append("baseline should not reach B.save")

    # enrich
    enr = dict(BASE); cg = dict(BASE["call_graph"])
    cg["__java_3a_type_resolved__"] = NEW; enr["call_graph"] = cg
    after = from_adapter_report(enr, language="java")

    # now B.save is reached: helper (depth1) and run (depth2) — CROSS-FILE chain
    ibd = AR.impact_by_depth("modB.B.save", after.rev)
    if ibd["by_depth"].get(1) != ["modA.A.helper"]:
        f.append(f"depth1 = {ibd['by_depth'].get(1)}")
    if ibd["by_depth"].get(2) != ["modA.A.run"]:
        f.append(f"depth2 = {ibd['by_depth'].get(2)} (transitive cross-file chain missing)")

    sp = AR.shortest_path("modA.A.run", "modB.B.save", after.fwd)
    if sp["path"] != ["modA.A.run", "modA.A.helper", "modB.B.save"]:
        f.append(f"cross-file path = {sp['path']}")

    if f:
        print("FAIL"); [print("  -", x) for x in f]; return 1
    print("PASS - 3A edges enrich the graph: 3B now chains run->helper->save "
          "ACROSS files (depth-2 impact + cross-file shortest path)")
    return 0

if __name__ == "__main__":
    raise SystemExit(run())

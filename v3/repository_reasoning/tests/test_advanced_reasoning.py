"""
Validates advanced_reasoning on a synthetic graph with HAND-COMPUTED answers.
Run: python -m v3.repository_reasoning.tests.test_advanced_reasoning

Graph (all edges internal):
    A -> B, A -> C        (A is the sole entry)
    B -> D, C -> D        (D reached via two paths)
    D -> E, E -> D        (D<->E mutual recursion, SCC {D,E})
    F -> G, G -> F        (isolated mutual recursion {F,G}, unreachable from A)
    H -> H                (direct self-recursion, unreachable from A)
"""
from v3.repository_reasoning.reasoning_queries import build_reverse_index
from v3.repository_reasoning import advanced_reasoning as AR


def fwd_of(edges):
    fwd = {}
    for c, e in edges:
        fwd.setdefault(c, []).append((e, "internal", 0, "x"))
        fwd.setdefault(e, fwd.get(e, []))
    return fwd

EDGES = [("A","B"),("A","C"),("B","D"),("C","D"),
         ("D","E"),("E","D"),("F","G"),("G","F"),("H","H")]
FWD = fwd_of(EDGES)
REV = build_reverse_index(FWD)


def run():
    f = []

    # --- recursion: mutual {D,E} and {F,G}; direct {H} ---
    rc = AR.recursion_clusters(FWD)
    mutual = {frozenset(c) for c in rc["mutual_recursion"]}
    if mutual != {frozenset({"D","E"}), frozenset({"F","G"})}:
        f.append(f"mutual_recursion = {rc['mutual_recursion']}")
    if rc["direct_recursion"] != ["H"]:
        f.append(f"direct_recursion = {rc['direct_recursion']}")
    # H is not a delegation name -> classified likely_real, not artifact
    if rc["direct_recursion_likely_real"] != ["H"] or rc["direct_recursion_likely_name_artifact"] != []:
        f.append(f"recursion precision split wrong: real={rc['direct_recursion_likely_real']} art={rc['direct_recursion_likely_name_artifact']}")

    # --- impact_by_depth(D): depth1={B,C,E}, depth2={A} ---
    ibd = AR.impact_by_depth("D", REV)
    if ibd["by_depth"].get(1) != ["B","C","E"]:
        f.append(f"impact depth1 = {ibd['by_depth'].get(1)}")
    if ibd["by_depth"].get(2) != ["A"]:
        f.append(f"impact depth2 = {ibd['by_depth'].get(2)}")

    # --- chokepoints: every path A..->E must pass through D (and A) ---
    cp = AR.chokepoints_for("E", FWD)
    if set(cp["chokepoints"]) != {"A","D"}:
        f.append(f"chokepoints(E) = {cp['chokepoints']}")
    # D's chokepoint is just A (reached via B or C, neither mandatory)
    cpD = AR.chokepoints_for("D", FWD)
    if set(cpD["chokepoints"]) != {"A"}:
        f.append(f"chokepoints(D) = {cpD['chokepoints']}")
    # F is unreachable from any entry (source-less cycle)
    cpF = AR.chokepoints_for("F", FWD)
    if cpF["reachable_from_entry"] is not False:
        f.append("F should be unreachable from entry")

    # --- hotspots: D has highest fan-in (3: B,C,E) ---
    hs = AR.hotspots(FWD, REV)
    if not hs["most_depended_on"] or hs["most_depended_on"][0]["node"] != "D" \
       or hs["most_depended_on"][0]["callers"] != 3:
        f.append(f"hotspots top fan-in = {hs['most_depended_on'][:1]}")

    # --- reachability + shortest path ---
    rf = AR.reachable_from("A", FWD)
    if set(rf["reachable"]) != {"B","C","D","E"}:
        f.append(f"reachable_from(A) = {rf['reachable']}")
    sp = AR.shortest_path("A","E",FWD)
    if sp["length"] != 3 or sp["path"][0] != "A" or sp["path"][-1] != "E":
        f.append(f"shortest_path A..E = {sp['path']}")
    sp2 = AR.shortest_path("A","H",FWD)
    if sp2["path"] is not None:
        f.append("A should not reach H")

    if f:
        print("FAIL"); [print("  -", x) for x in f]; return 1
    print("PASS - SCC/recursion, depth-impact, dominator chokepoints, hotspots, "
          "reachability, shortest-path all exact on hand-checked graph")
    return 0

if __name__ == "__main__":
    raise SystemExit(run())
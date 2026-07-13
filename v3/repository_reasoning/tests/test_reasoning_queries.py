"""Pure-core test for reasoning_queries on a synthetic call graph."""
from v3.repository_reasoning.reasoning_queries import (
    build_reverse_index, who_calls, paths_to, impact_of,
    depends_on_class, dead_code, paths_between,
)

# Graph:  A -> B -> D ;  C -> D ;  D -> <external>.x ;  Z (orphan, no inbound)
#         m.K.m1 -> D   (class K method depends on D)
FWD = {
    "A": [("B", "internal", 1, "l")],
    "B": [("D", "internal", 2, "l")],
    "C": [("D", "internal", 3, "l")],
    "D": [("<external>.x", "external", 4, "e")],
    "m.K.m1": [("D", "internal", 5, "l")],
    "Z": [("<builtin>.print", "builtin", 6, "b")],
}

def run():
    rev = build_reverse_index(FWD)
    f = []

    # who_calls D -> B, C, m.K.m1
    wc = who_calls("D", rev)
    if set(wc["direct_callers"]) != {"B", "C", "m.K.m1"}:
        f.append(f"who_calls D = {wc['direct_callers']}")

    # paths_to D -> includes A->B->D and C->D and m.K.m1->D
    pt = paths_to("D", rev)
    joined = {" -> ".join(p) for p in pt["paths"]}
    if "A -> B -> D" not in joined or "C -> D" not in joined:
        f.append(f"paths_to D = {joined}")

    # impact_of D -> A, B, C, m.K.m1 (everything that transitively calls D)
    im = impact_of("D", rev)
    if set(im["affected_callers"]) != {"A", "B", "C", "m.K.m1"}:
        f.append(f"impact_of D = {im['affected_callers']}")
    if im["label"] != "CALL_REACHABLE":
        f.append("impact label missing")

    # depends_on_class m.K -> external dependents of K's methods = none here,
    # but K.m1 depends on D; dependents of class K = callers of K.* = none
    dc = depends_on_class("m.K", FWD, rev)
    if dc["methods"] != ["m.K.m1"]:
        f.append(f"class methods = {dc['methods']}")

    # dead_code -> A, C, m.K.m1, Z have no inbound internal edges; A/C/Z are
    # candidates (m.K.m1 has none inbound either). None are entry points here.
    dead = dead_code(FWD, rev)
    deadset = set(dead["candidates"])
    if not {"A", "C", "Z"}.issubset(deadset):
        f.append(f"dead_code candidates = {deadset}")
    if "D" in deadset or "B" in deadset:
        f.append("D/B wrongly flagged dead")

    # paths_between A and D -> A->B->D
    pb = paths_between("A", "D", FWD)
    if [["A", "B", "D"]] != pb["paths"]:
        f.append(f"paths_between A..D = {pb['paths']}")

    # cycle safety: X->Y->X must not hang
    cyc = {"X": [("Y", "internal", 1, "l")], "Y": [("X", "internal", 2, "l")]}
    paths_to("X", build_reverse_index(cyc))  # must return
    paths_between("X", "Y", cyc)             # must return

    if f:
        print("FAIL"); [print("  -", x) for x in f]; return 1
    print("PASS - who_calls/paths_to/impact/depends_on_class/dead_code/paths_between + cycle-safe")
    return 0

if __name__ == "__main__":
    raise SystemExit(run())

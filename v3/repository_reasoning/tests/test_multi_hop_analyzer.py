"""
test_multi_hop_analyzer.py
Pure-core test for build_call_index + walk_chains: internal chaining,
external/builtin termination, cycle safety, depth bound.
Run:  python -m v3.repository_reasoning.tests.test_multi_hop_analyzer
"""

from v3.repository_reasoning.multi_hop_analyzer import build_call_index, walk_chains

# A -> B -> C -> <external>.lib.f   (linear, terminates external)
# B -> <builtin>.dict.get           (B also calls a builtin leaf)
# D -> E -> D                       (cycle)
EDGES = [
    {"caller": "m.A", "callee": "m.B", "lineno": 1, "resolution": "local"},
    {"caller": "m.B", "callee": "m.C", "lineno": 2, "resolution": "local"},
    {"caller": "m.B", "callee": "<builtin>.dict.get", "lineno": 3, "resolution": "b"},
    {"caller": "m.C", "callee": "<external>.lib.f", "lineno": 4, "resolution": "e"},
    {"caller": "m.D", "callee": "m.E", "lineno": 5, "resolution": "local"},
    {"caller": "m.E", "callee": "m.D", "lineno": 6, "resolution": "local"},
]


def _paths(chains):
    return {" -> ".join(h.get("to", "?") for h in ch if "to" in ch[0] or "to" in h)
            for ch in chains}


def run():
    idx = build_call_index(EDGES)
    failures = []

    # internal edges present, external/builtin classified
    kinds = {c: [k for _, k, _, _ in outs] for c, outs in idx.items()}
    if kinds.get("m.C") != ["external"]:
        failures.append(f"m.C callee kind {kinds.get('m.C')} != ['external']")
    if "builtin" not in kinds.get("m.B", []):
        failures.append("m.B should have a builtin leaf")

    # chains from A: A->B->C-><external> and A->B-><builtin>
    chains = walk_chains("m.A", idx, max_depth=6)
    paths = set()
    for ch in chains:
        paths.add(" -> ".join(h["to"] for h in ch if "to" in h))
    if "m.B -> m.C -> <external>.lib.f" not in paths:
        failures.append(f"missing external-terminated chain; got {paths}")
    if "m.B -> <builtin>.dict.get" not in paths:
        failures.append(f"missing builtin-terminated chain; got {paths}")

    # cycle: from D, must terminate and mark cycle, not hang
    dchains = walk_chains("m.D", idx, max_depth=10)
    if not any(ch[-1].get("cycle") for ch in dchains):
        failures.append("cycle D->E->D not detected/marked")

    # depth bound: deep linear chain truncates
    deep = [{"caller": f"n.{i}", "callee": f"n.{i+1}", "lineno": i, "resolution": "l"}
            for i in range(10)]
    dchains2 = walk_chains("n.0", build_call_index(deep), max_depth=3)
    if not any(ch[-1].get("truncated") for ch in dchains2):
        failures.append("depth bound did not truncate a 10-deep chain at max_depth=3")

    if failures:
        print("FAIL")
        for f in failures:
            print("  -", f)
        return 1
    print("PASS - internal/external/builtin + cycle + depth-bound")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())

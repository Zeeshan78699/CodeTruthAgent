"""The benchmark must (a) agree with networkx on correct reasoning and (b) DETECT
a planted error. A benchmark that can't fail is not a benchmark.
Run: python -m v3.repository_reasoning.tests.test_bench_against_networkx"""
from v3.repository_reasoning import bench_against_networkx as B
from v3.repository_reasoning import advanced_reasoning as AR


def fwd_of(edges):
    fwd = {}
    for c, e in edges:
        fwd.setdefault(c, []).append((e, "internal", 0, "x"))
        fwd.setdefault(e, fwd.get(e, []))
    return fwd

EDGES = [("A","B"),("A","C"),("B","D"),("C","D"),("D","E"),("E","D"),("F","G"),("G","F")]


def run():
    f = []
    res = B.bench(fwd_of(EDGES), sample=20)
    if not res["_summary"]["all_match"]:
        f.append(f"correct reasoning should match nx: {res}")

    # planted error must be caught
    orig = AR.reachable_from
    AR.reachable_from = lambda x, fwd, **k: {"reachable": []}
    res2 = B.bench(fwd_of(EDGES), sample=20)
    AR.reachable_from = orig
    if res2["_summary"]["all_match"]:
        f.append("benchmark failed to detect planted reachability error")

    if f:
        print("FAIL"); [print("  -", x) for x in f]; return 1
    print("PASS - differential bench agrees with networkx on correct reasoning "
          "AND detects a planted error (negative control)")
    return 0

if __name__ == "__main__":
    raise SystemExit(run())

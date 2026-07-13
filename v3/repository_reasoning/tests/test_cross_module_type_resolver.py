"""
test_cross_module_type_resolver.py
Pure-core test for resolve_reexport: chain following, cycle safety, hop bound.
Run:  python -m v3.repository_reasoning.tests.test_cross_module_type_resolver
"""

from v3.repository_reasoning.cross_module_type_resolver import resolve_reexport

DEFINED = {"django.http.response.HttpResponse", "a.b.real", "deep.d.X"}

# django.http.HttpResponse re-exports -> django.http.response.HttpResponse (defined)
EDGES = {
    "django.http.HttpResponse": "django.http.response.HttpResponse",
    # 3-hop chain: deep.a.X -> deep.b.X -> deep.c.X -> deep.d.X (defined)
    "deep.a.X": "deep.b.X",
    "deep.b.X": "deep.c.X",
    "deep.c.X": "deep.d.X",
    # cycle: cyc.a -> cyc.b -> cyc.a
    "cyc.a": "cyc.b",
    "cyc.b": "cyc.a",
    # dangling: points nowhere defined
    "dang.x": "nowhere.y",
}

CASES = [
    ("direct defined", "a.b.real", "a.b.real"),
    ("one hop reexport", "django.http.HttpResponse", "django.http.response.HttpResponse"),
    ("multi hop", "deep.a.X", "deep.d.X"),
    ("cycle -> None", "cyc.a", None),
    ("dangling -> None", "dang.x", None),
    ("unknown -> None", "not.in.graph", None),
]


def run():
    failures = []
    for name, sym, expect in CASES:
        got = resolve_reexport(sym, EDGES, DEFINED, max_hops=5)
        if got != expect:
            failures.append(f"[{name}] {sym} -> {got} != {expect}")

    # hop-bound: a 3-hop chain must fail when max_hops=2
    if resolve_reexport("deep.a.X", EDGES, DEFINED, max_hops=2) is not None:
        failures.append("hop-bound: 3-hop chain resolved under max_hops=2")

    if failures:
        print("FAIL")
        for f in failures:
            print("  -", f)
        return 1
    print(f"PASS - all {len(CASES)} cases + hop-bound")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())

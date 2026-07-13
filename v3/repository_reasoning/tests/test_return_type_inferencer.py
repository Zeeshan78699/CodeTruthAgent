"""
test_return_type_inferencer.py
Tests the PURE core (_fixed_point + _label_table) with synthetic atoms only -
no AST, no frozen engine - so the transitive / multi-path / poison / cycle
logic is verified in isolation. AST glue and from_repo are validated on a real
repo (FastAPI) separately.

Run:  python test_return_type_inferencer.py
"""

from v3.repository_reasoning.return_type_inferencer import _fixed_point, _label_table, RESOLVED, INFERRED, AMBIGUOUS

X  = ("class", "m", "X")
FS = ("class", "m", "FastService")
SS = ("class", "m", "StandardService")

# Synthetic repo of functions, each as a list of return atoms.
SEED = {
    "m.f_a": X,                       # frozen-resolved single  (return X())
}
ATOMS = {
    "m.f_a": [("type", X)],                       # already in seed -> RESOLVED
    "m.f_b": [("call", "m.f_a")],                 # transitive single -> INFERRED X
    "m.f_c": [("type", FS), ("type", SS)],        # multi-path known -> AMBIGUOUS {FS,SS}
    "m.f_d": [("unknown",)],                      # poison -> absent
    "m.f_e": [("call", "m.f_c")],                 # transitive of AMBIGUOUS -> AMBIGUOUS {FS,SS}
    "m.f_g": [("call", "m.f_d")],                 # depends on poison -> absent
    "m.f_bare": [("type", X), ("unknown",)],      # one unknown return poisons whole fn -> absent
    "m.f_h": [("call", "m.f_i")],                 # cycle h<->i, never grounds -> absent
    "m.f_i": [("call", "m.f_h")],
    "m.f_none": [],                               # no returns -> absent
}

EXPECT = {
    "m.f_a":  (RESOLVED,  X),
    "m.f_b":  (INFERRED,  X),
    "m.f_c":  (AMBIGUOUS, [FS, SS]),
    "m.f_e":  (AMBIGUOUS, [FS, SS]),
}
ABSENT = {"m.f_d", "m.f_g", "m.f_bare", "m.f_h", "m.f_i", "m.f_none"}


def run():
    determinate, used_call = _fixed_point(SEED, ATOMS, max_passes=10)
    table = _label_table(SEED, determinate, used_call)

    failures = []

    for fid, (label, typ) in EXPECT.items():
        if fid not in table:
            failures.append(f"{fid}: expected present, was ABSENT")
            continue
        rec = table[fid]
        if rec["label"] != label:
            failures.append(f"{fid}: label {rec['label']} != {label}")
        got = rec["type"]
        want = sorted(typ, key=repr) if isinstance(typ, list) else typ
        if got != want:
            failures.append(f"{fid}: type {got} != {want}")

    for fid in ABSENT:
        if fid in table:
            failures.append(f"{fid}: expected ABSENT, was {table[fid]}")

    # Additive guarantee: every seed entry preserved as RESOLVED with exact type.
    for fid, info in SEED.items():
        rec = table.get(fid)
        if not rec or rec["label"] != RESOLVED or rec["type"] != info:
            failures.append(f"{fid}: frozen seed not preserved -> {rec}")

    if failures:
        print("FAIL")
        for f in failures:
            print("  -", f)
        return 1

    print("PASS - all", len(EXPECT) + len(ABSENT), "cases")
    for fid in sorted(table):
        print(f"  {fid:12} {table[fid]['label']:10} {table[fid]['type']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())

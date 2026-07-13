"""
test_variable_type_propagator.py
Tests the pure resolve_env core with synthetic assignments only.
Run:  python -m v3.repository_reasoning.tests.test_variable_type_propagator
"""

from v3.repository_reasoning.variable_type_propagator import resolve_env
from v3.repository_reasoning.return_type_inferencer import RESOLVED, AMBIGUOUS

DB = ("class", "m", "DatabaseConnection")
OTH = ("class", "m", "OtherConnection")

TABLE = {"m.get_conn": DB}  # a function known to return DatabaseConnection

CASES = [
    # x = DatabaseConnection() ; x.method()   -> RESOLVED DB
    ("direct ctor", [("x", ("type", DB))], {"x": (RESOLVED, DB)}),
    # x = get_conn()  (call resolved via table) -> RESOLVED DB
    ("call via table", [("x", ("call", "m.get_conn"))], {"x": (RESOLVED, DB)}),
    # x = unknown_thing()                       -> absent (untyped)
    ("untyped", [("x", ("unknown",))], {}),
    # x = DB(); x = DB()  same type             -> RESOLVED DB
    ("same retype", [("x", ("type", DB)), ("x", ("type", DB))], {"x": (RESOLVED, DB)}),
    # x = DB(); x = OtherConnection()           -> AMBIGUOUS {DB,OTH}
    ("reassign diff", [("x", ("type", DB)), ("x", ("type", OTH))],
     {"x": (AMBIGUOUS, [DB, OTH])}),
    # x = DB(); x = something_unknown()         -> absent (poisoned by unknown)
    ("typed then unknown", [("x", ("type", DB)), ("x", ("unknown",))], {}),
    # call to a function NOT in table           -> absent
    ("call not in table", [("x", ("call", "m.missing"))], {}),
]


def run():
    failures = []
    for name, assigns, expect in CASES:
        env = resolve_env(assigns, TABLE)
        # check expected vars
        for var, (label, typ) in expect.items():
            if var not in env:
                failures.append(f"[{name}] {var} expected present, absent")
                continue
            if env[var]["label"] != label:
                failures.append(f"[{name}] {var} label {env[var]['label']} != {label}")
            want = sorted(typ, key=repr) if isinstance(typ, list) else typ
            if env[var]["type"] != want:
                failures.append(f"[{name}] {var} type {env[var]['type']} != {want}")
        # check nothing unexpected resolved
        for var in env:
            if var not in expect:
                failures.append(f"[{name}] {var} resolved but expected absent")

    if failures:
        print("FAIL")
        for f in failures:
            print("  -", f)
        return 1
    print(f"PASS - all {len(CASES)} cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())

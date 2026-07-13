"""
Validates from_adapter_report on a synthetic report shaped EXACTLY like the
Java adapter's output (call_graph = {module: [{caller,callee,lineno,resolution}]}),
and confirms a custom-shape (C#-like) report is rejected with guidance.
Run: python -m v3.repository_reasoning.tests.test_language_agnostic_3b
"""
from v3.repository_reasoning.reasoning_queries import from_adapter_report

# Shaped like java_adapter.scan() output: same-file resolved edges only.
JAVA_REPORT = {
    "call_graph": {
        "com.app.Service": [
            {"caller": "com.app.Service.Service.run",
             "callee": "com.app.Service.Service.helper",
             "lineno": 10, "resolution": "self_method_call"},
            {"caller": "com.app.Service.Service.run",
             "callee": "com.app.Service.Service.validate",
             "lineno": 11, "resolution": "self_method_call"},
        ],
        "com.app.Controller": [
            {"caller": "com.app.Controller.Controller.handle",
             "callee": "com.app.Service.Service.run",
             "lineno": 22, "resolution": "self_method_call"},
        ],
    },
    "function_graph": {}, "unresolved": [],
}

# Shaped like csharp_adapter output: NO call_graph (custom shape).
CSHARP_REPORT = {"method_calls": [], "deep_resolution": {}, "resolution": {}}


def run():
    f = []
    qs = from_adapter_report(JAVA_REPORT, language="java")

    wc = qs.who_calls("com.app.Service.Service.run")
    if set(wc["direct_callers"]) != {"com.app.Controller.Controller.handle"}:
        f.append(f"who_calls run = {wc['direct_callers']}")

    im = qs.impact_of("com.app.Service.Service.helper")
    if set(im["affected_callers"]) != {"com.app.Service.Service.run",
                                       "com.app.Controller.Controller.handle"}:
        f.append(f"impact helper = {im['affected_callers']}")

    pt = qs.paths_to("com.app.Service.Service.helper")
    joined = {" -> ".join(p) for p in pt["paths"]}
    if not any("com.app.Controller.Controller.handle -> com.app.Service.Service.run -> com.app.Service.Service.helper" == p for p in joined):
        f.append(f"paths_to helper = {joined}")

    dc = qs.depends_on_class("com.app.Service.Service")
    if "com.app.Controller.Controller.handle" not in dc["external_dependents"]:
        f.append(f"depends_on_class = {dc['external_dependents']}")

    st = qs.stats()
    if st["internal_edges"] != 3:
        f.append(f"stats internal_edges {st['internal_edges']} != 3")

    # custom-shape rejection
    try:
        from_adapter_report(CSHARP_REPORT, language="csharp")
        f.append("C#-shape report should have raised ValueError")
    except ValueError:
        pass

    if f:
        print("FAIL"); [print("  -", x) for x in f]; return 1
    print("PASS - language-agnostic 3B on Java-shaped report + custom-shape rejection")
    return 0

if __name__ == "__main__":
    raise SystemExit(run())

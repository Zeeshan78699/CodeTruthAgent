"""Pure-core test for type_fact_aggregator.aggregate."""
from v3.repository_reasoning.type_fact_aggregator import aggregate, RESOLVED, AMBIGUOUS, UNCERTAIN

def run():
    attr = [{"label": RESOLVED}, {"label": RESOLVED}, {"label": AMBIGUOUS}]
    self_attr = [{"label": RESOLVED}]
    registry = [{"label": UNCERTAIN}, {"label": UNCERTAIN}]
    rep = aggregate(1000, attr, self_attr, 50, registry,
                    {"internal": 300, "external": 200, "builtin": 10, "callers": 80})
    f = []
    a = rep["phase_3a"]
    if a["attr_calls_resolved"] != 3: f.append(f"resolved {a['attr_calls_resolved']} != 3")
    if a["attr_calls_ambiguous"] != 1: f.append(f"ambig {a['attr_calls_ambiguous']} != 1")
    if a["attr_calls_total"] != 4: f.append(f"total {a['attr_calls_total']} != 4")
    if a["pct_of_baseline"] != 0.4: f.append(f"pct {a['pct_of_baseline']} != 0.4")
    if a["registry_uncertain_edges"] != 2: f.append("registry count wrong")
    if rep["by_label"][UNCERTAIN] != 2: f.append("by_label UNCERTAIN wrong")
    if rep["by_label"][RESOLVED] != 3: f.append("by_label RESOLVED wrong")
    if rep["phase_3b"]["terminal_edges"] != 210: f.append("terminal edges wrong")
    if rep["truth_boundary"]["numeric_confidence_scores"] != 0: f.append("confidence != 0")
    if f:
        print("FAIL"); [print(" -", x) for x in f]; return 1
    print("PASS - aggregator counts + by-label + truth-boundary"); return 0

if __name__ == "__main__":
    raise SystemExit(run())

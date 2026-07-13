"""
type_fact_aggregator.py
CodeTruth Agent V3 — Module 3 (Repository Reasoning Engine), Integration.

Assembles every Phase 3A / 3B fact into ONE Module 3 report with per-source
counts and a categorical by-label breakdown. No numeric confidence; bounded sets
preserved; unresolved is reported as a documented remainder, never zero-filled.

Pure: takes already-computed facts and returns a dict. Unit-testable.
"""

RESOLVED = "RESOLVED"
INFERRED = "INFERRED"
AMBIGUOUS = "AMBIGUOUS"
UNCERTAIN = "UNCERTAIN"
UNRESOLVABLE = "UNRESOLVABLE"
LABELS = (RESOLVED, INFERRED, AMBIGUOUS, UNCERTAIN, UNRESOLVABLE)


def aggregate(baseline_attr_calls, attr_edges, self_attr_edges,
              reexport_grounded, registry_edges, chain_stats):
    """
    baseline_attr_calls : int  (Module 2 remaining attribute_call sites)
    attr_edges          : Step-1 type_flow_tracer edges (RESOLVED/AMBIGUOUS)
    self_attr_edges     : self_attribute_typer edges
    reexport_grounded   : int  (cross_module symbols grounded)
    registry_edges      : registry_string_resolver UNCERTAIN edges
    chain_stats         : {"internal":..,"external":..,"builtin":..,"callers":..}
    """
    by_label = {l: 0 for l in LABELS}
    for e in list(attr_edges) + list(self_attr_edges):
        by_label[e["label"]] = by_label.get(e["label"], 0) + 1
    for e in registry_edges:
        by_label[UNCERTAIN] = by_label.get(UNCERTAIN, 0) + 1

    attr_resolved = sum(1 for e in attr_edges if e["label"] == RESOLVED) \
        + sum(1 for e in self_attr_edges if e["label"] == RESOLVED)
    attr_ambiguous = sum(1 for e in list(attr_edges) + list(self_attr_edges)
                         if e["label"] == AMBIGUOUS)
    attr_total = attr_resolved + attr_ambiguous

    pct = (100.0 * attr_total / baseline_attr_calls) if baseline_attr_calls else 0.0
    return {
        "phase_3a": {
            "baseline_attr_calls": baseline_attr_calls,
            "attr_calls_resolved": attr_resolved,
            "attr_calls_ambiguous": attr_ambiguous,
            "attr_calls_total": attr_total,
            "pct_of_baseline": round(pct, 2),
            "reexport_symbols_grounded": reexport_grounded,
            "registry_uncertain_edges": len(registry_edges),
        },
        "phase_3b": {
            "internal_edges_chainable": chain_stats.get("internal", 0),
            "terminal_edges": chain_stats.get("external", 0) + chain_stats.get("builtin", 0),
            "callers_with_internal_edges": chain_stats.get("callers", 0),
        },
        "by_label": by_label,
        "truth_boundary": {
            "numeric_confidence_scores": 0,
            "guesses": 0,
            "note": "categorical labels only; bounded sets preserved; "
                    "remaining attribute_calls retain documented reasons",
        },
    }

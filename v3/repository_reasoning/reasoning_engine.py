"""
reasoning_engine.py
CodeTruth Agent V3 — Module 3 (Repository Reasoning Engine), Phase 3B driver +
public entry point.

Composes the validated Phase 3A components (type resolution) and Phase 3B
(multi_hop_analyzer) into one Module 3 result, then hands the facts to
type_fact_aggregator for the report. Adds no new resolution logic of its own -
it is the coordinator the architecture calls for.

  ReasoningEngine(repo_root).resolve() -> Module 3 report dict
"""

from v3.repository_reasoning.type_fact_aggregator import aggregate
from v3.repository_reasoning.multi_hop_analyzer import build_call_index, _callee_kind


class ReasoningEngine:
    def __init__(self, repo_root, root_counts=None, max_passes=5, max_depth=6,
                 m2_scan=None, m1_result=None):
        self.repo_root = repo_root
        self.root_counts = root_counts
        self.max_passes = max_passes
        self.max_depth = max_depth
        self.m2_scan = m2_scan          # optional: reuse M2 scan (avoid double scan)
        self.m1_result = m1_result      # optional: future-proof, ignored today

    def resolve(self):
        # Lazy imports keep this module import-light and the frozen engine lazy.
        from v3.repository_graph.languages.python_adapter import PythonAdapter
        from v3.repository_reasoning.type_flow_tracer import trace_attribute_calls
        from v3.repository_reasoning.self_attribute_typer import trace_self_attr_calls
        from v3.repository_reasoning.cross_module_type_resolver import (
            from_repo as reexport_from_repo,
        )
        from v3.repository_reasoning.registry_string_resolver import (
            extract_registries, resolve_dispatch_sites,
        )
        from v3.repository_reasoning.return_type_inferencer import _reconstruct_inputs

        # ---- Phase 3A: type resolution (all banked components) ----
        attr_edges, attr_summary = trace_attribute_calls(
            self.repo_root, self.root_counts, self.max_passes)
        self_edges, self_summary, _ = trace_self_attr_calls(
            self.repo_root, self.root_counts, self.max_passes)

        # cross-module re-export grounding (count only; resolved_map is the artifact)
        # reuse the reconstruction once for registry + reexport to avoid re-parsing.
        inp = _reconstruct_inputs(self.repo_root, self.root_counts)
        from v3.repository_reasoning.cross_module_type_resolver import (
            build_defining_index, build_reexport_edges, resolve_reexport, MAX_HOPS,
        )
        defined = build_defining_index(inp)
        rx_edges = build_reexport_edges(inp["import_alias_maps"], defined)
        grounded = 0
        for module_name, amap in inp["import_alias_maps"].items():
            for local, target in amap.items():
                if target in defined:
                    continue
                if resolve_reexport(target, rx_edges, defined, MAX_HOPS) is not None:
                    grounded += 1

        registries = extract_registries(
            inp["module_trees"], inp["real_class_names_index"], inp["import_alias_maps"])
        registry_edges = resolve_dispatch_sites(inp["module_trees"], registries)

        # ---- Phase 3B: call-graph reasoning ----
        m2 = self.m2_scan if self.m2_scan is not None else \
            PythonAdapter().scan(repo_root=self.repo_root, file_paths=[])
        all_edges = [e for edges in m2["call_graph"].values() for e in edges]
        m2_edge_count = len(all_edges)  # provenance baseline (never mutated)

        # --- promote local-variable receiver edges into the primary graph ---
        local_counts = {}
        imported_counts = {}
        try:
            from v3.repository_reasoning.local_receiver_edges import emit_local_typed_edges
            lr = emit_local_typed_edges(self.repo_root, self.root_counts, self.max_passes)
            local_counts = lr.get("counts", {})
            existing = {(e["caller"], e["callee"]) for e in all_edges}
            for edges in lr.get("call_graph", {}).values():
                for e in edges:
                    key = (e["caller"], e["callee"])
                    if key not in existing:
                        all_edges.append(e)
                        existing.add(key)
        except Exception as _e:
            local_counts = {"error": f"{type(_e).__name__}: {_e}"}

        # --- merge imported-receiver edges (namespace-bridge) additively ---
        try:
            from v3.repository_reasoning.imported_receiver_edges import emit_imported_receiver_edges
            ir = emit_imported_receiver_edges(self.repo_root, self.root_counts, self.max_passes)
            imported_counts = ir.get("counts", {})
            for edges in ir.get("call_graph", {}).values():
                for e in edges:
                    key = (e["caller"], e["callee"])
                    if key not in existing:
                        all_edges.append(e)
                        existing.add(key)
        except Exception as _e2:
            imported_counts = {"error": f"{type(_e2).__name__}: {_e2}"}

        index = build_call_index(all_edges)
        chain_stats = {
            "internal": sum(1 for e in all_edges if _callee_kind(e["callee"]) == "internal"),
            "external": sum(1 for e in all_edges if _callee_kind(e["callee"]) == "external"),
            "builtin": sum(1 for e in all_edges if _callee_kind(e["callee"]) == "builtin"),
            "callers": sum(1 for outs in index.values()
                           if any(k == "internal" for _, k, _, _ in outs)),
        }

        report = aggregate(
            baseline_attr_calls=attr_summary["baseline_attr_calls"],
            attr_edges=attr_edges,
            self_attr_edges=self_edges,
            reexport_grounded=grounded,
            registry_edges=registry_edges,
            chain_stats=chain_stats,
        )
        report["call_index"] = index  # available for on-demand chain queries
        report["local_receiver_counts"] = local_counts
        report["imported_receiver_counts"] = imported_counts
        report["edge_provenance"] = {
            "module2_edges": m2_edge_count,
            "local_receiver_added": len(all_edges) - m2_edge_count,
            "total_edges": len(all_edges),
        }

        return report


def from_repo(repo_root, root_counts=None):
    report = ReasoningEngine(repo_root, root_counts).resolve()
    a, b = report["phase_3a"], report["phase_3b"]
    print("  === Module 3 report ===")
    print(f"  [3A] baseline attribute_calls   : {a['baseline_attr_calls']}")
    print(f"  [3A] resolved (RESOLVED+AMBIG)  : {a['attr_calls_total']}  ({a['pct_of_baseline']}%)")
    print(f"  [3A] re-export symbols grounded : {a['reexport_symbols_grounded']}")
    print(f"  [3A] registry UNCERTAIN edges   : {a['registry_uncertain_edges']}")
    print(f"  [3B] chainable internal edges   : {b['internal_edges_chainable']}")
    print(f"  [3B] connected callers          : {b['callers_with_internal_edges']}")
    print(f"  by label: {report['by_label']}")
    print(f"  truth boundary: {report['truth_boundary']['numeric_confidence_scores']} "
          f"confidence scores, {report['truth_boundary']['guesses']} guesses")
    return report

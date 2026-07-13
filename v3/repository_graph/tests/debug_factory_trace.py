"""
debug_factory_trace.py

Traces the make_setup_state -> add_url_rule factory case step by step
to find exactly where it diverges, if it does, from the expected result.

    python v3\\repository_graph\\tests\\debug_factory_trace.py C:\\repos\\v3\\flask
"""

import sys
from pathlib import Path


def _find_and_add_project_root():
    here = Path(__file__).resolve().parent
    for candidate in [here, *here.parents]:
        if (candidate / "v3" / "repository_graph").is_dir():
            sys.path.insert(0, str(candidate))
            return
    raise RuntimeError("Could not find the 'v3' package.")


_find_and_add_project_root()

from v3.repository_graph.languages.python_adapter import PythonAdapter
from v3.repository_graph import subtree_naming
from v3.repository_graph.deep_resolution.resolution_pipeline import ResolutionPipeline, _enrich_origin_facts
from v3.repository_graph.deep_resolution.cause_classifier import CauseClassifier
from v3.repository_graph.deep_resolution.fact_extractor_v2 import extract_facts_v2 as extract_facts


def main():
    repo_path = sys.argv[1]
    report = PythonAdapter().scan(repo_root=repo_path, file_paths=[])

    # FIX: must mirror python_adapter.py's own rename_fn exactly - this
    # script forgot it on the first pass, which silently broke the
    # assignment_table's keys for src-layout repos like Flask and
    # produced a misleading "factory_function never gets set" result
    # for the WRONG reason. repo_path passed to the pipeline must also
    # be the correct scanning root (effective_root) per the same fix
    # applied in python_adapter.py for D-008 cases.
    src_prefix = report.get("src_layout_prefix_stripped")
    rename_fn = (lambda name: subtree_naming._strip(name, src_prefix + ".")) if src_prefix else None

    pipeline = ResolutionPipeline(
        unresolved_entries=report["unresolved"], return_type_table=report["return_type_table"],
        class_graph=report["class_graph"], repo_path=repo_path,
        function_graph=report["function_graph"], module_graph=report["module_graph"],
        rename_fn=rename_fn,
    )

    classifier = CauseClassifier()
    classified = [dict(e, cause=classifier.classify_entry(e)) for e in pipeline.unresolved_entries]
    facts = extract_facts(classified)

    target_facts = [f for f in facts if f.get("module") == "flask.sansio.blueprints" and f.get("attribute_name") == "add_url_rule"]
    print(f"Step 1 - raw extracted facts matching module+attribute_name: {len(target_facts)}")
    for f in target_facts:
        print(" ", f)

    enriched = _enrich_origin_facts(facts, pipeline.assignment_table, pipeline.flat_class_graph, pipeline.bare_name_index, pipeline.origin_extractor)
    target_enriched = [f for f in enriched if f.get("module") == "flask.sansio.blueprints" and f.get("attribute_name") == "add_url_rule"]
    print(f"\nStep 2 - after enrichment, same facts: {len(target_enriched)}")
    for f in target_enriched:
        print(" ", f)

    # Finer-grained trace of the two sub-steps _enrich_origin_facts
    # relies on, isolated directly - this is the part most likely to
    # diverge if everything else (Steps 3-5) already matches.
    print(f"\nStep 2a - VariableOriginExtractor.extract_variable_name('flask.sansio.blueprints', 324, 'add_url_rule'):")
    var_name = pipeline.origin_extractor.extract_variable_name("flask.sansio.blueprints", 324, "add_url_rule")
    print(" ", repr(var_name))

    print(f"\nStep 2b - module_graph path stored for 'flask.sansio.blueprints':")
    print(" ", pipeline.module_graph.get("flask.sansio.blueprints", {}).get("path"))

    print(f"\nStep 2c - assignment_table entry for 'flask.sansio.blueprints:state':")
    print(" ", pipeline.assignment_table.get("flask.sansio.blueprints:state"))

    print(f"\nStep 2d - all assignment_table keys containing 'blueprints':")
    for k in pipeline.assignment_table:
        if "blueprints" in k:
            print(" ", k, "->", pipeline.assignment_table[k])

    print(f"\nStep 3 - return_type_table entry for 'make_setup_state':")
    print(" ", pipeline.flat_return_type_table.get("make_setup_state"))

    print(f"\nStep 4 - bare_name_index entry for 'BlueprintSetupState':")
    print(" ", pipeline.bare_name_index.get("BlueprintSetupState"))

    qualified = pipeline.bare_name_index.get("BlueprintSetupState")
    if qualified and len(qualified) == 1:
        print(f"\nStep 5 - class_graph entry for '{qualified[0]}':")
        print(" ", pipeline.flat_class_graph.get(qualified[0]))


if __name__ == "__main__":
    main()
"""
flatten_class_graph.py

The fix for the root cause found across the unresolved_pipeline
experiment: every resolver in this package (constructor_origin_tracker,
factory_origin_tracker, return_flow_tracker / _v2, property_type_table_builder,
inheritance_resolver, reflection_resolver, constructor_tracking_engine,
factory_return_engine, property_type_engine) was written expecting

    class_graph["Parser"] = {"methods": [...], "bases": [...]}

but the real class_graph produced by graph_engine.build_repository_graph
(via PythonAdapter) is keyed by MODULE name, with a list of class dicts
as the value:

    class_graph["pkg.module"] = [{"name": "Parser", "bases": [...], ...}]

and has no "methods" key at all - methods are tracked separately in
function_graph, linked by each function's "scope" field.

This converts the real shape into the flat shape every one of those
files already expects, so NONE of their internal logic needs to change -
only what gets passed in as `class_graph`.

Known limitation, disclosed rather than hidden: this keys the output by
BARE class name, not by fully-qualified module path. If two different
modules in the same repo define a class with the same name, the second
one encountered silently overwrites the first in this flat table. That
risk is acceptable for this exploratory tool, but would NOT be
acceptable inside the frozen call_graph.py itself (which correctly
keys everything by fully-qualified id for exactly this reason).
"""

from typing import Any, Dict, List


def flatten_class_graph(
    class_graph: Dict[str, List[Dict[str, Any]]],
    function_graph: Dict[str, List[Dict[str, Any]]],
) -> Dict[str, Dict[str, Any]]:
    """
    Returns {class_name: {"methods": [method_name, ...], "bases": [base_name, ...]}}

    class_graph / function_graph: the real, module-keyed dicts as returned
    by graph_engine.build_repository_graph() / PythonAdapter.scan().
    """
    flat: Dict[str, Dict[str, Any]] = {}

    # First pass: register every class with its declared bases (already
    # plain names-as-written, per class_graph.py's own contract - no
    # resolution needed here).
    for module_name, classes in class_graph.items():
        for cls in classes:
            name = cls["name"]
            entry = flat.setdefault(name, {"methods": [], "bases": []})
            # If the same bare name is seen twice (the disclosed collision
            # risk), bases get unioned rather than silently replaced - a
            # little more honest than a flat overwrite, though still not
            # module-qualified.
            for base in cls.get("bases", []):
                if base not in entry["bases"]:
                    entry["bases"].append(base)

    # Second pass: attach methods via function_graph's "scope" field.
    # scope is the owning class's name as written (e.g. "Parser", or
    # "Parser.Inner" for a nested class - only the first component is
    # the class for our purposes here).
    for module_name, funcs in function_graph.items():
        for f in funcs:
            scope = f.get("scope")
            if not scope:
                continue
            class_name = scope.split(".")[0]
            if class_name not in flat:
                # A method whose class wasn't itself in class_graph
                # (shouldn't normally happen) - skip rather than guess
                # at a class that was never actually seen.
                continue
            if f["name"] not in flat[class_name]["methods"]:
                flat[class_name]["methods"].append(f["name"])

    return flat


def flatten_return_type_table(return_type_table: Dict[str, Any]) -> Dict[str, str]:
    """
    Second shape mismatch found while wiring this in: the real
    return_type_table (from type_inference.py / PythonAdapter) is keyed
    by FULL function id ("module.create_app") with type_info tuples as
    values (("class", "module", "Flask")) - but the experimental tools
    here (factory_return_engine.py etc.) look up by BARE function name
    as called in code ("create_app") and expect a plain class-name
    string ("Flask"), not a tuple.

    Only "class" type_info entries are kept - "builtin" entries
    (list/dict/set/str) have no class to chain a method onto in these
    tools, so they're correctly dropped rather than mis-converted.

    Same bare-name collision caveat as flatten_class_graph: two
    differently-scoped functions with the same bare name will overwrite
    each other here. Acceptable for this exploratory tool, not for the
    frozen core.
    """
    flat: Dict[str, str] = {}
    for full_id, type_info in return_type_table.items():
        if not type_info or type_info[0] != "class":
            continue
        bare_name = full_id.split(".")[-1]
        flat[bare_name] = type_info[2]
    return flat

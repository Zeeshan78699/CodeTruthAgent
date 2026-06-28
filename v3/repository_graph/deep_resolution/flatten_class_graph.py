"""
flatten_class_graph.py

The fix for the root cause found across this resolver set
(constructor_tracking_engine, factory_return_engine, property_type_engine,
inheritance_resolver, reflection_resolver): each was written expecting

    class_graph["Parser"] = {"methods": [...], "bases": [...]}

but the real class_graph produced by graph_engine.build_repository_graph
(via PythonAdapter) is keyed by MODULE name, with a list of class dicts
as the value:

    class_graph["pkg.module"] = [{"name": "Parser", "bases": [...], ...}]

and has no "methods" key at all - methods are tracked separately in
function_graph, linked by each function's "scope" field.

FIX (main-pipeline integration): the original version of this file keyed
its output by BARE class name only, with a disclosed collision risk -
two classes with the same name in different modules would silently
overwrite each other. Acceptable for a one-repo exploratory script,
NOT acceptable once this runs across many repos as part of the real
pipeline. Now keyed by FULLY QUALIFIED name ("module.ClassName")
instead, with a small bare-name index kept ALONGSIDE (not instead of)
the qualified one - used only as an explicit, disclosed fallback by
inheritance_resolver.py when walking a base class written as a bare
name with no local import information to qualify it against (see that
file's own comment on this limitation).
"""

from typing import Any, Dict, List


def flatten_class_graph(
    class_graph: Dict[str, List[Dict[str, Any]]],
    function_graph: Dict[str, List[Dict[str, Any]]],
) -> Dict[str, Dict[str, Any]]:
    """
    Returns {"module.ClassName": {"methods": [...], "bases": [...],
    "bare_name": "ClassName", "module": "module"}}.

    class_graph / function_graph: the real, module-keyed dicts as
    returned by graph_engine.build_repository_graph() / PythonAdapter.scan().
    """
    flat: Dict[str, Dict[str, Any]] = {}

    for module_name, classes in class_graph.items():
        for cls in classes:
            name = cls["name"]
            qualified = f"{module_name}.{name}"
            entry = flat.setdefault(qualified, {
                "methods": [], "bases": [], "bare_name": name, "module": module_name,
            })
            for base in cls.get("bases", []):
                if base not in entry["bases"]:
                    entry["bases"].append(base)

    for module_name, funcs in function_graph.items():
        for f in funcs:
            scope = f.get("scope")
            if not scope:
                continue
            class_name = scope.split(".")[0]
            qualified = f"{module_name}.{class_name}"
            if qualified not in flat:
                continue
            if f["name"] not in flat[qualified]["methods"]:
                flat[qualified]["methods"].append(f["name"])

    return flat


def build_bare_name_index(flat_class_graph: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    {"ClassName": ["module.ClassName", "other_module.ClassName", ...]}

    Explicit, disclosed fallback index for inheritance_resolver.py only -
    used when a base class is written as a bare name with no local
    qualification info available. If a bare name maps to more than one
    qualified entry, that ambiguity is visible right here rather than
    silently picking one - callers must decide how to handle it (the
    current resolver skips ambiguous bare-name matches rather than
    guessing which one is meant).
    """
    index: Dict[str, List[str]] = {}
    for qualified, info in flat_class_graph.items():
        index.setdefault(info["bare_name"], []).append(qualified)
    return index


def resolve_bare_class_name(bare_name: str, bare_name_index: Dict[str, List[str]]):
    """
    Shared helper: resolves a bare class name to its single qualified
    match, or None if it matches zero or more than one class repo-wide.
    Used by every resolver here that only has a bare name available
    (a return-type table entry, a class-level property assignment) and
    has no further import-alias information to qualify it more
    precisely - the honest, conservative choice over silently picking
    one when ambiguous.
    """
    matches = bare_name_index.get(bare_name)
    if not matches or len(matches) != 1:
        return None
    return matches[0]


def flatten_return_type_table(return_type_table: Dict[str, Any]) -> Dict[str, str]:
    """
    Second shape mismatch found while wiring this in: the real
    return_type_table (from type_inference.py / PythonAdapter) is keyed
    by FULL function id ("module.create_app") with type_info tuples as
    values (("class", "module", "Flask")) - but the resolvers here
    look up by BARE function name as called in code ("create_app") and
    expect a plain class-name string ("Flask"), not a tuple.

    Only "class" type_info entries are kept - "builtin" entries
    (list/dict/set/str) have no class to chain a method onto in these
    tools, so they're correctly dropped rather than mis-converted.

    Same bare-name collision caveat as before: two differently-scoped
    functions with the same bare name will overwrite each other here.
    This table is about RETURN TYPES OF CALLED FUNCTIONS, not classes -
    the call site itself only ever has the bare name available (e.g.
    "x = create_app()"), so there is no qualification information to
    key on more precisely without resolving the call site's own import
    aliases first - a real, disclosed limitation, not yet fixed here.
    """
    flat: Dict[str, str] = {}
    for full_id, type_info in return_type_table.items():
        if not type_info or type_info[0] != "class":
            continue
        bare_name = full_id.split(".")[-1]
        flat[bare_name] = type_info[2]
    return flat

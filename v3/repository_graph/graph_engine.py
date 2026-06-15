"""
graph_engine.py
Module 2 orchestrator - implements decision D-001 (two-stage global build).

STAGE A: parse all files once, build function_graph, class_graph,
         module_graph, and raw import lists (per module).
STAGE B: using Stage A's global symbol tables, resolve call_graph.

dependency_graph and the internal/external import split happen after
Stage A using the project's module-root set.
"""

import ast
import os

from .module_graph import build_module_graph, module_name_from_path
from .function_graph import build_function_graph_for_module
from .class_graph import build_class_graph_for_module
from .import_graph import collect_raw_imports, split_internal_external
from .dependency_graph import build_dependency_graph, load_declared_dependencies
from .call_graph import build_call_graph, build_import_alias_map
from .topology import find_cycles, annotate_module_graph


def find_python_files(root):
    py_files = []
    for dirpath, dirnames, filenames in os.walk(root):
        # skip common non-source dirs
        dirnames[:] = [d for d in dirnames if d not in
                        {".git", "__pycache__", "node_modules", ".venv", "venv"}]
        for f in filenames:
            if f.endswith(".py"):
                py_files.append(os.path.join(dirpath, f))
    return py_files


def build_repository_graph(repo_root, cognition_report=None):
    """
    Main entry point for Module 2.

    repo_root: path to repository root
    cognition_report: optional Module 1 RepositoryCognitionReport - if
        provided, can be used to scope file discovery to detected source
        dirs / languages. Currently informational only (Python-only engine).

    Returns a single RepositoryGraphReport-shaped dict containing all 6
    graphs (V3-004 through V3-009), unresolved log, and governance gate.

    NOTE: Output also includes "language_composition" (informational,
    additive) - a count of files per detected language extension across
    the whole repo, via the languages/ adapter registry. This does NOT
    change Python-only scanning behavior; it is a forward-compatible hook
    for future language adapters (java/javascript/go/rust/c_cpp - see
    v3/repository_graph/languages/). Only "python" is currently scanned;
    other languages report file counts only (is_implemented=False).
    """
    py_files = find_python_files(repo_root)

    # ---- STAGE A: per-file parse + symbol collection ----
    module_trees = {}
    function_graph = {}
    class_graph = {}
    raw_imports_by_module = {}
    unresolved = []

    for filepath in py_files:
        mod_name = module_name_from_path(repo_root, filepath)
        if mod_name == "":
            continue

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source, filename=filepath)
        except (SyntaxError, UnicodeDecodeError) as e:
            unresolved.append({
                "module": mod_name, "pattern": "parse_error",
                "note": f"{type(e).__name__}: {e}",
            })
            continue

        module_trees[mod_name] = tree
        function_graph[mod_name] = build_function_graph_for_module(mod_name, tree)
        class_graph[mod_name] = build_class_graph_for_module(mod_name, tree)
        raw_imports_by_module[mod_name] = collect_raw_imports(mod_name, tree)

    module_graph = build_module_graph(repo_root, py_files)

    # ---- Determine project module roots (for internal/external split) ----
    project_module_roots = {m.split(".")[0] for m in module_trees.keys()}

    import_graph = {}
    external_imports_by_module = {}
    import_alias_maps = {}

    for mod_name, raw_imports in raw_imports_by_module.items():
        internal, external = split_internal_external(raw_imports, project_module_roots)
        import_graph[mod_name] = internal
        external_imports_by_module[mod_name] = external
        is_pkg = module_graph.get(mod_name, {}).get("is_package", False)
        import_alias_maps[mod_name] = build_import_alias_map(mod_name, raw_imports, is_package=is_pkg)

    dependency_graph = build_dependency_graph(external_imports_by_module)
    declared_dependencies = load_declared_dependencies(repo_root)

    # ---- STAGE B: global call resolution ----
    call_graph, call_unresolved = build_call_graph(
        module_trees, function_graph, class_graph, import_alias_maps,
        project_module_roots=project_module_roots
    )
    unresolved.extend(call_unresolved)

    # ---- Gap 3: cycle detection (Tarjan SCC over internal import graph) ----
    cycle_info = find_cycles(import_graph)
    module_graph = annotate_module_graph(module_graph, cycle_info)

    # ---- Governance gate (V3-003 style consistency) ----
    governance_gate = "APPROVED" if py_files else "BLOCKED"

    # ---- Language composition (informational, additive - see
    #      v3/repository_graph/languages/) ----
    try:
        from .languages import classify_files
        composition = classify_files(repo_root)
        language_composition = {
            lang: {
                "file_count": len(info["files"]),
                "implemented": info["adapter"].is_implemented(),
            }
            for lang, info in composition.items()
            if lang != "_unclassified"
        }
        language_composition["_other_extensions"] = composition["_unclassified"]["extensions"]
    except Exception:
        # Never let the (optional, informational) composition scan break
        # the core Python pipeline.
        language_composition = {}

    return {
        "repo_root": repo_root,
        "files_scanned": len(py_files),
        "modules_parsed": len(module_trees),
        "function_graph": function_graph,         # V3-004
        "class_graph": class_graph,                 # V3-005
        "module_graph": module_graph,               # V3-006 (+ cycle annotations)
        "import_graph": import_graph,               # V3-007 (internal)
        "dependency_graph": dependency_graph,       # V3-008 (external)
        "declared_dependencies": declared_dependencies,
        "call_graph": call_graph,                   # V3-009
        "cyclic_clusters": cycle_info["clusters"],  # Gap 3
        "unresolved": unresolved,
        "governance_gate": governance_gate,
        "language_composition": language_composition,  # forward-compat hook
    }
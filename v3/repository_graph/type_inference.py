"""
type_inference.py
attribute_call fix (Module 3 Python-core gap): per-function return-type
inference, consulted by an EXTENDED call resolver.

Non-invasive by design: imports CallResolver and its existing helper
functions from the FROZEN call_graph.py and subclasses exactly ONE
method (_classify_assignment_value) to add a single new fallback case.
Zero lines of call_graph.py are edited. super() is called FIRST in that
override, so every existing Gap 1 / Gap 2 / D-003 / D-004 resolution
this produces is byte-for-byte identical to the frozen CallResolver -
this module can only ADD newly-resolved edges that were previously
honest "attribute_call" unresolved entries; it never changes or removes
an existing resolved edge.

Truth Boundary: a function's return type is only recorded when EVERY
`return` statement in its body classifies to the SAME known type. A
bare `return`/`return None`, a return with no value, conflicting types
across branches, or any expression that doesn't match a known shape
leaves that function's return type UNDETERMINED - calls assigned from
it stay correctly unresolved, exactly as today. This intentionally does
NOT do transitive propagation (a function returning the result of
ANOTHER not-yet-classified function) - that is a known, honest scope
limit of this first increment, not a silent gap.
"""

import ast

from .call_graph import (
    CallResolver,
    build_global_symbol_index,
    build_resolved_bases,
    _flatten_attribute,
)


class _ReturnClassifier(ast.NodeVisitor):
    """
    Walks ONE function body and classifies its return type, using the
    same type_info shape as call_graph.py's Gap 2:
        ("builtin", name) | ("class", module, class_name) | None (unknown)

    framework_kb (optional): {function_name: type_info} for known
    framework helper functions actually in use by this repo - see
    framework_knowledge_base.py. Defaults to {} (zero behavior change
    for any caller not passing it).

    real_class_names / global_real_class_names: {module: {class_name}}
    built directly from class_graph - see build_real_class_names_index.
    FIX (found via deep-resolution scale testing on transformers):
    class_methods_index (built in call_graph.py from function SCOPE)
    conflates two different things that both produce a non-None scope -
    an actual class method, and a nested function/closure defined
    inside another function. A function like
    `def _build_foo(): def score(): ...; return score` ends up
    registered as if "_build_foo" were a CLASS with a "score" METHOD,
    purely because `score`'s scope happens to equal "_build_foo".
    Any other function elsewhere doing `return _build_foo(...)` was
    then misclassified as "returns an instance of class _build_foo" -
    confirmed on a real case in transformers
    (benchmark_v2...continuous_batching_overall.py). These params let
    every class_methods-based branch below also verify the name is a
    REAL class (from class_graph, never touched by this contamination)
    before trusting it - optional, defaulting to None, meaning "no
    additional check" for any caller not yet passing them, so nothing
    breaks if this is used outside its one call site.
    """

    def __init__(self, module_name, class_methods, import_alias_map,
                 global_class_methods, framework_kb=None,
                 real_class_names=None, global_real_class_names=None):
        self.module_name = module_name
        self.class_methods = class_methods
        self.import_alias_map = import_alias_map
        self.global_class_methods = global_class_methods
        self.framework_kb = framework_kb or {}
        self.real_class_names = real_class_names
        self.global_real_class_names = global_real_class_names or {}
        self.found_types = set()
        self.gave_up = False
        self._depth = 0  # don't descend into a nested def's own returns

    def visit_FunctionDef(self, node):
        self._depth += 1
        if self._depth > 1:
            return  # nested function - its returns belong to IT, not us
        self.generic_visit(node)
        self._depth -= 1

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Return(self, node):
        if node.value is None:
            self.gave_up = True
            return
        classified = self._classify(node.value)
        if classified is None:
            self.gave_up = True
        else:
            self.found_types.add(classified)

    def _classify(self, node):
        if isinstance(node, (ast.List, ast.ListComp)):
            return ("builtin", "list")
        if isinstance(node, (ast.Dict, ast.DictComp)):
            return ("builtin", "dict")
        if isinstance(node, (ast.Set, ast.SetComp)):
            return ("builtin", "set")
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return ("builtin", "str")

        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                cname = node.func.id
                if cname in self.class_methods:
                    # FIX: also require cname to be a REAL class, not
                    # just present in the scope-contaminated index.
                    if self.real_class_names is None or cname in self.real_class_names:
                        return ("class", self.module_name, cname)
                if cname in self.framework_kb:
                    return self.framework_kb[cname]
                target = self.import_alias_map.get(cname)
                if target:
                    parts = target.split(".")
                    for sp in range(len(parts) - 1, 0, -1):
                        mod, cls = ".".join(parts[:sp]), ".".join(parts[sp:])
                        if "." not in cls and cls in self.global_class_methods.get(mod, {}):
                            if cls in self.global_real_class_names.get(mod, set()) if self.global_real_class_names else True:
                                return ("class", mod, cls)
            elif isinstance(node.func, ast.Attribute):
                root, rest = _flatten_attribute(node.func)
                if root and rest and root in self.import_alias_map:
                    full = self.import_alias_map[root] + "." + ".".join(rest)
                    parts = full.split(".")
                    for sp in range(len(parts) - 1, 0, -1):
                        mod, cls = ".".join(parts[:sp]), ".".join(parts[sp:])
                        if "." not in cls and cls in self.global_class_methods.get(mod, {}):
                            if cls in self.global_real_class_names.get(mod, set()) if self.global_real_class_names else True:
                                return ("class", mod, cls)
        return None  # anything else is honestly UNKNOWN, never guessed

    def result(self):
        if self.gave_up or len(self.found_types) != 1:
            return None
        return next(iter(self.found_types))


def build_real_class_names_index(class_graph):
    """
    {module_name: {class_name, ...}} built directly from class_graph -
    immune to the function-scope contamination affecting
    class_methods_index (see _ReturnClassifier's docstring).
    """
    return {module: {c["name"] for c in classes} for module, classes in class_graph.items()}


def build_return_type_table(module_trees, function_graph, class_methods_index,
                             import_alias_maps, global_class_methods, framework_kb=None,
                             real_class_names_index=None):
    """
    Returns {full_function_id: type_info} for every function whose
    return type is UNAMBIGUOUSLY classifiable. Functions are absent from
    this table (not present, not None) when undetermined - callers must
    treat absence the same as "don't know".

    framework_kb (optional): see framework_knowledge_base.py - defaults
    to {} (zero behavior change for any caller not passing it).

    real_class_names_index (optional): see build_real_class_names_index -
    defaults to None (zero behavior change for any caller not passing
    it, i.e. the pre-fix behavior).
    """
    table = {}

    # (module, lineno) -> (full_id, scope), reusing function_graph's
    # ALREADY-correct qualname/scope computation rather than re-deriving
    # it a second time.
    id_by_location = {}
    for module_name, funcs in function_graph.items():
        for f in funcs:
            id_by_location[(module_name, f["lineno"])] = (f["id"], f["scope"])

    for module_name, tree in module_trees.items():
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            located = id_by_location.get((module_name, node.lineno))
            if not located:
                continue
            full_id, scope = located
            classifier = _ReturnClassifier(
                module_name,
                class_methods_index.get(module_name, {}),
                import_alias_maps.get(module_name, {}),
                global_class_methods,
                framework_kb=framework_kb,
                real_class_names=(real_class_names_index.get(module_name) if real_class_names_index is not None else None),
                global_real_class_names=real_class_names_index,
            )
            classifier.visit(node)
            result = classifier.result()
            if result is not None:
                table[full_id] = result

    return table


class TypeAwareCallResolver(CallResolver):
    """
    Extends the frozen CallResolver with exactly one new fallback inside
    _classify_assignment_value. See module docstring for the
    super()-first guarantee.
    """

    def __init__(self, *args, return_type_table=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.return_type_table = return_type_table or {}

    def _classify_assignment_value(self, node):
        existing = super()._classify_assignment_value(node)
        if existing is not None:
            return existing

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            fname = node.func.id
            full_id = self.local_funcs.get(fname)
            if full_id is None:
                resolved, kind = self._resolve_imported_name(fname)
                if kind == "resolved":
                    full_id = resolved
            if full_id and full_id in self.return_type_table:
                return self.return_type_table[full_id]

        return None


def augment_class_index_with_zero_method_classes(class_graph, class_methods_index):
    """
    Pre-existing limitation in the frozen build_global_symbol_index: a
    class is only added to class_methods_index if it has at least one
    method, since the index is built by iterating FUNCTIONS (filtering
    by scope), not by iterating classes directly. A class with zero
    methods - extremely common for exception hierarchies, e.g.
    `class ArgumentsRequired(BaseError): pass` - is therefore invisible
    to constructor-call resolution, D-004 base-class resolution, and
    the Gap 1 / external-call split, regardless of anything in
    type_inference.py. Discovered during real-repo validation: ~4,000+
    unresolved/mislabeled calls in ccxt alone traced to exactly this.

    Returns a NEW dict (does not mutate the input) with every
    class_graph entry represented, using {} for classes with no methods
    of their own. Existing call_graph.py resolution code already
    handles an empty methods dict correctly - it's the same code path
    already used for classes that have methods but no explicit
    __init__ (falls back to a synthetic ".<class>" marker). So this is
    a pure index-completeness fix, not a new resolution branch - it
    can only let MORE classes be recognized as classes; it never
    changes how a recognized class resolves.
    """
    augmented = {mod: dict(methods) for mod, methods in class_methods_index.items()}
    for module_name, classes in class_graph.items():
        augmented.setdefault(module_name, {})
        for c in classes:
            if c["name"] not in augmented[module_name]:
                augmented[module_name][c["name"]] = {}
    return augmented


def build_call_graph_with_type_inference(module_trees, function_graph, class_graph,
                                          import_alias_maps, project_module_roots=None,
                                          framework_kb=None):
    """
    Drop-in equivalent of call_graph.build_call_graph(), using
    TypeAwareCallResolver instead of CallResolver, with the
    zero-method-class index augmented in before any resolution runs.
    Orchestration is intentionally identical to the frozen
    build_call_graph - only the resolver class and the class index
    differ.

    framework_kb (optional): see framework_knowledge_base.py - defaults
    to {} (zero behavior change for any caller not passing it).

    Returns (call_graph, unresolved, return_type_table).
    """
    local_func_index, class_methods_index, nested_func_index = build_global_symbol_index(
        function_graph, class_graph
    )
    class_methods_index = augment_class_index_with_zero_method_classes(
        class_graph, class_methods_index
    )
    resolved_bases_index = build_resolved_bases(
        class_graph, class_methods_index, import_alias_maps
    )
    real_class_names_index = build_real_class_names_index(class_graph)
    return_type_table = build_return_type_table(
        module_trees, function_graph, class_methods_index,
        import_alias_maps, class_methods_index, framework_kb=framework_kb,
        real_class_names_index=real_class_names_index,
    )

    call_graph = {}
    unresolved = []

    for module_name, tree in module_trees.items():
        resolver = TypeAwareCallResolver(
            module_name=module_name,
            local_funcs=local_func_index.get(module_name, {}),
            class_methods=class_methods_index.get(module_name, {}),
            import_alias_map=import_alias_maps.get(module_name, {}),
            global_func_index=local_func_index,
            global_class_methods=class_methods_index,
            resolved_bases=resolved_bases_index.get(module_name, {}),
            global_resolved_bases=resolved_bases_index,
            project_module_roots=project_module_roots,
            nested_func_index=nested_func_index.get(module_name, {}),
            return_type_table=return_type_table,
        )
        resolver.visit(tree)
        call_graph[module_name] = resolver.calls
        unresolved.extend(resolver.unresolved)

    return call_graph, unresolved, return_type_table


def build_repository_call_graph_enhanced(repo_root, root_counts=None):
    """
    Re-runs Stage A (file discovery + per-module parsing + import alias
    maps) independently of graph_engine.build_repository_graph, then
    runs Stage B via TypeAwareCallResolver instead of the frozen
    CallResolver.

    This duplicates Stage A's ORCHESTRATION (a second parse pass over
    the repo) but reuses every actual Stage A function UNCHANGED
    (find_python_files, build_function_graph_for_module,
    build_class_graph_for_module, collect_raw_imports, build_module_graph,
    build_import_alias_map) - no parsing/resolution logic is duplicated,
    only the sequencing, since build_repository_graph computes this
    internally but does not expose it.

    root_counts (optional): the {import_root: count} table the caller
    may already have computed (e.g. via package_root's
    detect_package_root_and_counts) - used to detect which framework
    knowledge base(s), if any, apply to this repo. If not supplied,
    computed independently here so behavior is unchanged for any
    existing caller.

    Returns (call_graph, unresolved, return_type_table). call_graph and
    unresolved are meant to REPLACE those two fields in
    build_repository_graph(repo_root)'s output; every other field in
    that report is unaffected by this fix.
    """
    from .graph_engine import find_python_files
    from .module_graph import build_module_graph, module_name_from_path
    from .function_graph import build_function_graph_for_module
    from .class_graph import build_class_graph_for_module
    from .import_graph import collect_raw_imports
    from .call_graph import build_import_alias_map
    from .package_root import _collect_absolute_import_roots
    from .framework_knowledge_base import build_active_knowledge_base

    py_files = find_python_files(repo_root)

    if root_counts is None:
        root_counts = _collect_absolute_import_roots(py_files)
    framework_kb = build_active_knowledge_base(root_counts)

    module_trees = {}
    function_graph = {}
    class_graph = {}
    raw_imports_by_module = {}

    for filepath in py_files:
        mod_name = module_name_from_path(repo_root, filepath)
        if mod_name == "":
            continue
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source, filename=filepath)
        except (SyntaxError, UnicodeDecodeError):
            continue

        module_trees[mod_name] = tree
        function_graph[mod_name] = build_function_graph_for_module(mod_name, tree)
        class_graph[mod_name] = build_class_graph_for_module(mod_name, tree)
        raw_imports_by_module[mod_name] = collect_raw_imports(mod_name, tree)

    module_graph = build_module_graph(repo_root, py_files)
    project_module_roots = {m.split(".")[0] for m in module_trees.keys()}

    import_alias_maps = {}
    for mod_name, raw_imports in raw_imports_by_module.items():
        is_pkg = module_graph.get(mod_name, {}).get("is_package", False)
        import_alias_maps[mod_name] = build_import_alias_map(
            mod_name, raw_imports, is_package=is_pkg
        )

    return build_call_graph_with_type_inference(
        module_trees, function_graph, class_graph, import_alias_maps,
        project_module_roots=project_module_roots,
        framework_kb=framework_kb,
    )
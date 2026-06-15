"""
call_graph.py
V3-009: Call graph mapping registry

STAGE B component (per D-001): requires the GLOBAL symbol table from
function_graph + class_graph (all modules) to be built first.
Cannot run correctly per-file in isolation - see
docs/module2/MODULE2_DECISIONS.md, decision D-001.

This version adds:
  - D-004: cross-module class inheritance resolution for self.method()
  - Gap 1: qualified module call resolution (e.g. `pkg.utils.helper()`,
           or `utils.helper()` after `from pkg import utils`)
  - Gap 2: non-predictive local-scope type tracking (e.g. `x = []` then
           `x.append(...)` -> resolves to builtin.list.append)
"""

import ast


def build_global_symbol_index(function_graph, class_graph):
    """
    Builds lookup structures needed for call resolution across the whole repo.

    Returns:
        local_func_index: {module_name: {func_name: full_id}}
            - top-level (non-method) functions only
        class_methods_index: {module_name: {class_name: {method_name: full_id}}}
    """
    local_func_index = {}
    class_methods_index = {}

    for module_name, funcs in function_graph.items():
        local_func_index[module_name] = {}
        for f in funcs:
            if f["scope"] is None:
                local_func_index[module_name][f["name"]] = f["id"]

    for module_name, classes in class_graph.items():
        class_methods_index[module_name] = {}

    for module_name, funcs in function_graph.items():
        for f in funcs:
            if f["scope"] is not None:
                class_name = f["scope"].split(".")[0]
                class_methods_index.setdefault(module_name, {})
                class_methods_index[module_name].setdefault(class_name, {})
                class_methods_index[module_name][class_name][f["name"]] = f["id"]

    # D-006: index ALL functions (incl. nested) by (module, scope, name) ->
    # full_id, so recursive/sibling calls to nested functions resolve.
    nested_func_index = {}
    for module_name, funcs in function_graph.items():
        nested_func_index[module_name] = {}
        for f in funcs:
            nested_func_index[module_name][(f["scope"], f["name"])] = f["id"]

    return local_func_index, class_methods_index, nested_func_index


def build_import_alias_map(module_name, raw_imports, is_package=False):
    """
    Maps local names usable in this module -> fully qualified target.
    e.g. `from pkg.utils import helper` -> {"helper": "pkg.utils.helper"}
         `import pkg.utils as u`        -> {"u": "pkg.utils"} (module alias)

    D-007: relative imports (`from . import x`, `from ..utils import Y`)
    are resolved to ABSOLUTE module paths using `module_name` and whether
    this module is a package (`is_package`, from module_graph). Without
    this, relative-import targets stayed unresolved against the global
    (absolute-path) symbol tables - a major source of unresolved
    constructor calls and inherited-base lookups in packages that use
    relative imports heavily (django, transformers, qiskit, etc.).
    """
    alias_map = {}
    for entry in raw_imports:
        if entry["type"] == "from_import":
            level = entry.get("relative_level", 0)
            if level > 0:
                # Current module's own package path.
                # Packages (__init__.py -> module_name IS the package) use
                # their own dotted path; regular modules use their parent.
                if is_package:
                    current_package_parts = module_name.split(".")
                else:
                    current_package_parts = module_name.split(".")[:-1]

                up = level - 1  # level=1 means "this package", level=2 means "one up", etc.
                if up > 0:
                    if up <= len(current_package_parts):
                        target_package_parts = current_package_parts[:-up]
                    else:
                        target_package_parts = []  # clamp - can't go above root
                else:
                    target_package_parts = current_package_parts

                module_part = entry.get("module_part", "")
                symbol_part = entry.get("symbol_part", entry["imports"].split(".")[-1])

                if module_part:
                    abs_parts = target_package_parts + module_part.split(".") + [symbol_part]
                else:
                    abs_parts = target_package_parts + [symbol_part]

                target = ".".join(p for p in abs_parts if p)
                alias_map[symbol_part] = target
                continue

            # Absolute from-import (level == 0)
            target = entry["imports"]
            local_name = target.split(".")[-1]
            alias_map[local_name] = target
        elif entry["type"] == "import":
            target = entry["imports"]
            local_name = target.split(".")[0]
            alias_map[local_name] = target
    return alias_map


def build_resolved_bases(class_graph, class_methods_index, import_alias_maps):
    """
    D-004: For each class, resolve its declared base classes (as written)
    to (module, class_name) pairs where possible.

    Returns:
        {module: {class_name: {"resolved": [(mod, cls), ...],
                                "raw": [base_str, ...]}}}
    "resolved" = bases we can locate in this project's class_methods_index
                 (same-module or cross-module via imports)
    "raw"      = bases we could NOT resolve (stdlib/3rd-party/dynamic) -
                 candidates for the D-003 STDLIB_INHERITED_METHODS whitelist
    """
    resolved_bases = {}
    for module, classes in class_graph.items():
        resolved_bases[module] = {}
        for c in classes:
            resolved_list = []
            raw_unresolved = []
            for base_str in c.get("bases", []):
                first = base_str.split(".")[0]

                # Case 1: base is a class defined in THIS SAME module
                if "." not in base_str and first in class_methods_index.get(module, {}):
                    resolved_list.append((module, first))
                    continue

                # Case 2: base resolved via this module's imports
                alias_target = import_alias_maps.get(module, {}).get(first)
                found = False
                if alias_target:
                    rest = base_str.split(".")[1:]
                    full = alias_target + ("." + ".".join(rest) if rest else "")
                    parts = full.split(".")
                    for split_point in range(len(parts) - 1, 0, -1):
                        cand_mod = ".".join(parts[:split_point])
                        cand_cls = ".".join(parts[split_point:])
                        if "." not in cand_cls and cand_cls in class_methods_index.get(cand_mod, {}):
                            resolved_list.append((cand_mod, cand_cls))
                            found = True
                            break

                if not found:
                    raw_unresolved.append(base_str)

            resolved_bases[module][c["name"]] = {
                "resolved": resolved_list,
                "raw": raw_unresolved,
            }
    return resolved_bases


def _find_method_in_hierarchy(module, class_name, method_name,
                               global_class_methods, global_resolved_bases,
                               visited=None):
    """
    D-004: walk the resolved base-class chain (across modules) looking for
    `method_name`. Cycle-safe via `visited`.
    """
    if visited is None:
        visited = set()
    key = (module, class_name)
    if key in visited:
        return None
    visited.add(key)

    bases = global_resolved_bases.get(module, {}).get(class_name, {}).get("resolved", [])
    for base_mod, base_cls in bases:
        methods = global_class_methods.get(base_mod, {}).get(base_cls, {})
        if method_name in methods:
            return methods[method_name]
        found = _find_method_in_hierarchy(
            base_mod, base_cls, method_name,
            global_class_methods, global_resolved_bases, visited
        )
        if found:
            return found
    return None


def _flatten_attribute(node):
    """
    Flattens an ast.Attribute call-target chain into (root_name, [parts...]).
    e.g. for `pkg.utils.helper`, node = Attribute(attr='helper',
         value=Attribute(attr='utils', value=Name('pkg')))
         -> ("pkg", ["utils", "helper"])
    For `lines.append`, node = Attribute(attr='append', value=Name('lines'))
         -> ("lines", ["append"])
    Returns (None, None) if the chain isn't rooted in a simple Name.
    """
    parts = []
    cur = node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
        parts.reverse()
        return parts[0], parts[1:]
    return None, None


def _resolve_dotted_path(full_path, global_func_index, global_class_methods):
    """
    Gap 1 helper: given a fully-qualified dotted path (e.g.
    "pkg.utils.helper" or "pkg.utils.Greeter.greet"), try every
    module/symbol split point and resolve against the global indices.

    Returns (resolved_id, kind) or (None, None).
    kind in {"function", "class_construct", "method"}
    """
    parts = full_path.split(".")
    for split_point in range(len(parts) - 1, 0, -1):
        module = ".".join(parts[:split_point])
        symbol = parts[split_point:]

        if len(symbol) == 1:
            s = symbol[0]
            if s in global_func_index.get(module, {}):
                return global_func_index[module][s], "function"
            if s in global_class_methods.get(module, {}):
                init = global_class_methods[module][s].get("__init__")
                return (init or f"{module}.{s}.<class>"), "class_construct"
        elif len(symbol) == 2:
            cls, meth = symbol
            methods = global_class_methods.get(module, {}).get(cls, {})
            if meth in methods:
                return methods[meth], "method"

    return None, None


class CallResolver(ast.NodeVisitor):
    """
    Stage B per-module call visitor.
    """

    BUILTINS = {
        "print", "len", "range", "open", "str", "int", "float", "list",
        "dict", "set", "tuple", "bool", "isinstance", "super", "enumerate",
        "zip", "map", "filter", "sorted", "sum", "min", "max", "abs",
        "getattr", "setattr", "hasattr", "type", "repr", "format",
        "round", "any", "all", "next", "iter", "id", "hash", "vars",
        "callable", "issubclass", "frozenset", "bytes", "bytearray",
        "object", "property", "staticmethod", "classmethod", "slice",
        "reversed", "divmod", "pow", "chr", "ord", "hex", "oct", "bin",
        "globals", "locals", "input", "exec", "eval", "compile",
        "__import__", "delattr", "memoryview", "complex",
        # Builtin exception types (D-003)
        "Exception", "ValueError", "TypeError", "KeyError", "IndexError",
        "AttributeError", "RuntimeError", "StopIteration", "FileNotFoundError",
        "NotImplementedError", "OSError", "IOError", "ZeroDivisionError",
        "ImportError", "NameError", "AssertionError", "Warning",
        "DeprecationWarning", "PermissionError", "TimeoutError",
    }

    # D-003: methods provided by common stdlib base classes. Used as a
    # fallback when self.X() isn't found anywhere in the resolved
    # inheritance chain (D-004) AND the class has an unresolved
    # (stdlib/3rd-party) base.
    STDLIB_INHERITED_METHODS = {
        "generic_visit", "visit", "visit_Module",  # ast.NodeVisitor
        "__post_init__",                            # dataclasses
        "__repr__", "__str__", "__eq__", "__hash__", "__len__",
        "__iter__", "__next__", "__enter__", "__exit__",
        # unittest.TestCase (D-005)
        "assertEqual", "assertNotEqual", "assertTrue", "assertFalse",
        "assertIs", "assertIsNot", "assertIsNone", "assertIsNotNone",
        "assertIn", "assertNotIn", "assertIsInstance", "assertNotIsInstance",
        "assertRaises", "assertRaisesRegex", "assertWarns", "assertLogs",
        "assertAlmostEqual", "assertNotAlmostEqual", "assertGreater",
        "assertGreaterEqual", "assertLess", "assertLessEqual",
        "assertRegex", "assertNotRegex", "assertCountEqual",
        "assertListEqual", "assertDictEqual", "assertSetEqual",
        "assertTupleEqual", "assertMultiLineEqual", "assertSequenceEqual",
        "setUp", "tearDown", "setUpClass", "tearDownClass", "fail", "skipTest",
    }

    def __init__(self, module_name, local_funcs, class_methods,
                 import_alias_map, global_func_index, global_class_methods,
                 resolved_bases=None, global_resolved_bases=None,
                 project_module_roots=None, nested_func_index=None):
        self.module_name = module_name
        self.local_funcs = local_funcs
        self.class_methods = class_methods
        self.import_alias_map = import_alias_map
        self.global_func_index = global_func_index
        self.global_class_methods = global_class_methods
        # this module's {class_name: {"resolved": [...], "raw": [...]}}
        self.resolved_bases = resolved_bases or {}
        # ALL modules' resolved_bases, for cross-module hierarchy walk (D-004)
        self.global_resolved_bases = global_resolved_bases or {}
        self.project_module_roots = project_module_roots or set()
        # D-006: {(scope_or_None, name): full_id} for nested function calls
        self.nested_func_index = nested_func_index or {}

        self.calls = []
        self.unresolved = []
        self._scope_stack = []
        self._current_class = None

        # Gap 2: per-function-scope local variable -> type binding.
        # Stack so each function gets its own scope; index 0 = module level.
        self._type_scopes = [{}]

    # ------------------------------------------------------------ #
    # Scope tracking
    # ------------------------------------------------------------ #

    def visit_ClassDef(self, node):
        prev = self._current_class
        self._current_class = node.name
        self.generic_visit(node)
        self._current_class = prev

    def visit_FunctionDef(self, node):
        self._scope_stack.append(node.name)
        self._type_scopes.append({})
        self.generic_visit(node)
        self._type_scopes.pop()
        self._scope_stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def _caller_id(self):
        if not self._scope_stack:
            return f"{self.module_name}.<module>"
        qualname = ".".join(self._scope_stack)
        if self._current_class:
            qualname = f"{self._current_class}.{qualname}"
        return f"{self.module_name}.{qualname}"

    # ------------------------------------------------------------ #
    # Gap 2: local type tracking
    # ------------------------------------------------------------ #

    def visit_Assign(self, node):
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            type_info = self._classify_assignment_value(node.value)
            scope = self._type_scopes[-1]
            if type_info:
                scope[node.targets[0].id] = type_info
            else:
                scope.pop(node.targets[0].id, None)
        self.generic_visit(node)

    def _lookup_local_type(self, name):
        for scope in reversed(self._type_scopes):
            if name in scope:
                return scope[name]
        return None

    def _classify_assignment_value(self, node):
        """Non-predictive: only classify obvious literal/constructor shapes."""
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
                    return ("class", self.module_name, cname)
                target = self.import_alias_map.get(cname)
                if target:
                    parts = target.split(".")
                    for sp in range(len(parts) - 1, 0, -1):
                        mod, cls = ".".join(parts[:sp]), ".".join(parts[sp:])
                        if "." not in cls and cls in self.global_class_methods.get(mod, {}):
                            return ("class", mod, cls)
            elif isinstance(node.func, ast.Attribute):
                root, rest = _flatten_attribute(node.func)
                if root and rest:
                    for full in self._qualified_candidates(root, rest):
                        parts = full.split(".")
                        for sp in range(len(parts) - 1, 0, -1):
                            mod, cls = ".".join(parts[:sp]), ".".join(parts[sp:])
                            if "." not in cls and cls in self.global_class_methods.get(mod, {}):
                                return ("class", mod, cls)
        return None

    # ------------------------------------------------------------ #
    # Gap 1: qualified module-path candidates
    # ------------------------------------------------------------ #

    def _qualified_candidates(self, root, rest):
        """Build candidate fully-qualified dotted paths for `root.rest...`."""
        candidates = []
        if root in self.project_module_roots:
            candidates.append(".".join([root] + rest))
        if root in self.import_alias_map:
            alias_target = self.import_alias_map[root]
            candidates.append(alias_target + ("." + ".".join(rest) if rest else ""))
        return candidates

    def _current_scope_str(self):
        """Returns the dotted scope path used as 'scope' in function_graph
        entries, e.g. for nested func 'inner' inside 'outer', scope='outer'."""
        if not self._scope_stack:
            return None
        if self._current_class:
            return ".".join([self._current_class] + self._scope_stack)
        return ".".join(self._scope_stack)

    def _resolve_nested_func_call(self, node, caller, name):
        """D-006: resolve recursive/sibling calls to a NESTED function
        (scope != None in function_graph), by walking outward from the
        current scope. Returns True if resolved (and appends the call)."""
        scope_chain = list(self._scope_stack)
        if self._current_class:
            scope_chain = [self._current_class] + scope_chain

        for i in range(len(scope_chain), -1, -1):
            scope_key = ".".join(scope_chain[:i]) if i > 0 else None
            full_id = self.nested_func_index.get((scope_key, name))
            if full_id and full_id != self.local_funcs.get(name):
                # avoid double-handling top-level funcs (already handled above)
                self.calls.append({
                    "caller": caller, "callee": full_id,
                    "lineno": node.lineno, "resolution": "nested_function_call",
                })
                return True
        return False



    def _resolve_imported_name(self, name):
        target = self.import_alias_map.get(name)
        if not target:
            return None, None

        root = target.split(".")[0]
        if root not in self.global_func_index and root not in self.global_class_methods:
            return None, "external"

        resolved, kind = _resolve_dotted_path(target, self.global_func_index, self.global_class_methods)
        if resolved:
            return resolved, "resolved"
        return None, None

    # ------------------------------------------------------------ #
    # Main call visitor
    # ------------------------------------------------------------ #

    def visit_Call(self, node):
        caller = self._caller_id()

        if isinstance(node.func, ast.Name):
            self._resolve_name_call(node, caller)
        elif isinstance(node.func, ast.Attribute):
            self._resolve_attribute_call(node, caller)

        self.generic_visit(node)

    def _resolve_name_call(self, node, caller):
        name = node.func.id

        if name in self.local_funcs:
            self.calls.append({
                "caller": caller, "callee": self.local_funcs[name],
                "lineno": node.lineno, "resolution": "direct_name_call",
            })
        elif self._current_class and name in self.class_methods.get(self._current_class, {}):
            self.calls.append({
                "caller": caller,
                "callee": self.class_methods[self._current_class][name],
                "lineno": node.lineno, "resolution": "same_class_name_call",
            })
        elif name in self.class_methods:
            init = self.class_methods[name].get("__init__")
            self.calls.append({
                "caller": caller,
                "callee": init or f"{self.module_name}.{name}.<class>",
                "lineno": node.lineno, "resolution": "same_module_class_call",
            })
        elif self._resolve_nested_func_call(node, caller, name):
            pass
        else:
            resolved, kind = self._resolve_imported_name(name)
            if resolved:
                self.calls.append({
                    "caller": caller, "callee": resolved,
                    "lineno": node.lineno, "resolution": "imported_call",
                })
            elif kind == "external":
                self.calls.append({
                    "caller": caller,
                    "callee": f"<external>.{self.import_alias_map[name]}",
                    "lineno": node.lineno, "resolution": "external_constructor_call",
                })
            elif name in self.BUILTINS:
                pass
            else:
                self.unresolved.append({
                    "module": self.module_name, "lineno": node.lineno,
                    "pattern": "name_call_unresolved",
                    "note": f"Call to '{name}(...)' not found in local, "
                            f"imported, or builtin symbols.",
                })

    def _resolve_attribute_call(self, node, caller):
        # ---- self.method() : D-003 + D-004 ----
        if (isinstance(node.func.value, ast.Name) and node.func.value.id == "self"
                and self._current_class):
            self._resolve_self_method_call(node, caller)
            return

        root, rest = _flatten_attribute(node.func)
        if root is None:
            self.unresolved.append({
                "module": self.module_name, "lineno": node.lineno,
                "pattern": "attribute_call",
                "note": f"Call via attribute access .{node.func.attr}(...) - "
                        f"target object type not statically resolved.",
            })
            return

        # ---- Gap 1: qualified module call (e.g. pkg.utils.helper(),
        #      or utils.helper() after `from pkg import utils`) ----
        if len(rest) >= 1:
            for full in self._qualified_candidates(root, rest):
                resolved, kind = _resolve_dotted_path(
                    full, self.global_func_index, self.global_class_methods
                )
                if resolved:
                    self.calls.append({
                        "caller": caller, "callee": resolved,
                        "lineno": node.lineno, "resolution": "qualified_module_call",
                    })
                    return

        # ---- Gap 2: local variable type tracking (single-level only,
        #      e.g. `lines.append(x)` where rest == ["append"]) ----
        if len(rest) == 1:
            method_name = rest[0]
            type_info = self._lookup_local_type(root)
            if type_info:
                kind = type_info[0]
                if kind == "builtin":
                    builtin_type = type_info[1]
                    self.calls.append({
                        "caller": caller,
                        "callee": f"<builtin>.{builtin_type}.{method_name}",
                        "lineno": node.lineno,
                        "resolution": "local_builtin_method_call",
                    })
                    return
                elif kind == "class":
                    _, cls_mod, cls_name = type_info
                    found = self.global_class_methods.get(cls_mod, {}).get(cls_name, {}).get(method_name)
                    if not found:
                        found = _find_method_in_hierarchy(
                            cls_mod, cls_name, method_name,
                            self.global_class_methods, self.global_resolved_bases
                        )
                    if found:
                        self.calls.append({
                            "caller": caller, "callee": found,
                            "lineno": node.lineno,
                            "resolution": "local_typed_method_call",
                        })
                        return

        # ---- Fallback: honest unresolved ----
        self.unresolved.append({
            "module": self.module_name, "lineno": node.lineno,
            "pattern": "attribute_call",
            "note": f"Call via attribute access .{node.func.attr}(...) - "
                    f"target object type not statically resolved.",
        })

    def _resolve_self_method_call(self, node, caller):
        method_name = node.func.attr
        methods = self.class_methods.get(self._current_class, {})

        # 1. Own class
        if method_name in methods:
            self.calls.append({
                "caller": caller, "callee": methods[method_name],
                "lineno": node.lineno, "resolution": "self_method_call",
            })
            return

        # 2. D-004: walk resolved inheritance chain (cross-module aware)
        found = _find_method_in_hierarchy(
            self.module_name, self._current_class, method_name,
            self.global_class_methods, self.global_resolved_bases
        )
        if found:
            self.calls.append({
                "caller": caller, "callee": found,
                "lineno": node.lineno, "resolution": "inherited_method_call",
            })
            return

        # 3. D-003: stdlib-base-class whitelist fallback, using bases that
        #    D-004 could NOT resolve to project classes
        raw_bases = self.resolved_bases.get(self._current_class, {}).get("raw", [])
        if method_name in self.STDLIB_INHERITED_METHODS and raw_bases:
            self.calls.append({
                "caller": caller,
                "callee": f"<external>.{'/'.join(raw_bases)}.{method_name}",
                "lineno": node.lineno,
                "resolution": "external_inherited_call",
            })
            return

        # 4. Honest unresolved
        self.unresolved.append({
            "module": self.module_name, "lineno": node.lineno,
            "pattern": "self_method_not_found",
            "note": f"self.{method_name}(...) not found in class "
                    f"'{self._current_class}' or its resolved inheritance "
                    f"chain (D-004), and not a recognized stdlib-base method.",
        })


def build_call_graph(module_trees, function_graph, class_graph,
                      import_alias_maps, project_module_roots=None):
    """
    Top-level Stage B entry point.

    module_trees: {module_name: ast.AST}
    function_graph, class_graph: Stage A outputs (all modules)
    import_alias_maps: {module_name: {local_name: "target.module.symbol"}}
    project_module_roots: set of top-level package/module names in this repo
                           (used by Gap 1 for `pkg.submodule.func()` patterns)

    Returns: (call_graph: {module: [edges]}, unresolved: [list])
    """
    local_func_index, class_methods_index, nested_func_index = build_global_symbol_index(
        function_graph, class_graph
    )

    # D-004: resolve class bases globally (all modules)
    resolved_bases_index = build_resolved_bases(
        class_graph, class_methods_index, import_alias_maps
    )

    call_graph = {}
    unresolved = []

    for module_name, tree in module_trees.items():
        resolver = CallResolver(
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
        )
        resolver.visit(tree)
        call_graph[module_name] = resolver.calls
        unresolved.extend(resolver.unresolved)

    return call_graph, unresolved
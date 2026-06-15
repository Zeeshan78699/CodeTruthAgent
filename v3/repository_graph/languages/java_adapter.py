"""
java_adapter.py
First real implementation, using `javalang` (pure-Python Java parser,
pip install javalang).

SCOPE (honest, matches Python's pre-D-001 starting point):
  - Per-file extraction only: function_graph, class_graph, module_graph,
    import_graph/dependency_graph, and SAME-FILE call resolution.
  - NO cross-file/cross-package call resolution yet (Java's equivalent of
    D-001's global symbol table). Calls to methods in other files are
    logged in `unresolved` with pattern "cross_file_unresolved" - same
    honest-boundary philosophy as Python's `attribute_call`.
  - Java imports are always absolute (no relative-import equivalent of
    D-007 needed).

FUTURE enhancements (mirroring Python's evolution):
  - D-001 equivalent: build a project-wide symbol table across all .java
    files (keyed by fully-qualified package.Class.method), then resolve
    cross-file calls in a second pass.
  - D-004 equivalent: resolve `extends`/`implements` across files for
    inherited-method calls.
  - Gap2 equivalent: local variable type tracking for `var.method()` calls.
"""

import os
import javalang

from .base_adapter import LanguageAdapter


def _module_name_from_path(repo_root, filepath, package_name):
    """Java module identity = package.ClassFileName (best-effort)."""
    base = os.path.splitext(os.path.basename(filepath))[0]
    if package_name:
        return f"{package_name}.{base}"
    return base


class JavaAdapter(LanguageAdapter):
    language_name = "java"
    file_extensions = {".java"}

    def is_implemented(self) -> bool:
        return True

    def scan(self, repo_root: str, file_paths: list) -> dict:
        function_graph = {}
        class_graph = {}
        module_graph = {}
        import_graph = {}
        dependency_graph = {}
        call_graph = {}
        unresolved = []

        # Track every (module, ClassName) -> {method_name: full_id} for
        # same-file resolution, and a flat set of all known full_ids for
        # the cross_file_unresolved check.
        all_class_methods = {}

        parsed = {}  # module_name -> (tree, package_name)

        for filepath in file_paths:
            try:
                with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                    source = f.read()
                tree = javalang.parse.parse(source)
            except (javalang.parser.JavaSyntaxError, Exception) as e:
                module_name = _module_name_from_path(repo_root, filepath, None)
                unresolved.append({
                    "module": module_name, "lineno": 0,
                    "pattern": "parse_error",
                    "note": f"{type(e).__name__}: {e}",
                })
                continue

            package_name = tree.package.name if tree.package else None
            module_name = _module_name_from_path(repo_root, filepath, package_name)
            parsed[module_name] = (tree, filepath)

            module_graph[module_name] = {
                "path": filepath,
                "parent": package_name,
                "is_package": False,
            }

            # ---- function_graph (V3-004) + class_graph (V3-005) ----
            funcs, classes = [], []
            all_class_methods[module_name] = {}
            for path, cls in tree.filter(javalang.tree.ClassDeclaration):
                bases = []
                if cls.extends:
                    bases.append(getattr(cls.extends, "name", str(cls.extends)))
                for impl in (cls.implements or []):
                    bases.append(getattr(impl, "name", str(impl)))
                classes.append({
                    "id": f"{module_name}.{cls.name}",
                    "name": cls.name,
                    "lineno": cls.position.line if cls.position else 0,
                    "bases": bases,
                    "scope": None,
                })
                all_class_methods[module_name][cls.name] = {}
                for m in cls.methods:
                    full_id = f"{module_name}.{cls.name}.{m.name}"
                    funcs.append({
                        "id": full_id,
                        "name": m.name,
                        "lineno": m.position.line if m.position else 0,
                        "scope": cls.name,
                        "is_async": False,
                    })
                    all_class_methods[module_name][cls.name][m.name] = full_id

            function_graph[module_name] = funcs
            class_graph[module_name] = classes

            # ---- import_graph / dependency_graph (V3-007/008) ----
            # Java imports are always absolute - split internal (matches
            # this project's package root) vs external (java.*, 3rd-party).
            internal_imports, external_imports = [], []
            project_root_pkg = package_name.split(".")[0] if package_name else None
            for imp in tree.imports:
                entry = {
                    "from_module": module_name,
                    "imports": imp.path,
                    "type": "import",
                    "lineno": 0,
                }
                if project_root_pkg and imp.path.startswith(project_root_pkg + "."):
                    internal_imports.append(entry)
                else:
                    external_imports.append(entry)
                    root = imp.path.split(".")[0]
                    dependency_graph.setdefault(root, {"used_by": [], "import_count": 0})
                    if module_name not in dependency_graph[root]["used_by"]:
                        dependency_graph[root]["used_by"].append(module_name)
                    dependency_graph[root]["import_count"] += 1

            import_graph[module_name] = internal_imports

        # ---- call_graph (V3-009) - same-file resolution only ----
        for module_name, (tree, filepath) in parsed.items():
            calls = []
            for path, cls in tree.filter(javalang.tree.ClassDeclaration):
                current_class = cls.name
                for m in cls.methods:
                    if not m.body:
                        continue
                    caller = f"{module_name}.{current_class}.{m.name}"
                    for _, inv in _walk_invocations(m.body):
                        line = inv.position.line if inv.position else 0
                        if inv.qualifier in (None, "", "this"):
                            # same-class method call
                            target = all_class_methods.get(module_name, {}).get(current_class, {})
                            if inv.member in target:
                                calls.append({
                                    "caller": caller, "callee": target[inv.member],
                                    "lineno": line, "resolution": "self_method_call",
                                })
                            else:
                                unresolved.append({
                                    "module": module_name, "lineno": line,
                                    "pattern": "cross_file_unresolved",
                                    "note": f"Call to '{inv.member}(...)' (this/implicit) "
                                            f"not found in class '{current_class}' - may be "
                                            f"inherited or defined in another file "
                                            f"(cross-file resolution not yet implemented).",
                                })
                        else:
                            unresolved.append({
                                "module": module_name, "lineno": line,
                                "pattern": "cross_file_unresolved",
                                "note": f"Call '{inv.qualifier}.{inv.member}(...)' - "
                                        f"qualifier resolution across files/imports not "
                                        f"yet implemented.",
                            })
            call_graph[module_name] = calls

        return {
            "function_graph": function_graph,
            "class_graph": class_graph,
            "module_graph": module_graph,
            "import_graph": import_graph,
            "dependency_graph": dependency_graph,
            "call_graph": call_graph,
            "unresolved": unresolved,
            "cyclic_clusters": [],
        }


def _walk_invocations(node):
    """Yield (path, MethodInvocation) for all method invocations in a
    method body, using javalang's tree.filter on the body list."""
    for stmt in node:
        if hasattr(stmt, "filter"):
            for path, inv in stmt.filter(javalang.tree.MethodInvocation):
                yield path, inv
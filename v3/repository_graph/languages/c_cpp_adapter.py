"""
c_cpp_adapter.py
First implementation - REGEX-BASED HEURISTIC, not AST-based.

HONESTY NOTE (important): unlike Python (ast module), Java (javalang), and
JavaScript (esprima), this adapter does NOT use a real parser. C/C++'s
preprocessor (#ifdef, macros) and grammar complexity make a lightweight
pure-Python AST parser impractical without a heavy dependency (libclang,
tree-sitter). This adapter uses regex pattern-matching as a STARTING POINT:

  - Lower precision than the AST-based adapters - multi-line signatures,
    macro-expanded code, templates, and operator overloads will often be
    missed or mis-attributed.
  - Every extracted item should be treated with LOWER confidence than
    Python/Java/JS results.

FUTURE: replace with a libclang or tree-sitter-c/tree-sitter-cpp based
implementation for AST-level accuracy, matching the other adapters'
contract (same 6-graph shape - no downstream changes needed, per
base_adapter.py's design).

SCOPE of this first pass:
  - function_graph (V3-004): top-level function definitions (heuristic
    regex match on "<return type> name(args) {")
  - class_graph (V3-005): C++ class/struct definitions + public/private
    inheritance as bases
  - import_graph/dependency_graph (V3-007/008): #include "local.h"
    (internal) vs #include <system.h> (external)
  - call_graph (V3-009): same-file calls to functions found in
    function_graph; everything else -> "cross_file_unresolved"
    (consistent with Java/JS adapters' current scope)
"""

import os
import re

from .base_adapter import LanguageAdapter


_INCLUDE_RE = re.compile(r'^\s*#\s*include\s*[<"]([^>"]+)[>"]')

_FUNC_DEF_RE = re.compile(
    r'^[A-Za-z_][\w:\*&<>,\s]*?\b([A-Za-z_]\w*)\s*\(([^;{}]*)\)\s*(?:const\s*)?\{'
)

# Kernel/Linux style: signature ends the line with ')' only, '{' is on the
# NEXT line by itself. Very common in u-boot, Linux kernel, etc.
_FUNC_SIG_ONLY_RE = re.compile(
    r'^[A-Za-z_][\w:\*&<>,\s]*?\b([A-Za-z_]\w*)\s*\(([^;{}]*)\)\s*$'
)

_CLASS_RE = re.compile(
    r'^\s*(class|struct)\s+([A-Za-z_]\w*)'
    r'(?:\s*:\s*((?:public|private|protected)?\s*[A-Za-z_:][\w:<>,\s]*))?'
    r'\s*\{?'
)

_CALL_RE = re.compile(r'\b([A-Za-z_]\w*)\s*\(')

# Keywords that look like calls in regex but aren't function calls.
_CONTROL_KEYWORDS = {
    "if", "for", "while", "switch", "return", "sizeof", "catch",
    "do", "else", "new", "delete", "static_cast", "dynamic_cast",
    "reinterpret_cast", "const_cast", "throw", "typeof", "decltype",
    "noexcept", "explicit", "static", "inline", "void", "int", "char",
    "float", "double", "bool", "auto", "namespace", "using", "template",
    "typename", "struct", "class", "enum", "union", "public", "private",
    "protected", "virtual", "override", "final", "operator",
}


def _module_name_from_path(repo_root, filepath):
    rel = os.path.relpath(filepath, repo_root)
    rel_no_ext = os.path.splitext(rel)[0]
    return rel_no_ext.replace(os.sep, ".").replace("/", ".")


class CCppAdapter(LanguageAdapter):
    language_name = "c_cpp"
    file_extensions = {".c", ".h", ".cpp", ".cc", ".cxx", ".hpp", ".hh", ".hxx"}

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

        for filepath in file_paths:
            module_name = _module_name_from_path(repo_root, filepath)

            try:
                with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()
            except Exception as e:
                unresolved.append({
                    "module": module_name, "lineno": 0,
                    "pattern": "parse_error",
                    "note": f"{type(e).__name__}: {e}",
                })
                continue

            module_graph[module_name] = {
                "path": filepath, "parent": None, "is_package": False,
            }

            funcs, classes = [], []
            internal_imports = []
            local_func_names = set()
            local_func_spans = []  # (start_line_idx, name)

            for i, raw_line in enumerate(lines):
                line = raw_line.strip()

                inc = _INCLUDE_RE.match(line)
                if inc:
                    target = inc.group(1)
                    if raw_line.strip().startswith('#include "'):
                        internal_imports.append({
                            "from_module": module_name, "imports": target,
                            "type": "include", "lineno": i + 1,
                        })
                    else:
                        root = target.split("/")[0].replace(".h", "")
                        dependency_graph.setdefault(root, {"used_by": [], "import_count": 0})
                        if module_name not in dependency_graph[root]["used_by"]:
                            dependency_graph[root]["used_by"].append(module_name)
                        dependency_graph[root]["import_count"] += 1
                    continue

                cls = _CLASS_RE.match(line)
                if cls and "{" in line:
                    bases = []
                    if cls.group(3):
                        for b in cls.group(3).split(","):
                            b = b.strip()
                            for kw in ("public", "private", "protected"):
                                b = b.replace(kw, "").strip()
                            if b:
                                bases.append(b)
                    classes.append({
                        "id": f"{module_name}.{cls.group(2)}",
                        "name": cls.group(2),
                        "lineno": i + 1,
                        "bases": bases,
                        "scope": None,
                    })
                    continue

                func = _FUNC_DEF_RE.match(line)
                if func and func.group(1) not in _CONTROL_KEYWORDS:
                    name = func.group(1)
                    full_id = f"{module_name}.{name}"
                    funcs.append({
                        "id": full_id, "name": name, "lineno": i + 1,
                        "scope": None, "is_async": False,
                    })
                    local_func_names.add(name)
                    local_func_spans.append((i, name))
                    continue

                # Kernel/Linux-style: signature ends with ')' alone, '{' is
                # the next non-blank line.
                sig = _FUNC_SIG_ONLY_RE.match(line)
                if sig and sig.group(1) not in _CONTROL_KEYWORDS:
                    j = i + 1
                    while j < len(lines) and lines[j].strip() == "":
                        j += 1
                    if j < len(lines) and lines[j].strip() == "{":
                        name = sig.group(1)
                        full_id = f"{module_name}.{name}"
                        funcs.append({
                            "id": full_id, "name": name, "lineno": i + 1,
                            "scope": None, "is_async": False,
                        })
                        local_func_names.add(name)
                        local_func_spans.append((i, name))

            function_graph[module_name] = funcs
            class_graph[module_name] = classes
            import_graph[module_name] = internal_imports

            # ---- call_graph: heuristic, same-file only ----
            # For each function, scan from its definition line to the next
            # function's definition line (or EOF) for call-shaped patterns.
            calls = []
            seen_unresolved = set()
            for idx, (start_line, fname) in enumerate(local_func_spans):
                end_line = (local_func_spans[idx + 1][0]
                             if idx + 1 < len(local_func_spans) else len(lines))
                caller = f"{module_name}.{fname}"
                for j in range(start_line, min(end_line, len(lines))):
                    for m in _CALL_RE.finditer(lines[j]):
                        callee_name = m.group(1)
                        if callee_name == fname and j == start_line:
                            continue  # skip the definition line's own name
                        if callee_name in _CONTROL_KEYWORDS:
                            continue
                        if callee_name in local_func_names:
                            calls.append({
                                "caller": caller,
                                "callee": f"{module_name}.{callee_name}",
                                "lineno": j + 1, "resolution": "direct_name_call",
                            })
                        else:
                            key = (module_name, j + 1, callee_name)
                            if key not in seen_unresolved:
                                seen_unresolved.add(key)
                                unresolved.append({
                                    "module": module_name, "lineno": j + 1,
                                    "pattern": "cross_file_unresolved",
                                    "note": f"Call to '{callee_name}(...)' - not a "
                                            f"locally-defined function in this file "
                                            f"(regex-based heuristic; cross-file/"
                                            f"library resolution not yet implemented).",
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
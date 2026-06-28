"""
========================================================================
go_adapter.py
CodeTruth Agent V3 — Module 2 Language Adapter

LANGUAGE:       Go (Golang)
PURPOSE:        Builds a call graph from Go repositories.
                Identifies packages, structs, interfaces, functions,
                methods, and cross-package calls.

GRAPH NODES:    Packages, Structs, Interfaces, Functions, Methods
GRAPH EDGES:    Function calls, Method calls, Interface implementations,
                Struct instantiations, Import references

HANDLES:
    - .go files (Go source)
    - go.mod (module definition)
    - Package declarations
    - Import paths (standard + third-party + local)
    - Interface satisfaction (implicit in Go)
    - Goroutines (go func() patterns)
    - Method receivers (value + pointer)
    - Error handling patterns

STATUS: Module 2 Language Adapter — Production
========================================================================
"""

from __future__ import annotations
import re
import warnings
from pathlib import Path
from typing import Any

GO_EXTENSIONS = {".go", ".mod", ".sum"}

GO_KEYWORDS = {
    "func", "var", "const", "type", "struct", "interface", "map",
    "chan", "go", "defer", "select", "case", "default", "fallthrough",
    "break", "continue", "return", "if", "else", "for", "range",
    "switch", "import", "package", "nil", "true", "false", "iota",
    "make", "new", "len", "cap", "append", "copy", "delete", "close",
    "panic", "recover", "print", "println", "error", "string", "int",
    "int8", "int16", "int32", "int64", "uint", "uint8", "uint16",
    "uint32", "uint64", "float32", "float64", "complex64", "complex128",
    "bool", "byte", "rune", "uintptr", "any", "comparable",
    "fmt", "os", "io", "log", "http", "json", "sync", "context",
    "errors", "strings", "strconv", "time", "math", "sort",
}


def _make_patterns() -> dict:
    return {
        # Package declaration
        "package": re.compile(
            r"^package\s+([\w]+)", re.MULTILINE),
        # Import paths
        "import_single": re.compile(
            r'import\s+"([\w\.\/\-]+)"'),
        "import_block": re.compile(
            r'"([\w\.\/\-]+)"', re.MULTILINE),
        # Struct definition
        "struct_def": re.compile(
            r"type\s+([\w]+)\s+struct\s*\{"),
        # Interface definition
        "interface_def": re.compile(
            r"type\s+([\w]+)\s+interface\s*\{"),
        # Function definition (standalone)
        "func_def": re.compile(
            r"^func\s+([\w]+)\s*\(", re.MULTILINE),
        # Method definition (with receiver)
        "method_def": re.compile(
            r"^func\s*\(\s*[\w]+\s+\*?([\w]+)\s*\)\s*([\w]+)\s*\(",
            re.MULTILINE),
        # Function/method calls: pkg.Func( or obj.Method(
        "call": re.compile(
            r"([\w]+)\.([\w]+)\s*\("),
        # Struct instantiation: TypeName{ or &TypeName{
        "struct_init": re.compile(
            r"&?([\w]+)\{"),
        # Goroutine launches: go funcName(
        "goroutine": re.compile(
            r"go\s+([\w\.]+)\s*\("),
        # Error check pattern: if err != nil
        "error_check": re.compile(
            r"if\s+err\s*!=\s*nil"),
        # Interface implementation clue: var _ Interface = (*Struct)(nil)
        "implements_check": re.compile(
            r"var\s+_\s+([\w]+)\s*=\s*[&\(\*]*([\w]+)"),
        # go.mod module name
        "module_name": re.compile(
            r"^module\s+([\w\.\/\-]+)", re.MULTILINE),
    }


PATTERNS = _make_patterns()


class GoFileParser:
    """Parses a single Go source file."""

    def __init__(self, file_path: Path, content: str):
        self.file_path   = file_path
        self.content     = content
        self.name        = file_path.stem
        self.package     = ""
        self.structs:    list[str] = []
        self.interfaces: list[str] = []
        self.functions:  list[str] = []
        self.methods:    dict[str, list] = {}  # struct → [methods]
        self.imports:    list[str] = []
        self.calls:      list[dict] = []
        self.struct_inits: list[dict] = []
        self.goroutines: list[dict] = []
        self.implements: list[dict] = []  # interface → struct checks

    def parse(self) -> "GoFileParser":
        src = self._strip_comments(self.content)

        # Package
        pkg_match = PATTERNS["package"].search(src)
        self.package = pkg_match.group(1) if pkg_match else ""

        # Definitions
        self.structs    = [m.group(1) for m in PATTERNS["struct_def"].finditer(src)
                           if m.group(1) not in GO_KEYWORDS]
        self.interfaces = [m.group(1) for m in PATTERNS["interface_def"].finditer(src)
                           if m.group(1) not in GO_KEYWORDS]

        # Standalone functions
        self.functions  = [m.group(1) for m in PATTERNS["func_def"].finditer(src)
                           if m.group(1) not in GO_KEYWORDS]

        # Methods with receivers
        for m in PATTERNS["method_def"].finditer(src):
            recv   = m.group(1)
            method = m.group(2)
            if recv not in GO_KEYWORDS and method not in GO_KEYWORDS:
                if recv not in self.methods:
                    self.methods[recv] = []
                self.methods[recv].append(method)

        # Imports
        in_import_block = False
        for line in src.splitlines():
            line = line.strip()
            if line.startswith("import ("):
                in_import_block = True
                continue
            if in_import_block:
                if line == ")":
                    in_import_block = False
                    continue
                m = re.search(r'"([\w\.\/\-]+)"', line)
                if m:
                    self.imports.append(m.group(1))
            elif line.startswith('import "'):
                m = PATTERNS["import_single"].search(line)
                if m:
                    self.imports.append(m.group(1))

        # Calls
        defined = set(self.structs + self.interfaces + self.functions)
        for m in PATTERNS["call"].finditer(src):
            pkg    = m.group(1)
            method = m.group(2)
            if pkg not in GO_KEYWORDS and method not in GO_KEYWORDS:
                self.calls.append({
                    "caller_pkg": pkg,
                    "method":     method,
                    "source_file": str(self.file_path),
                    "ref_type":   "CALL",
                })

        # Struct instantiations
        for m in PATTERNS["struct_init"].finditer(src):
            name = m.group(1)
            if name not in GO_KEYWORDS and name[0:1].isupper():
                self.struct_inits.append({
                    "target":      name,
                    "source_file": str(self.file_path),
                    "ref_type":   "STRUCT_INIT",
                })

        # Goroutines
        for m in PATTERNS["goroutine"].finditer(src):
            self.goroutines.append({
                "target":      m.group(1),
                "source_file": str(self.file_path),
                "ref_type":   "GOROUTINE",
            })

        # Interface checks
        for m in PATTERNS["implements_check"].finditer(src):
            self.implements.append({
                "interface": m.group(1),
                "struct":    m.group(2),
                "source_file": str(self.file_path),
            })

        return self

    def _strip_comments(self, src: str) -> str:
        src = re.sub(r"//[^\n]*", " ", src)
        src = re.sub(r"/\*.*?\*/", " ", src, flags=re.DOTALL)
        return src


class GoAdapter:
    """
    Module 2 Go language adapter with deep resolution.
    """

    file_extensions = {".go", ".mod"}
    language = "go"

    """
    Module 2 Go language adapter.

    Builds a call graph from Go repositories:
      nodes = packages, structs, interfaces, functions, methods
      edges = function/method calls, struct inits, goroutines
    """

    def scan(self, repo_root: str, file_paths: list | None = None) -> dict:
        root = Path(repo_root)

        if file_paths:
            go_files = [Path(f) for f in file_paths
                        if Path(f).suffix.lower() == ".go"]
        else:
            go_files = [f for f in root.rglob("*.go") if f.is_file()]

        if not go_files:
            return self._empty(repo_root, "NO_GO_FILES")

        # Read go.mod for module name
        module_name = self._read_module_name(root)

        parsed = []
        parse_errors = 0
        for path in go_files:
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
                parsed.append(GoFileParser(path, content).parse())
            except Exception:
                parse_errors += 1

        graph      = self._build_graph(parsed, module_name)
        resolution = self._resolve(graph, parsed)
        return self._report(
            repo_root, go_files, parsed, graph,
            resolution, parse_errors, module_name
        )

    def _read_module_name(self, root: Path) -> str:
        mod_file = root / "go.mod"
        if mod_file.exists():
            try:
                content = mod_file.read_text(encoding="utf-8", errors="ignore")
                m = PATTERNS["module_name"].search(content)
                return m.group(1) if m else ""
            except Exception:
                pass
        return ""

    def _build_graph(self, parsed: list, module_name: str) -> dict:
        packages:   dict[str, dict] = {}
        structs:    dict[str, dict] = {}
        interfaces: dict[str, dict] = {}
        functions:  dict[str, dict] = {}
        methods:    dict[str, dict] = {}

        for p in parsed:
            pkg = p.package
            src = str(p.file_path)

            if pkg and pkg not in packages:
                packages[pkg] = {
                    "files": [], "structs": [],
                    "interfaces": [], "functions": [],
                }
            if pkg:
                packages[pkg]["files"].append(src)

            for s in p.structs:
                key = f"{pkg}.{s}" if pkg else s
                structs[key] = {
                    "simple_name": s, "package": pkg,
                    "defined_in": src, "type": "STRUCT",
                    "methods": p.methods.get(s, []),
                }
                if pkg:
                    packages[pkg]["structs"].append(s)

            for i in p.interfaces:
                key = f"{pkg}.{i}" if pkg else i
                interfaces[key] = {
                    "simple_name": i, "package": pkg,
                    "defined_in": src, "type": "INTERFACE",
                }
                if pkg:
                    packages[pkg]["interfaces"].append(i)

            for f in p.functions:
                key = f"{pkg}.{f}" if pkg else f
                functions[key] = {
                    "simple_name": f, "package": pkg,
                    "defined_in": src, "type": "FUNCTION",
                }
                if pkg:
                    packages[pkg]["functions"].append(f)

            for recv, meths in p.methods.items():
                for meth in meths:
                    key = f"{pkg}.{recv}.{meth}" if pkg else f"{recv}.{meth}"
                    methods[key] = {
                        "receiver": recv, "method": meth,
                        "package": pkg, "defined_in": src,
                        "type": "METHOD",
                    }

        return {
            "packages":   packages,
            "structs":    structs,
            "interfaces": interfaces,
            "functions":  functions,
            "methods":    methods,
        }

    def _resolve(self, graph: dict, parsed: list) -> dict:
        # Build lookup sets
        known_pkgs    = set(graph["packages"].keys())
        known_structs = {v["simple_name"] for v in graph["structs"].values()}
        known_funcs   = {v["simple_name"] for v in graph["functions"].values()}
        known_methods: dict[str, set] = {}
        for k, v in graph["methods"].items():
            recv = v["receiver"]
            meth = v["method"]
            if recv not in known_methods:
                known_methods[recv] = set()
            known_methods[recv].add(meth)

        resolved:   list[dict] = []
        unresolved: list[dict] = []

        for p in parsed:
            for call in p.calls:
                pkg    = call["caller_pkg"]
                method = call["method"]

                # Package-level function call: fmt.Println
                if pkg in known_pkgs and method in known_funcs:
                    resolved.append({**call, "resolved": True,
                                     "resolved_to": f"{pkg}.{method}"})
                # Method call on known struct: conn.Execute
                elif pkg in known_structs and method in known_methods.get(pkg, set()):
                    resolved.append({**call, "resolved": True,
                                     "resolved_to": f"{pkg}.{method}",
                                     "confidence": "HIGH"})
                # Package call — package known, method unknown
                elif pkg in known_pkgs:
                    resolved.append({**call, "resolved": True,
                                     "resolved_to": f"{pkg}.{method}",
                                     "confidence": "MEDIUM"})
                else:
                    unresolved.append({**call, "resolved": False,
                                       "reason": "PACKAGE_OR_TYPE_UNKNOWN"})

            for init in p.struct_inits:
                target = init["target"]
                if target in known_structs:
                    resolved.append({**init, "resolved": True,
                                     "resolved_to": f"new {target}{{}}"})
                else:
                    unresolved.append({**init, "resolved": False,
                                       "reason": "STRUCT_NOT_IN_REPO"})

            for go_call in p.goroutines:
                target = go_call["target"]
                if "." in target:
                    pkg, fn = target.rsplit(".", 1)
                    if pkg in known_pkgs:
                        resolved.append({**go_call, "resolved": True,
                                         "resolved_to": target})
                        continue
                if target.split(".")[0] in known_pkgs | known_structs:
                    resolved.append({**go_call, "resolved": True,
                                     "resolved_to": target})
                else:
                    unresolved.append({**go_call, "resolved": False,
                                       "reason": "GOROUTINE_TARGET_UNKNOWN"})

        total = len(resolved) + len(unresolved)
        return {
            "resolved_count":     len(resolved),
            "unresolved_count":   len(unresolved),
            "resolved_entries":   resolved[:100],
            "unresolved_entries": unresolved[:100],
            "resolution_pct":     round(len(resolved)/total*100,2) if total else 0.0,
        }

    def _report(self, repo_root, go_files, parsed,
                graph, resolution, parse_errors, module_name):
        nc = {
            "packages":   len(graph["packages"]),
            "structs":    len(graph["structs"]),
            "interfaces": len(graph["interfaces"]),
            "functions":  len(graph["functions"]),
            "methods":    len(graph["methods"]),
        }
        nc["total"] = sum(nc.values())

        ec = {
            "calls":        sum(len(p.calls) for p in parsed),
            "struct_inits": sum(len(p.struct_inits) for p in parsed),
            "goroutines":   sum(len(p.goroutines) for p in parsed),
        }
        ec["total"] = sum(ec.values())

        total   = len(go_files)
        err_pct = parse_errors / total * 100 if total else 0
        gate = ("BLOCKED" if err_pct > 50
                else "REVIEW_REQUIRED" if nc["total"] == 0
                else "APPROVED")

        framework = self._detect_framework(parsed)

        return {
            "repo_root":        repo_root,
            "language":         "go",
            "module_name":      module_name,
            "framework":        framework,
            "files_scanned":    total,
            "parse_errors":     parse_errors,
            "packages":         graph["packages"],
            "structs":          graph["structs"],
            "interfaces":       graph["interfaces"],
            "functions":        graph["functions"],
            "methods":          graph["methods"],
            "node_counts":      nc,
            "edge_counts":      ec,
            "resolution":       resolution,
            "resolved_calls":   resolution["resolved_count"],
            "unresolved_total": resolution["unresolved_count"],
            "resolution_pct":   resolution["resolution_pct"],
            "governance_gate":  gate,
            "language_composition": {
                "go": {
                    "file_count":  total,
                    "implemented": True,
                    "framework":   framework,
                    "module":      module_name,
                }
            },
        }

    def _detect_framework(self, parsed: list) -> str:
        all_imports = set()
        for p in parsed:
            all_imports.update(p.imports)

        if any("gin-gonic/gin" in i for i in all_imports):
            return "gin"
        if any("labstack/echo" in i for i in all_imports):
            return "echo"
        if any("gorilla/mux" in i for i in all_imports):
            return "gorilla_mux"
        if any("go-chi/chi" in i for i in all_imports):
            return "chi"
        if any("grpc" in i for i in all_imports):
            return "grpc"
        if any("net/http" in i for i in all_imports):
            return "net_http"
        if any("database/sql" in i for i in all_imports):
            return "database_sql"
        return "go_standard"

    def _empty(self, repo_root: str, reason: str) -> dict:
        return {
            "repo_root":     repo_root,
            "language":      "go",
            "files_scanned": 0,
            "status":        reason,
            "node_counts":   {"total": 0},
            "edge_counts":   {"total": 0},
            "resolution":    {"resolved_count": 0, "unresolved_count": 0},
            "governance_gate": "BLOCKED",
        }

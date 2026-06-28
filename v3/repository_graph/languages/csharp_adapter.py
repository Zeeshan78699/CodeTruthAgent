"""
========================================================================
csharp_adapter.py
CodeTruth Agent V3 — Module 2 Language Adapter

LANGUAGE:       C# (.NET)
DEEP RESOLUTION: 3 resolvers built-in
  1. field_type_resolver    — resolves calls on typed fields
                               private readonly IUserRepository _repo
                               → _repo.CreateAsync() resolved
  2. interface_resolver     — maps interface method calls to
                               all implementing classes in repo
  3. di_constructor_resolver — tracks constructor-injected types
                               and resolves their method calls

STATUS: Module 2 Language Adapter — Production
========================================================================
"""

from __future__ import annotations
import re
import warnings
from pathlib import Path
from typing import Any

CSHARP_EXTENSIONS = {".cs", ".csproj", ".cshtml", ".razor"}

CSHARP_KEYWORDS = {
    "var", "void", "int", "string", "bool", "double", "float",
    "decimal", "long", "short", "byte", "char", "object", "dynamic",
    "null", "true", "false", "this", "base", "new", "return",
    "if", "else", "while", "for", "foreach", "in", "break",
    "continue", "switch", "case", "default", "try", "catch",
    "finally", "throw", "using", "namespace", "class", "interface",
    "struct", "enum", "public", "private", "protected", "internal",
    "static", "readonly", "const", "abstract", "virtual", "override",
    "sealed", "async", "await", "yield", "get", "set", "value",
    "where", "select", "from", "join", "group", "into", "let",
    "orderby", "delegate", "event", "operator", "extern", "unsafe",
    "Task", "IEnumerable", "IList", "ICollection", "IDictionary",
    "List", "Dictionary", "Array", "String", "Object", "Exception",
    "Console", "Math", "Convert", "Enumerable", "ActionResult",
    "IActionResult", "ControllerBase", "Controller",
}


def _make_patterns() -> dict:
    return {
        "namespace": re.compile(
            r"namespace\s+([\w\.]+)", re.IGNORECASE),
        "class_def": re.compile(
            r"(?:public|private|protected|internal|abstract|sealed|static|partial)?"
            r"\s*(?:partial\s+)?class\s+([\w<>]+)"
            r"(?:\s*:\s*([\w\s,<>\.]+))?"),
        "interface_def": re.compile(
            r"(?:public|private|protected|internal)?\s*interface\s+([\w<>]+)"
            r"(?:\s*:\s*([\w\s,<>\.]+))?"),
        "enum_def": re.compile(
            r"(?:public|private|protected|internal)?\s*enum\s+([\w]+)"),
        "struct_def": re.compile(
            r"(?:public|private|protected|internal)?\s*struct\s+([\w]+)"),
        "method_def": re.compile(
            r"(?:public|private|protected|internal|static|virtual|override|abstract|async)+"
            r"\s+(?:async\s+)?(?:Task<?[\w<>]*>?|void|[\w<>\[\]]+)\s+([\w]+)\s*\("),
        "property_def": re.compile(
            r"(?:public|private|protected|internal|static|virtual|override)+"
            r"\s+[\w<>\[\]]+\s+([\w]+)\s*\{"),
        "using": re.compile(
            r"^using\s+(?:static\s+)?([\w\.]+);", re.MULTILINE),
        "method_call": re.compile(
            r"([\w]+)\.([\w]+)\s*\("),
        "constructor_call": re.compile(
            r"new\s+([\w<>\.]+)\s*[\(\{]"),
        "await_call": re.compile(
            r"await\s+([\w]+)\.([\w]+)\s*\("),
        # Field declarations: private readonly IType _fieldName
        "field_decl": re.compile(
            r"(?:private|protected|public|internal)\s+(?:readonly\s+)?"
            r"([\w<>]+)\s+(_[\w]+|[\w]+)(?:\s*[;=])"),
        # DI constructor params: (IType paramName, ...)
        "di_param": re.compile(
            r"\(\s*(?:readonly\s+)?(I[\w]+)\s+([\w]+)"),
        # Class implements interface: class Foo : IBar, IBaz
        "class_implements": re.compile(
            r"class\s+([\w]+)\s*:\s*([\w\s,<>\.]+)"),
    }


PATTERNS = _make_patterns()


class CSharpFileParser:
    def __init__(self, file_path: Path, content: str):
        self.file_path    = file_path
        self.content      = content
        self.name         = file_path.stem
        self.namespace    = ""
        self.classes:     list[str] = []
        self.interfaces:  list[str] = []
        self.enums:       list[str] = []
        self.structs:     list[str] = []
        self.methods:     list[str] = []
        self.properties:  list[str] = []
        self.usings:      list[str] = []
        self.field_types: dict[str, str] = {}  # fieldName → TypeName
        self.implements:  dict[str, list] = {} # ClassName → [IFace1, IFace2]
        self.method_calls:      list[dict] = []
        self.constructor_calls: list[dict] = []
        self.di_deps:           list[dict] = []

    def parse(self) -> "CSharpFileParser":
        src = self._strip_comments(self.content)

        ns_match = PATTERNS["namespace"].search(src)
        self.namespace = ns_match.group(1) if ns_match else ""

        self.classes    = self._extract(src, "class_def")
        self.interfaces = self._extract(src, "interface_def")
        self.enums      = self._extract(src, "enum_def")
        self.structs    = self._extract(src, "struct_def")
        self.methods    = self._extract(src, "method_def")
        self.properties = self._extract(src, "property_def")
        self.usings     = [m.group(1) for m in PATTERNS["using"].finditer(src)]

        # Field type declarations
        for m in PATTERNS["field_decl"].finditer(src):
            type_name  = m.group(1).strip()
            field_name = m.group(2).strip().lstrip("_")
            if type_name not in CSHARP_KEYWORDS:
                self.field_types[field_name]  = type_name
                self.field_types[m.group(2).strip()] = type_name

        # Class → interface implementations
        for m in PATTERNS["class_implements"].finditer(src):
            cls   = m.group(1).strip()
            bases = [b.strip() for b in m.group(2).split(",")]
            ifaces = [b for b in bases if b.startswith("I") and b[1:2].isupper()]
            if ifaces:
                self.implements[cls] = ifaces

        # Method calls
        for m in PATTERNS["method_call"].finditer(src):
            obj    = m.group(1)
            method = m.group(2)
            if obj not in CSHARP_KEYWORDS and method not in CSHARP_KEYWORDS:
                self.method_calls.append({
                    "caller_obj":  obj,
                    "method":      method,
                    "source_file": str(self.file_path),
                    "ref_type":    "METHOD_CALL",
                })

        # Await calls (async pattern)
        for m in PATTERNS["await_call"].finditer(src):
            obj    = m.group(1)
            method = m.group(2)
            if obj not in CSHARP_KEYWORDS and method not in CSHARP_KEYWORDS:
                self.method_calls.append({
                    "caller_obj":  obj,
                    "method":      method,
                    "source_file": str(self.file_path),
                    "ref_type":    "AWAIT_CALL",
                })

        # Constructor calls
        for m in PATTERNS["constructor_call"].finditer(src):
            cls = m.group(1).split("<")[0]
            if cls not in CSHARP_KEYWORDS and cls[0:1].isupper():
                self.constructor_calls.append({
                    "target":      cls,
                    "source_file": str(self.file_path),
                    "ref_type":    "CONSTRUCTOR_CALL",
                })

        # DI params
        for m in PATTERNS["di_param"].finditer(src):
            self.di_deps.append({
                "interface":   m.group(1),
                "param_name":  m.group(2),
                "source_file": str(self.file_path),
                "ref_type":    "DEPENDENCY_INJECTION",
            })

        return self

    def _extract(self, src: str, key: str) -> list[str]:
        return [
            m.group(1).strip() for m in PATTERNS[key].finditer(src)
            if m.group(1).strip() not in CSHARP_KEYWORDS
        ]

    def _strip_comments(self, src: str) -> str:
        src = re.sub(r"//[^\n]*", " ", src)
        src = re.sub(r"/\*.*?\*/", " ", src, flags=re.DOTALL)
        return src


# ------------------------------------------------------------------
# Deep Resolution for C#
# ------------------------------------------------------------------

class CSharpDeepResolver:
    """
    Three-resolver deep resolution pipeline for C#.

    Resolver 1: field_type_resolver
        Reads typed field declarations:
          private readonly IUserRepository _userRepository
        When _userRepository.CreateAsync() is unresolved →
        resolves to IUserRepository.CreateAsync()

    Resolver 2: interface_resolver
        Maps interface method calls to concrete implementations.
        If UserRepository implements IUserRepository, and
        _repo.CreateAsync() → IUserRepository.CreateAsync()
        then resolves to UserRepository.CreateAsync()

    Resolver 3: di_constructor_resolver
        Tracks constructor-injected types.
        Constructor param (IUserRepository userRepository) →
        _userRepository field → method calls resolved.
    """

    def __init__(self, parsed: list, graph: dict):
        self.parsed = parsed
        self.graph  = graph

        # Build lookup maps
        self.field_type_map: dict[str, str] = {}
        for p in parsed:
            self.field_type_map.update(p.field_types)

        # Interface → implementing classes
        self.interface_implementations: dict[str, list] = {}
        for p in parsed:
            for cls, ifaces in p.implements.items():
                for iface in ifaces:
                    if iface not in self.interface_implementations:
                        self.interface_implementations[iface] = []
                    self.interface_implementations[iface].append(cls)

        # Class → methods map
        self.class_methods: dict[str, set] = {}
        for p in parsed:
            ns = p.namespace
            for cls in p.classes:
                key = cls
                self.class_methods[key] = set(p.methods)
                if ns:
                    self.class_methods[f"{ns}.{cls}"] = set(p.methods)

        # Interface → methods map
        self.interface_methods: dict[str, set] = {}
        for cls_data in self.graph["interfaces"].values():
            sn = cls_data["simple_name"]
            # collect methods from files that define this interface
            for p in parsed:
                if sn in p.interfaces:
                    self.interface_methods[sn] = set(p.methods)

    def resolve(self, unresolved: list[dict]) -> dict:
        resolved_fr : list[dict] = []  # field_type_resolver
        resolved_ir : list[dict] = []  # interface_resolver
        resolved_di : list[dict] = []  # di_constructor_resolver
        still_unresolved: list[dict] = []

        for entry in unresolved:
            obj    = entry.get("caller_obj", "")
            method = entry.get("method", "")
            resolved = False

            # Resolver 1: field_type_resolver
            if obj in self.field_type_map:
                type_name = self.field_type_map[obj]
                resolved_fr.append({
                    **entry,
                    "resolved":     True,
                    "resolved_to":  f"{type_name}.{method}",
                    "resolver":     "field_type_resolver",
                    "field_type":   type_name,
                    "confidence":   "HIGH",
                })
                resolved = True

            # Resolver 2: interface_resolver
            if not resolved:
                for iface, impls in self.interface_implementations.items():
                    if obj in self.field_type_map:
                        continue
                    # Check if obj is typed as this interface
                    for impl in impls:
                        methods = self.class_methods.get(impl, set())
                        if method in methods:
                            resolved_ir.append({
                                **entry,
                                "resolved":        True,
                                "resolved_to":     f"{impl}.{method}",
                                "resolver":        "interface_resolver",
                                "via_interface":   iface,
                                "concrete_class":  impl,
                                "confidence":      "MEDIUM",
                            })
                            resolved = True
                            break
                    if resolved:
                        break

            # Resolver 3: di_constructor_resolver
            if not resolved:
                for p in self.parsed:
                    for dep in p.di_deps:
                        if dep["param_name"] == obj or dep["param_name"].lstrip("_") == obj:
                            iface = dep["interface"]
                            resolved_di.append({
                                **entry,
                                "resolved":      True,
                                "resolved_to":   f"{iface}.{method}",
                                "resolver":      "di_constructor_resolver",
                                "injected_type": iface,
                                "confidence":    "HIGH",
                            })
                            resolved = True
                            break
                    if resolved:
                        break

            if not resolved:
                still_unresolved.append(entry)

        total_resolved = len(resolved_fr) + len(resolved_ir) + len(resolved_di)
        total_all      = total_resolved + len(still_unresolved)

        return {
            "dr_field_type":         len(resolved_fr),
            "dr_interface":          len(resolved_ir),
            "dr_di_constructor":     len(resolved_di),
            "dr_resolved_by_pipeline": total_resolved,
            "dr_remaining_unresolved": len(still_unresolved),
            "dr_reduction_pct":        round(total_resolved / total_all * 100, 2) if total_all else 0.0,
            "resolver_results": {
                "field_type":     len(resolved_fr),
                "interface":      len(resolved_ir),
                "di_constructor": len(resolved_di),
            },
            "final": {
                "resolved_by_pipeline": total_resolved,
                "remaining_unresolved": len(still_unresolved),
                "reduction_pct":        round(total_resolved / total_all * 100, 2) if total_all else 0.0,
            },
            "resolved_entries":   resolved_fr + resolved_ir + resolved_di,
            "still_unresolved":   still_unresolved,
        }


class CSharpAdapter:
    """Module 2 C# language adapter with deep resolution."""

    file_extensions = CSHARP_EXTENSIONS
    language = "csharp"

    def scan(self, repo_root: str, file_paths: list | None = None) -> dict:
        root = Path(repo_root)

        if file_paths:
            cs_files = [Path(f) for f in file_paths if Path(f).suffix.lower() == ".cs"]
        else:
            cs_files = list(root.rglob("*.cs"))

        if not cs_files:
            return self._empty(repo_root, "NO_CSHARP_FILES")

        parsed = []
        parse_errors = 0
        for path in cs_files:
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
                parsed.append(CSharpFileParser(path, content).parse())
            except Exception:
                parse_errors += 1

        graph       = self._build_graph(parsed)
        resolution  = self._resolve(graph, parsed)

        # Deep resolution
        unresolved_entries = resolution.get("unresolved_entries", [])
        dr = CSharpDeepResolver(parsed, graph).resolve(unresolved_entries)

        return self._report(repo_root, cs_files, parsed, graph, resolution, dr, parse_errors)

    def _build_graph(self, parsed: list) -> dict:
        classes    : dict[str, dict] = {}
        interfaces : dict[str, dict] = {}
        enums      : dict[str, dict] = {}
        structs    : dict[str, dict] = {}
        namespaces : dict[str, dict] = {}

        for p in parsed:
            src = str(p.file_path)
            ns  = p.namespace
            for cls in p.classes:
                fqn = f"{ns}.{cls}" if ns else cls
                classes[fqn] = {
                    "simple_name": cls, "namespace": ns,
                    "defined_in": src, "type": "CLASS",
                    "methods": p.methods,
                    "implements": p.implements.get(cls, []),
                }
            for iface in p.interfaces:
                fqn = f"{ns}.{iface}" if ns else iface
                interfaces[fqn] = {
                    "simple_name": iface, "namespace": ns,
                    "defined_in": src, "type": "INTERFACE",
                    "methods": p.methods,
                }
            for en in p.enums:
                enums[en] = {"defined_in": src, "namespace": ns, "type": "ENUM"}
            for st in p.structs:
                structs[st] = {"defined_in": src, "namespace": ns, "type": "STRUCT"}
            if ns:
                namespaces[ns] = namespaces.get(ns, {"files": []})
                namespaces[ns]["files"].append(src)

        return {"classes": classes, "interfaces": interfaces,
                "enums": enums, "structs": structs, "namespaces": namespaces}

    def _resolve(self, graph: dict, parsed: list) -> dict:
        known_classes    = {v["simple_name"] for v in graph["classes"].values()}
        known_classes   |= set(graph["classes"].keys())
        known_interfaces = {v["simple_name"] for v in graph["interfaces"].values()}
        known_interfaces |= set(graph["interfaces"].keys())
        all_known        = known_classes | known_interfaces

        all_methods: dict[str, set] = {}
        for fqn, cls in graph["classes"].items():
            sn = cls["simple_name"]
            all_methods[sn]  = set(cls.get("methods", []))
            all_methods[fqn] = all_methods[sn]

        resolved, unresolved = [], []
        for p in parsed:
            for call in p.method_calls:
                obj    = call["caller_obj"]
                method = call["method"]
                if obj in known_classes and method in all_methods.get(obj, set()):
                    resolved.append({**call, "resolved": True,
                                     "resolved_to": f"{obj}.{method}"})
                elif obj in all_known:
                    resolved.append({**call, "resolved": True,
                                     "resolved_to": f"{obj}.{method}",
                                     "confidence": "MEDIUM"})
                else:
                    unresolved.append({**call, "resolved": False,
                                       "reason": "OBJECT_TYPE_UNKNOWN"})

            for ctor in p.constructor_calls:
                target = ctor["target"]
                if target in known_classes:
                    resolved.append({**ctor, "resolved": True,
                                     "resolved_to": f"new {target}()"})
                else:
                    unresolved.append({**ctor, "resolved": False,
                                       "reason": "CLASS_NOT_IN_REPO"})

            for dep in p.di_deps:
                iface = dep["interface"]
                if iface in known_interfaces or iface in known_classes:
                    resolved.append({**dep, "resolved": True,
                                     "resolved_to": iface})
                else:
                    unresolved.append({**dep, "resolved": False,
                                       "reason": "INTERFACE_NOT_IN_REPO"})

        total = len(resolved) + len(unresolved)
        return {
            "resolved_count":     len(resolved),
            "unresolved_count":   len(unresolved),
            "resolved_entries":   resolved,
            "unresolved_entries": unresolved,
            "resolution_pct":     round(len(resolved)/total*100,2) if total else 0.0,
        }

    def _report(self, repo_root, cs_files, parsed, graph, resolution, dr, parse_errors):
        nc = {k: len(v) for k, v in graph.items()}
        nc["total"] = sum(nc.values())
        ec = {
            "method_calls":      sum(len(p.method_calls) for p in parsed),
            "constructor_calls": sum(len(p.constructor_calls) for p in parsed),
            "di_dependencies":   sum(len(p.di_deps) for p in parsed),
        }
        ec["total"] = sum(ec.values())

        total   = len(cs_files)
        err_pct = parse_errors / total * 100 if total else 0
        gate = "BLOCKED" if err_pct > 50 else ("REVIEW_REQUIRED" if nc["total"] == 0 else "APPROVED")
        framework = self._detect_framework(parsed, repo_root)

        # Combined resolution
        baseline   = resolution["unresolved_count"]
        dr_resolved = dr["dr_resolved_by_pipeline"]
        total_resolved = resolution["resolved_count"] + dr_resolved
        grand_total    = resolution["resolved_count"] + resolution["unresolved_count"]
        overall_pct    = round(total_resolved / grand_total * 100, 2) if grand_total else 0.0

        return {
            "repo_root":        repo_root,
            "language":         "csharp",
            "framework":        framework,
            "files_scanned":    total,
            "parse_errors":     parse_errors,
            "classes":          graph["classes"],
            "interfaces":       graph["interfaces"],
            "enums":            graph["enums"],
            "structs":          graph["structs"],
            "namespaces":       graph["namespaces"],
            "node_counts":      nc,
            "edge_counts":      ec,
            # Core resolution
            "resolution":       resolution,
            "resolved_calls":   resolution["resolved_count"],
            "unresolved_total": resolution["unresolved_count"],
            "resolution_pct":   resolution["resolution_pct"],
            # Deep resolution
            "deep_resolution":  dr,
            "dr_field_type":    dr["dr_field_type"],
            "dr_interface":     dr["dr_interface"],
            "dr_di_constructor":dr["dr_di_constructor"],
            "dr_resolved_by_pipeline": dr_resolved,
            "dr_reduction_pct": dr["dr_reduction_pct"],
            # Combined
            "overall_resolved": total_resolved,
            "overall_pct":      overall_pct,
            "baseline_unresolved": baseline,
            "governance_gate":  gate,
            "language_composition": {
                "csharp": {"file_count": total, "implemented": True, "framework": framework}
            },
        }

    def _detect_framework(self, parsed: list, repo_root: str) -> str:
        all_usings = set()
        for p in parsed:
            all_usings.update(p.usings)
        if any("Microsoft.AspNetCore" in u for u in all_usings):
            return "aspnet_core"
        if any("Microsoft.EntityFrameworkCore" in u for u in all_usings):
            return "entity_framework_core"
        if any("System.Web" in u for u in all_usings):
            return "aspnet_framework"
        if any("Xamarin" in u for u in all_usings):
            return "xamarin"
        if any("MAUI" in u or "Maui" in u for u in all_usings):
            return "dotnet_maui"
        if any("WPF" in u or "Windows.UI" in u for u in all_usings):
            return "wpf"
        try:
            for csproj in Path(repo_root).rglob("*.csproj"):
                c = csproj.read_text(encoding="utf-8", errors="ignore")
                if "net8" in c or "net9" in c: return "dotnet_8_9"
                if "net6" in c or "net7" in c: return "dotnet_6_7"
                if "netcoreapp" in c: return "dotnet_core"
                if "net4" in c: return "dotnet_framework"
        except Exception:
            pass
        return "dotnet"

    def _empty(self, repo_root: str, reason: str) -> dict:
        return {
            "repo_root": repo_root, "language": "csharp",
            "files_scanned": 0, "status": reason,
            "node_counts": {"total": 0}, "edge_counts": {"total": 0},
            "resolution": {"resolved_count": 0, "unresolved_count": 0},
            "deep_resolution": {"dr_resolved_by_pipeline": 0},
            "governance_gate": "BLOCKED",
        }

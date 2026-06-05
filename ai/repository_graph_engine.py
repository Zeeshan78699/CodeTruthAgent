"""
CodeTruth Agent V2
Repository Graph Engine

Safe deterministic repository graph builder.
"""

from __future__ import annotations

import ast
import json
import warnings
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Set


@dataclass
class FunctionNode:
    name: str
    file_path: str
    line_number: int
    calls: List[str]
    method_calls: List[str]


@dataclass
class ClassNode:
    name: str
    file_path: str
    line_number: int
    bases: List[str]
    methods: List[str]


@dataclass
class FileNode:
    file_path: str
    imports: List[str]
    from_imports: List[str]
    functions: List[FunctionNode]
    classes: List[ClassNode]
    top_level_calls: List[str]


@dataclass
class RepositoryGraph:
    root_path: str
    files: Dict[str, FileNode]
    dependency_map: Dict[str, List[str]]
    function_index: Dict[str, List[str]]
    class_index: Dict[str, List[str]]
    unresolved_calls: Dict[str, List[str]]


class RepositoryGraphEngine:
    def __init__(self, repo_root: str, ignore_dirs: Optional[List[str]] = None) -> None:
        self.repo_root = Path(repo_root).resolve()

        self.ignore_dirs: Set[str] = set(ignore_dirs or [
            ".venv",
            "venv",
            "__pycache__",
            ".git",
            ".pytest_cache",
            "backups",
            "archive",
            "logs",
            "reports",
         #   "models",
            "real_world",
            "site-packages",
            "vendor",
            "external",
        ])

        self.ignored_calls: Set[str] = {
            "print", "len", "range", "str", "int", "float", "bool",
            "list", "dict", "set", "tuple", "open", "sum", "min", "max",
            "sorted", "enumerate", "zip", "isinstance", "hasattr",
            "getattr", "setattr", "super", "any", "all", "next",
            "round", "type", "ValueError", "Exception",

            "append", "extend", "insert", "remove", "pop", "clear",
            "split", "strip", "lower", "upper", "replace", "join",
            "items", "keys", "values", "get", "read", "write",
            "readlines", "writelines", "startswith", "endswith",

            "json.dump", "json.load",
            "os.path.exists", "os.path.join", "os.walk",
            "os.makedirs", "os.remove", "os.listdir",
        }

    def build_graph(self) -> RepositoryGraph:
        py_files = self._find_python_files()
        files: Dict[str, FileNode] = {}

        for file_path in py_files:
            node = self._analyze_file(file_path)
            if node:
                files[node.file_path] = node

        function_index = self._build_function_index(files)
        class_index = self._build_class_index(files)
        dependency_map = self._build_dependency_map(files)
        unresolved_calls = self._find_unresolved_calls(files, function_index)

        return RepositoryGraph(
            root_path=str(self.repo_root),
            files=files,
            dependency_map=dependency_map,
            function_index=function_index,
            class_index=class_index,
            unresolved_calls=unresolved_calls,
        )

    def export_graph_json(self, output_path: str) -> None:
        graph = self.build_graph()
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        with output.open("w", encoding="utf-8") as f:
            json.dump(asdict(graph), f, indent=4)

    def print_summary(self) -> None:
        graph = self.build_graph()

        print("=" * 70)
        print("CODETRUTH V2 - REPOSITORY GRAPH SUMMARY")
        print("=" * 70)
        print(f"Repository: {graph.root_path}")
        print(f"Python files scanned: {len(graph.files)}")
        print(f"Functions found: {sum(len(f.functions) for f in graph.files.values())}")
        print(f"Classes found: {sum(len(f.classes) for f in graph.files.values())}")
        print("=" * 70)

        for file_path, file_node in graph.files.items():
            print(f"\nFILE: {file_path}")

            if file_node.imports:
                print(f"  Imports: {file_node.imports}")

            if file_node.from_imports:
                print(f"  From Imports: {file_node.from_imports}")

            if file_node.classes:
                print("  Classes:")
                for cls in file_node.classes:
                    print(f"    - {cls.name} | bases={cls.bases} | methods={cls.methods}")

            if file_node.functions:
                print("  Functions:")
                for fn in file_node.functions:
                    print(f"    - {fn.name}")
                    if fn.calls:
                        print(f"      calls={fn.calls}")
                    if fn.method_calls:
                        print(f"      method_calls={fn.method_calls}")

            if file_node.top_level_calls:
                print(f"  Top-level calls: {file_node.top_level_calls}")

        print("\n" + "=" * 70)
        print("DEPENDENCY MAP")
        print("=" * 70)

        for file_path, deps in graph.dependency_map.items():
            print(f"{file_path} -> {deps}")

        print("\n" + "=" * 70)
        print("UNRESOLVED CALLS")
        print("=" * 70)

        for file_path, calls in graph.unresolved_calls.items():
            if calls:
                print(f"{file_path} -> {calls}")

    def _find_python_files(self) -> List[Path]:
        files: List[Path] = []

        for path in self.repo_root.rglob("*.py"):
            if not self._should_ignore(path):
                files.append(path)

        return files

    def _should_ignore(self, path: Path) -> bool:
        return any(part in self.ignore_dirs for part in path.parts)

    def _analyze_file(self, file_path: Path) -> Optional[FileNode]:
        try:
            source = file_path.read_text(
                encoding="utf-8", 
                errors="ignore")
            with warnings.catch_warnings(record=True) as warning_list:

                warnings.simplefilter("always")

                tree = ast.parse(source)

            for warning in warning_list:

                if "invalid escape sequence" in str(warning.message):

                    print("\n" + "=" * 60)
                    print("WARNING FILE FOUND")
                    print("=" * 60)
                    print(file_path)
                    print(warning.message)
                    print("=" * 60)
        except Exception:
            return None

        relative = self._relative(file_path)

        imports: List[str] = []
        from_imports: List[str] = []
        functions: List[FunctionNode] = []
        classes: List[ClassNode] = []
        top_level_calls: List[str] = []

        for node in tree.body:
            if isinstance(node, ast.Import):
                imports.extend(self._extract_imports(node))

            elif isinstance(node, ast.ImportFrom):
                from_imports.extend(self._extract_from_imports(node))

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(self._extract_function(node, relative))

            elif isinstance(node, ast.ClassDef):
                classes.append(self._extract_class(node, relative))
                # Also walk into method bodies so dangerous-API and
                # global-mutation checks see method-level calls. Each
                # method is represented as a FunctionNode named
                # "ClassName.method_name".
                functions.extend(self._extract_class_methods(node, relative))

            else:
                top_level_calls.extend(self._extract_calls_from_node(node))

        return FileNode(
            file_path=relative,
            imports=sorted(set(imports)),
            from_imports=sorted(set(from_imports)),
            functions=functions,
            classes=classes,
            top_level_calls=sorted(set(top_level_calls)),
        )

    def _extract_imports(self, node: ast.Import) -> List[str]:
        return [alias.name for alias in node.names]

    def _extract_from_imports(self, node: ast.ImportFrom) -> List[str]:
        module = node.module or ""
        return [f"{module}.{alias.name}" if module else alias.name for alias in node.names]

    def _extract_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef, file_path: str) -> FunctionNode:
        calls: List[str] = []
        method_calls: List[str] = []

        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                name = self._get_call_name(child)
                if name:
                    if "." in name:
                        method_calls.append(name)
                    else:
                        calls.append(name)

        return FunctionNode(
            name=node.name,
            file_path=file_path,
            line_number=getattr(node, "lineno", -1),
            calls=sorted(set(calls)),
            method_calls=sorted(set(method_calls)),
        )

    def _extract_class(self, node: ast.ClassDef, file_path: str) -> ClassNode:
        """Build a ClassNode for this class.

        Method bodies are walked separately by _extract_class_methods so
        the dangerous-API and global-mutation checks see calls inside
        methods. This split preserves the original ClassNode shape (just
        method names) while exposing the method bodies through
        _extract_class_methods.
        """
        bases: List[str] = []
        methods: List[str] = []

        for base in node.bases:
            name = self._get_name(base)
            if name:
                bases.append(name)

        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(item.name)

        return ClassNode(
            name=node.name,
            file_path=file_path,
            line_number=getattr(node, "lineno", -1),
            bases=sorted(set(bases)),
            methods=sorted(set(methods)),
        )

    def _extract_class_methods(
        self, node: ast.ClassDef, file_path: str
    ) -> List[FunctionNode]:
        """Walk class body and return a FunctionNode for each method.

        Each returned FunctionNode has its name prefixed with the class
        name (e.g. 'Command.handle') so it does not collide with a same-
        named top-level function elsewhere in the repo. The line_number
        and the extracted calls/method_calls come from the method body
        itself, so dangerous-API detection works inside methods exactly
        as it does for top-level functions.

        Returns an empty list for classes with no methods. Nested classes
        are not walked here (kept as a deliberate scope decision).
        """
        method_nodes: List[FunctionNode] = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                fn = self._extract_function(item, file_path)
                # Prefix with class name to disambiguate.
                qualified_name = f"{node.name}.{fn.name}"
                method_nodes.append(FunctionNode(
                    name=qualified_name,
                    file_path=fn.file_path,
                    line_number=fn.line_number,
                    calls=fn.calls,
                    method_calls=fn.method_calls,
                ))
        return method_nodes

    def _extract_calls_from_node(self, node: ast.AST) -> List[str]:
        calls: List[str] = []

        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                name = self._get_call_name(child)
                if name:
                    calls.append(name)

        return sorted(set(calls))

    def _get_call_name(self, node: ast.Call) -> Optional[str]:
        return self._get_name(node.func)

    def _get_name(self, node: ast.AST) -> Optional[str]:
        if isinstance(node, ast.Name):
            return node.id

        if isinstance(node, ast.Attribute):
            parent = self._get_name(node.value)
            return f"{parent}.{node.attr}" if parent else node.attr

        if isinstance(node, ast.Call):
            return self._get_call_name(node)

        if isinstance(node, ast.Subscript):
            return self._get_name(node.value)

        return None

    def _build_function_index(self, files: Dict[str, FileNode]) -> Dict[str, List[str]]:
        index: Dict[str, List[str]] = {}

        for file_path, file_node in files.items():
            for fn in file_node.functions:
                index.setdefault(fn.name, []).append(file_path)

            for cls in file_node.classes:
                for method in cls.methods:
                    index.setdefault(method, []).append(file_path)
                    index.setdefault(f"{cls.name}.{method}", []).append(file_path)

        return index

    def _build_class_index(self, files: Dict[str, FileNode]) -> Dict[str, List[str]]:
        index: Dict[str, List[str]] = {}

        for file_path, file_node in files.items():
            for cls in file_node.classes:
                index.setdefault(cls.name, []).append(file_path)

        return index

    def _build_dependency_map(self, files: Dict[str, FileNode]) -> Dict[str, List[str]]:
        dependency_map: Dict[str, List[str]] = {}
        known_files = list(files.keys())

        for file_path, file_node in files.items():
            deps: Set[str] = set()

            for import_name in file_node.imports + file_node.from_imports:
                matched = self._match_import_to_file(import_name, known_files)
                if matched and matched != file_path:
                    deps.add(matched)

            dependency_map[file_path] = sorted(deps)

        return dependency_map

    def _find_unresolved_calls(
        self,
        files: Dict[str, FileNode],
        function_index: Dict[str, List[str]],
    ) -> Dict[str, List[str]]:
        unresolved: Dict[str, List[str]] = {}

        for file_path, file_node in files.items():
            missing: Set[str] = set()

            for fn in file_node.functions:
                for call in fn.calls + fn.method_calls:
                    base = call.split(".")[-1]

                    if call in self.ignored_calls or base in self.ignored_calls:
                        continue

                    if call not in function_index and base not in function_index:
                        missing.add(call)

            unresolved[file_path] = sorted(missing)

        return unresolved

    def _match_import_to_file(self, import_name: str, known_files: List[str]) -> Optional[str]:
        """
        Improved resolver.

        Supports:
        ai.embedding_similarity.EmbeddingSemanticEngine
        ai.embedding_similarity
        memory.memory_store_v2.MemoryStoreV2
        validation.rollback_manager.RollbackManager
        reporting.report_generator.ReportGenerator
        core.memory_store.load_memory
        """

        clean_import = import_name.strip()
        if not clean_import:
            return None

        normalized_files = {
            file_path.replace("\\", "/"): file_path
            for file_path in known_files
        }

        parts = clean_import.split(".")

        candidates: List[str] = []

        for i in range(len(parts), 0, -1):
            module_path = "/".join(parts[:i]) + ".py"
            candidates.append(module_path)

        for candidate in candidates:
            for normalized, original in normalized_files.items():
                if normalized.endswith(candidate):
                    return original

        if len(parts) >= 2:
            module_candidate = "/".join(parts[:-1]) + ".py"
            for normalized, original in normalized_files.items():
                if normalized.endswith(module_candidate):
                    return original

        short_candidate = parts[-1] + ".py"
        for normalized, original in normalized_files.items():
            if normalized.endswith(short_candidate):
                return original

        return None

    def _relative(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.repo_root))
        except ValueError:
            return str(path)


if __name__ == "__main__":
    repo_path = Path.cwd()

    engine = RepositoryGraphEngine(str(repo_path))
    engine.print_summary()

    output_file = repo_path / "reports" / "repository_graph.json"
    engine.export_graph_json(str(output_file))

    print("\nRepository graph exported to:")
    print(output_file)
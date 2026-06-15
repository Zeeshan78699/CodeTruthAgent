"""
python_adapter.py
The only fully IMPLEMENTED language adapter. Wraps the existing,
frozen Stage A / Stage B engine (function_graph.py, class_graph.py,
module_graph.py, import_graph.py, dependency_graph.py, call_graph.py,
topology.py) without modifying any of it.
"""

from .base_adapter import LanguageAdapter
from .. import graph_engine


class PythonAdapter(LanguageAdapter):
    language_name = "python"
    file_extensions = {".py"}

    def is_implemented(self) -> bool:
        return True

    def scan(self, repo_root: str, file_paths: list) -> dict:
        # The existing engine already discovers and scans all .py files
        # under repo_root itself (find_python_files). file_paths is provided
        # for interface consistency with other adapters but is not needed
        # here - delegate to the proven, frozen implementation as-is.
        return graph_engine.build_repository_graph(repo_root)

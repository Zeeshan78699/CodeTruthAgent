"""
registry.py
Central registry of language adapters - the single place to add support
for a new language. To add a language:
    1. Create <language>_adapter.py implementing LanguageAdapter
    2. Add an instance to ADAPTERS below

graph_engine.py and any future multi-language entry point use
classify_files() to group a repo's files by language WITHOUT needing to
know which languages are implemented vs stubs.
"""

import os

from .python_adapter import PythonAdapter
from .java_adapter import JavaAdapter
from .javascript_adapter import JavaScriptAdapter
from .go_adapter import GoAdapter
from .rust_adapter import RustAdapter
from .c_cpp_adapter import CCppAdapter


#: Ordered list of registered adapters. Order matters only if extensions
#: overlap (first match wins) - currently no overlaps exist.
ADAPTERS = [
    PythonAdapter(),
    JavaAdapter(),
    JavaScriptAdapter(),
    GoAdapter(),
    RustAdapter(),
    CCppAdapter(),
]


def _extension_map():
    """{extension: adapter} built once from ADAPTERS."""
    mapping = {}
    for adapter in ADAPTERS:
        for ext in adapter.file_extensions:
            mapping[ext] = adapter
    return mapping


_EXTENSION_MAP = _extension_map()


def adapter_for_extension(ext: str):
    """Returns the registered adapter for a file extension, or None."""
    return _EXTENSION_MAP.get(ext.lower())


def classify_files(repo_root: str, ignore_dirs=None):
    """
    Walks repo_root and groups files by language adapter.

    Returns:
        {
          "python":     {"adapter": <PythonAdapter>, "files": [...]},
          "java":       {"adapter": <JavaAdapter>, "files": [...]},
          ...
          "_unclassified": {"extensions": {".md": 12, ".json": 3, ...}}
        }

    "_unclassified" mirrors Module 1's "detected_file_types" tier - files
    whose extension has no registered adapter (docs, configs, data, etc.)
    are counted but not attributed to any language.
    """
    ignore_dirs = ignore_dirs or {".git", "__pycache__", "node_modules", ".venv", "venv"}

    by_language = {a.language_name: {"adapter": a, "files": []} for a in ADAPTERS}
    unclassified_exts = {}

    for dirpath, dirnames, filenames in os.walk(repo_root):
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs]
        for fname in filenames:
            ext = os.path.splitext(fname)[1].lower()
            adapter = adapter_for_extension(ext)
            full_path = os.path.join(dirpath, fname)
            if adapter:
                by_language[adapter.language_name]["files"].append(full_path)
            else:
                unclassified_exts[ext] = unclassified_exts.get(ext, 0) + 1

    by_language["_unclassified"] = {"extensions": unclassified_exts}
    return by_language

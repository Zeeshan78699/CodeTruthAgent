"""
module_graph.py
V3-006: Package & directory level mapping

Builds a tree of modules/packages based on file paths, independent of
import relationships (that is import_graph.py's job).
"""

import os


def module_name_from_path(root, filepath):
    """Convert a file path into a dotted module name relative to root."""
    rel = os.path.relpath(filepath, root)
    parts = rel.replace(".py", "").split(os.sep)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def build_module_graph(root, py_files):
    """
    Returns a dict mapping each module to its parent package and children.

    {
        "module.name": {
            "path": "/abs/path/to/file.py",
            "parent": "module" or None,
            "is_package": bool
        }
    }
    """
    graph = {}

    for filepath in py_files:
        mod_name = module_name_from_path(root, filepath)
        if mod_name == "":
            continue

        parts = mod_name.split(".")
        parent = ".".join(parts[:-1]) if len(parts) > 1 else None
        is_package = os.path.basename(filepath) == "__init__.py"

        graph[mod_name] = {
            "path": filepath,
            "parent": parent,
            "is_package": is_package,
        }

    return graph

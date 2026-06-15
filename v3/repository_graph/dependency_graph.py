"""
dependency_graph.py
V3-008: Third-party package tree graph

Consumes the "external" half of import_graph.py's split output, plus
(optionally) requirements.txt / pyproject.toml for version info.
This module does NOT re-parse source; it aggregates what import_graph found.
"""

import os
import re


def build_dependency_graph(external_imports_by_module):
    """
    external_imports_by_module: {module_name: [raw_import_entry, ...]}
    (the "external" list returned by import_graph.split_internal_external)

    Returns:
    {
        "<package_root>": {
            "used_by": ["module.a", "module.b", ...],
            "import_count": N
        },
        ...
    }
    """
    deps = {}
    for module_name, entries in external_imports_by_module.items():
        for entry in entries:
            pkg_root = entry["imports"].split(".")[0]
            if pkg_root not in deps:
                deps[pkg_root] = {"used_by": [], "import_count": 0}
            if module_name not in deps[pkg_root]["used_by"]:
                deps[pkg_root]["used_by"].append(module_name)
            deps[pkg_root]["import_count"] += 1

    return deps


def load_declared_dependencies(repo_root):
    """
    Best-effort read of requirements.txt for declared (vs. actually-imported)
    dependencies. Returns a dict {package_name: version_spec_or_None}.
    Missing file -> empty dict (not an error).
    """
    req_path = os.path.join(repo_root, "requirements.txt")
    declared = {}
    if not os.path.exists(req_path):
        return declared

    with open(req_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            match = re.match(r"^([A-Za-z0-9_\-\.]+)\s*([=<>!~]+.*)?$", line)
            if match:
                name = match.group(1)
                version = match.group(2)
                declared[name] = version

    return declared

"""
package_root.py
D-008 fix: per-repo package-root detection.

Non-frozen wrapper component - lives alongside call_graph.py/module_graph.py/
graph_engine.py but is a NEW file. Detects repositories whose importable
package root is a SUBDIRECTORY of the cloned repo (e.g. ccxt/python/ccxt/,
odoo/odoo/) rather than the repo root itself, and computes the correct
"effective root" to pass into graph_engine.build_repository_graph() so
module names match the absolute import paths actually used in the code.

Truth Boundary: if detection is ambiguous (no dominant candidate, or no
matching directory found), this returns repo_root UNCHANGED. It never
guesses - for the repos that don't have this problem, the result is
identical to calling build_repository_graph(repo_root) directly.
"""

import ast
import os

from .graph_engine import find_python_files

# A candidate's absolute-import root must account for at least this
# fraction of all absolute-import-root occurrences repo-wide before it's
# trusted enough to override repo_root. Conservative by design - "no
# change" is preferred over a wrong guess.
DOMINANCE_THRESHOLD = 0.5

# Same skip-set as graph_engine.find_python_files, kept identical so
# detection scans exactly the same file population the engine itself
# will scan.
_SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv"}


def _collect_absolute_import_roots(py_files):
    """
    Parses every file for import statements and returns a
    {root_name: count} frequency table of ABSOLUTE (non-relative) import
    roots only. Files that fail to parse are silently skipped here -
    graph_engine's own Stage A is the one that logs the real
    "parse_error" entry; this is a best-effort signal pass only.
    """
    counts = {}
    for filepath in py_files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source, filename=filepath)
        except (SyntaxError, UnicodeDecodeError, OSError):
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    counts[root] = counts.get(root, 0) + 1
            elif isinstance(node, ast.ImportFrom):
                if node.level and node.level > 0:
                    continue  # relative import - not relevant to D-008
                if node.module:
                    root = node.module.split(".")[0]
                    counts[root] = counts.get(root, 0) + 1
    return counts


def _find_package_dir(repo_root, package_name):
    """
    Searches repo_root's tree for the SHALLOWEST directory named
    `package_name` that is itself an importable package (contains
    __init__.py). Returns the absolute path, or None.
    """
    best = None
    best_depth = None
    for dirpath, dirnames, filenames in os.walk(repo_root):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        if os.path.basename(dirpath) == package_name and "__init__.py" in filenames:
            depth = dirpath.count(os.sep)
            if best is None or depth < best_depth:
                best = dirpath
                best_depth = depth
    return best


def detect_package_root_and_counts(repo_root):
    """
    Same detection as detect_package_root() below, but also returns
    the computed root_counts table. Exists so callers that need both
    D-008's detection AND the raw import-root counts (e.g.
    subtree_naming.py's src-layout check) can get both from a single
    pass over the repo's files, instead of parsing every file twice -
    confirmed as a real cost on a 69-repo corpus scan (one repo,
    transformers, took 94.9s largely due to this exact duplication).

    detect_package_root() below is now a thin wrapper around this -
    its behavior is completely unchanged, this is a pure refactor.
    """
    py_files = find_python_files(repo_root)
    if not py_files:
        return repo_root, {}

    root_counts = _collect_absolute_import_roots(py_files)
    if not root_counts:
        return repo_root, {}

    total = sum(root_counts.values())
    top_name, top_count = max(root_counts.items(), key=lambda kv: kv[1])

    if top_count / total < DOMINANCE_THRESHOLD:
        return repo_root, root_counts  # no dominant candidate - honest "no change"

    package_dir = _find_package_dir(repo_root, top_name)
    if package_dir is None:
        return repo_root, root_counts  # candidate name doesn't exist as a real package

    effective_root = os.path.dirname(package_dir)

    if os.path.normpath(effective_root) == os.path.normpath(repo_root):
        return repo_root, root_counts  # already the common case - package sits
                                        # directly under repo_root, nothing to correct

    return effective_root, root_counts


def detect_package_root(repo_root):
    """
    Returns the effective root to use for module-name / file-discovery
    purposes. Falls back to repo_root UNCHANGED whenever detection isn't
    confidently resolvable - never guesses.
    """
    effective_root, _ = detect_package_root_and_counts(repo_root)
    return effective_root
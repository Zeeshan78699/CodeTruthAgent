r"""
docs_inventory.py
CodeTruth Agent V3 — D3-015 Documentation Auditor, Phase 1 / Capability 1.

Scans a repository for documentation artifacts and returns OBSERVED facts about
WHAT DOCUMENTATION EXISTS. It does not read docs as truth, does not interpret
them, does not let them influence any structural classification. It answers only:
"what documentation is present, and how much of it."

AUTHORITY RULE (D3-015): code is the arbiter; docs are claims. This module is the
inventory step — it records the existence and shape of the claim artifacts. It
never assigns a domain, application_type, or architecture value.

Output maps directly onto the schema's `documentation` section:
    readme_present, readme_sections, changelog_present, adrs, api_docs
    (docstring_coverage is Capability 2 — needs the call graph — not here)
    (docs_code_drift is Capability 2 — the drift engine — not here)

Every field is OBSERVED with a path citation, or UNKNOWN:NO_EVIDENCE if absent.
"""
from __future__ import annotations
import os
import re


# --------------------------------------------------------------------------- #
# tier constructors (kept local so this module has no import coupling)
# --------------------------------------------------------------------------- #
def _OBSERVED(value, path, excerpt):
    return {"tier": "OBSERVED", "value": value,
            "evidence": [{"path": path, "excerpt": excerpt, "sha256": "0" * 64}]}


def _UNKNOWN(reason, notes=None):
    f = {"tier": "UNKNOWN", "reason": reason}
    if notes:
        f["notes"] = notes
    return f


NOEV = "NO_EVIDENCE_FOUND"

# Filenames we recognize, case-insensitive, first match wins.
README_NAMES = ("readme.md", "readme.rst", "readme.txt", "readme")
CHANGELOG_NAMES = ("changelog.md", "changelog.rst", "changelog.txt", "changelog",
                   "changes.md", "changes.rst", "history.md", "news.md")
# Directories that indicate a documentation site / API docs.
DOC_DIR_NAMES = ("docs", "doc")
API_DOC_MARKERS = ("conf.py", "mkdocs.yml", "mkdocs.yaml", "index.rst", "index.md")
# ADR conventions.
ADR_DIR_HINTS = (os.path.join("docs", "adr"), os.path.join("doc", "adr"),
                 os.path.join("docs", "decisions"), "adr")

# Directories never treated as source of docs (noise).
PRUNE = {".git", "__pycache__", "node_modules", ".venv", "venv", ".tox",
         "build", "dist", ".mypy_cache", ".pytest_cache"}


def _find_first(repo_root: str, names) -> str | None:
    """Return the repo-root-relative path of the first top-level file whose name
    matches (case-insensitive), else None. Only checks the repo root — a README
    is a root artifact; nested readmes are not the project README."""
    try:
        entries = os.listdir(repo_root)
    except OSError:
        return None
    lower = {e.lower(): e for e in entries}
    for want in names:
        if want in lower:
            return lower[want]
    return None


def _count_markdown_sections(path: str) -> int | None:
    """Count headings in a markdown/rst README. Markdown: lines starting with #.
    rst: lines underlined with ===/---. Returns None if unreadable."""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
    except OSError:
        return None
    if path.lower().endswith(".rst"):
        # rst section = a text line immediately followed by a run of ===/---/~~~
        count = 0
        for i in range(len(lines) - 1):
            under = lines[i + 1].strip()
            if under and len(set(under)) == 1 and under[0] in "=-~^\"'#*+":
                if lines[i].strip():
                    count += 1
        return count
    # markdown / plain: count ATX headings
    return sum(1 for ln in lines if re.match(r"^#{1,6}\s+\S", ln))


def _dir_exists(repo_root: str, rel: str) -> bool:
    return os.path.isdir(os.path.join(repo_root, rel))


def _has_api_docs(repo_root: str) -> tuple[bool, str]:
    """True if a docs/ or doc/ dir exists AND contains a recognizable doc-site
    marker (sphinx conf.py, mkdocs.yml, an index). Returns (bool, evidence)."""
    for d in DOC_DIR_NAMES:
        ddir = os.path.join(repo_root, d)
        if not os.path.isdir(ddir):
            continue
        for root, dirs, files in os.walk(ddir):
            dirs[:] = [x for x in dirs if x not in PRUNE]
            for fn in files:
                if fn.lower() in API_DOC_MARKERS:
                    rel = os.path.relpath(os.path.join(root, fn), repo_root)
                    return True, rel
            # don't descend more than 2 levels for this check
            if root.count(os.sep) - ddir.count(os.sep) >= 2:
                dirs[:] = []
    return False, ""


def _find_adrs(repo_root: str) -> tuple[int, str]:
    """Count Architecture Decision Records. Returns (count, evidence_dir)."""
    for hint in ADR_DIR_HINTS:
        adir = os.path.join(repo_root, hint)
        if os.path.isdir(adir):
            n = sum(1 for f in os.listdir(adir)
                    if f.lower().endswith((".md", ".rst", ".txt")))
            if n:
                return n, hint
    return 0, ""


def inventory(repo_root: str) -> dict:
    """Return the `documentation` section (partial — Capability 1 fields only).

    Fields NOT set here (docstring_coverage, docs_code_drift) are left for
    Capability 2 and must be merged in by the caller; this function does not
    fabricate them.
    """
    out = {}

    # ---- readme_present + readme_sections -------------------------------- #
    readme = _find_first(repo_root, README_NAMES)
    if readme:
        out["readme_present"] = _OBSERVED(True, readme, "README file at repo root")
        sections = _count_markdown_sections(os.path.join(repo_root, readme))
        if sections is not None:
            out["readme_sections"] = _OBSERVED(
                sections, readme, f"{sections} headings counted")
        else:
            out["readme_sections"] = _UNKNOWN(NOEV, "README present but unreadable")
    else:
        out["readme_present"] = _OBSERVED(False, ".", "no README.* at repo root")
        out["readme_sections"] = _UNKNOWN(NOEV, "no README to count sections in")

    # ---- changelog_present ----------------------------------------------- #
    changelog = _find_first(repo_root, CHANGELOG_NAMES)
    if changelog:
        out["changelog_present"] = _OBSERVED(True, changelog, "CHANGELOG at repo root")
    else:
        out["changelog_present"] = _OBSERVED(False, ".", "no CHANGELOG.* at repo root")

    # ---- adrs ------------------------------------------------------------ #
    n_adr, adr_dir = _find_adrs(repo_root)
    if adr_dir:
        out["adrs"] = _OBSERVED(n_adr, adr_dir, f"{n_adr} ADR files")
    else:
        out["adrs"] = _OBSERVED(0, ".", "no ADR directory found")

    # ---- api_docs -------------------------------------------------------- #
    has_api, api_ev = _has_api_docs(repo_root)
    if has_api:
        out["api_docs"] = _OBSERVED(True, api_ev, "doc-site marker present")
    else:
        out["api_docs"] = _OBSERVED(False, ".", "no docs/ site marker found")

    return out


if __name__ == "__main__":
    import sys, json
    print(json.dumps(inventory(sys.argv[1]), indent=2))

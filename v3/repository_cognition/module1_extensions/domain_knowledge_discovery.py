"""
========================================================================
domain_knowledge_discovery.py
CodeTruth Agent V3 — Module 1 Extension

CAPABILITIES:
    - README Discovery
    - Business Rule Document Discovery
    - Architecture Document Discovery
    - Functional Specification Discovery
    - Knowledge Index Creation

SCOPE CORRECTION (critical):
    This module is a POINTER, not an EXTRACTOR.
    It discovers THAT documents exist and WHERE they are.
    It does NOT read, parse, or interpret document contents.
    Rule extraction routes through V3-108 (governed interpretation).

    Output: "Finance_Policy.pdf found at path X"
    NOT:    "the policy says approval threshold is $10,000"

TRUTH BOUNDARY:
    If no documents found, index is empty — not fabricated.
========================================================================
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path


# ---------------------------------------------------------------------------
# Document pattern matching
# ---------------------------------------------------------------------------

_README_PATTERNS = {
    "README.md", "README.rst", "README.txt", "README",
    "readme.md", "readme.txt",
}

_BUSINESS_RULE_KEYWORDS = [
    "policy", "rule", "regulation", "compliance", "standard",
    "procedure", "guideline", "workflow", "process", "approval",
    "doa", "matrix", "charter", "mandate",
]

_ARCHITECTURE_KEYWORDS = [
    "architecture", "design", "adr", "decision", "blueprint",
    "system", "component", "diagram", "overview",
]

_SPEC_KEYWORDS = [
    "spec", "specification", "requirement", "functional",
    "feature", "usecase", "use_case", "story", "backlog",
]

_DOC_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".xlsx", ".xls", ".md",
    ".rst", ".txt", ".html", ".pptx",
}


@dataclass
class DocumentPointer:
    doc_type:    str       # "README" | "BUSINESS_RULE" | "ARCHITECTURE" | "SPEC" | "OTHER"
    path:        str       # relative path from repo root
    filename:    str
    extension:   str


@dataclass
class KnowledgeIndex:
    readme_files:        list[DocumentPointer]
    business_rule_docs:  list[DocumentPointer]
    architecture_docs:   list[DocumentPointer]
    functional_specs:    list[DocumentPointer]
    total_docs_found:    int
    notes:               list[str]


class DomainKnowledgeDiscovery:
    """
    Discovers documentation files by name and extension only.
    Does NOT read file contents. Does NOT extract rules or interpret meaning.
    """

    MAX_DEPTH = 4

    def discover(self, repo_path: str) -> KnowledgeIndex:
        root = Path(repo_path)
        readmes:    list[DocumentPointer] = []
        biz_rules:  list[DocumentPointer] = []
        arch_docs:  list[DocumentPointer] = []
        specs:      list[DocumentPointer] = []
        notes:      list[str] = []

        if not root.exists():
            return KnowledgeIndex(
                readme_files=[], business_rule_docs=[],
                architecture_docs=[], functional_specs=[],
                total_docs_found=0,
                notes=["Repository path does not exist"],
            )

        try:
            for item in root.rglob("*"):
                if not item.is_file():
                    continue
                depth = len(item.relative_to(root).parts)
                if depth > self.MAX_DEPTH:
                    continue
                if item.suffix.lower() not in _DOC_EXTENSIONS:
                    continue

                rel_path = str(item.relative_to(root))
                name_lower = item.name.lower()
                ext = item.suffix.lower()

                ptr = DocumentPointer(
                    doc_type="OTHER",
                    path=rel_path,
                    filename=item.name,
                    extension=ext,
                )

                # Classify by filename keywords — name only, not content
                if item.name in _README_PATTERNS:
                    ptr.doc_type = "README"
                    readmes.append(ptr)
                elif any(kw in name_lower for kw in _BUSINESS_RULE_KEYWORDS):
                    ptr.doc_type = "BUSINESS_RULE"
                    biz_rules.append(ptr)
                elif any(kw in name_lower for kw in _ARCHITECTURE_KEYWORDS):
                    ptr.doc_type = "ARCHITECTURE"
                    arch_docs.append(ptr)
                elif any(kw in name_lower for kw in _SPEC_KEYWORDS):
                    ptr.doc_type = "SPEC"
                    specs.append(ptr)

        except PermissionError as e:
            notes.append(f"Permission error: {e}")
        except Exception as e:
            notes.append(f"Discovery error: {e}")

        total = len(readmes) + len(biz_rules) + len(arch_docs) + len(specs)
        if total == 0:
            notes.append(
                "No documentation files found. "
                "Business rules and architecture must be discovered from code signals only."
            )

        notes.append(
            "SCOPE NOTE: This module reports document locations only. "
            "Content extraction and rule interpretation require V3-108 governance."
        )

        return KnowledgeIndex(
            readme_files=readmes,
            business_rule_docs=biz_rules,
            architecture_docs=arch_docs,
            functional_specs=specs,
            total_docs_found=total,
            notes=notes,
        )

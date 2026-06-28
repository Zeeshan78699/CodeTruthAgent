"""
========================================================================
evidence_traceability.py
CodeTruth Agent V3 — Module 1 Extension

CAPABILITIES:
    - Document -> Code Mapping
    - Code -> Test Mapping
    - Centralized Test Harness Detection

SCOPE CORRECTION:
    Requirement -> Code Mapping is Module 9's job (V3-106).
    This module traces document references and test structure only.

TRUTH BOUNDARY:
    A traceability link is only created when a document name is explicitly
    mentioned in source code.

    Centralized test harness detection is based only on physical files
    present in the repository. No inference is treated as truth.
========================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


_DOC_REFERENCE_PATTERN = re.compile(
    r"""['"]([^'"]*\.(?:pdf|docx|doc|xlsx|xls|md|rst|txt))['"]\s*"""
    r"""|#\s*(?:see|ref|reference|as per|per)\s+(.+\.(?:pdf|docx|doc|xlsx|xls|md|rst|txt))""",
    re.IGNORECASE,
)

CENTRALIZED_TEST_INDICATORS = (
    "test_all",
    "run_tests",
    "test_suite",
    "base_test",
    "integration_test",
    "integration_tests",
    "functional_test",
    "acceptance_test",
    "runner",
    "test_runner",
    "test_base",
    "base_tests",
)

# Coverage below this threshold triggers a search for harness evidence.
# If evidence found → CENTRALIZED_TEST_HARNESS_DETECTED
# If not found     → LOW_COVERAGE_DETECTED
# Never automatic — physical evidence is always required.
LOW_COVERAGE_THRESHOLD = 30.0

# Additional harness config file markers (evidence-based only)
HARNESS_CONFIG_MARKERS = (
    "pytest.ini",
    "tox.ini",
    "noxfile.py",
    "conftest.py",
    ".pytest.ini",
    "setup.cfg",    # may contain [tool:pytest]
    "pyproject.toml",  # may contain [tool.pytest]
)


@dataclass
class DocumentCodeLink:
    document_name: str
    source_file: str
    source_line: int
    reference_text: str


@dataclass
class CodeTestLink:
    source_file: str
    test_file: str
    link_type: str


@dataclass
class TraceabilityResult:
    document_code_links: list[DocumentCodeLink]
    code_test_links: list[CodeTestLink]
    untraced_source: list[str]
    total_doc_links: int
    total_test_links: int
    coverage_note: str
    notes: list[str]


class EvidenceTraceability:
    """
    Module 1 traceability extension.

    This module performs deterministic evidence collection only:

    1. Document -> Code references
       Finds explicit document names referenced in code comments or strings.

    2. Code -> Test mapping
       Finds direct test counterparts using naming convention.

    3. Centralized test harness detection
       If local file-pair coverage is 0%, checks for physical test harness
       files that indicate centralized testing.

    It does NOT:
        - Interpret requirements
        - Prove business rule compliance
        - Perform Module 3 reasoning
        - Perform Module 9 requirement mapping
    """

    MAX_FILES = 300

    SOURCE_EXTENSIONS = (
        ".py",
        ".js",
        ".ts",
        ".tsx",
        ".jsx",
        ".java",
        ".go",
        ".cs",
        ".php",
    )

    TEST_DIR_MARKERS = (
        "test",
        "tests",
        "__tests__",
        "spec",
        "specs",
    )

    def trace(self, repo_path: str) -> TraceabilityResult:
        root = Path(repo_path)

        doc_links: list[DocumentCodeLink] = []
        code_test_links: list[CodeTestLink] = []
        source_files: list[str] = []
        untraced: list[str] = []
        notes: list[str] = []

        if not root.exists():
            return TraceabilityResult(
                document_code_links=[],
                code_test_links=[],
                untraced_source=[],
                total_doc_links=0,
                total_test_links=0,
                coverage_note="Repository path does not exist",
                notes=["Repository path does not exist."],
            )

        all_source_files = self._collect_source_files(root)
        scan_files = all_source_files[: self.MAX_FILES]

        test_files = self._collect_test_files(root)

        for source_file in scan_files:
            rel = str(source_file.relative_to(root))

            if self._is_test_file(source_file):
                continue

            source_files.append(rel)

            matched_test = self._find_test_counterpart(
                source_file=source_file,
                root=root,
                test_files=test_files,
            )

            if matched_test:
                code_test_links.append(
                    CodeTestLink(
                        source_file=rel,
                        test_file=str(matched_test.relative_to(root)),
                        link_type="NAMING_CONVENTION",
                    )
                )
            else:
                untraced.append(rel)

            doc_links.extend(
                self._extract_document_references(
                    source_file=source_file,
                    root=root,
                )
            )

        total_src = len(source_files)
        total_cov = len(code_test_links)

        pct = round(100 * total_cov / total_src, 1) if total_src else 0.0

        centralized_detected = False

        if pct == 0.0:
            centralized_detected = self._detect_centralized_test_harness(root)

        if pct == 0.0 and centralized_detected:
            coverage_note = (
                "CENTRALIZED_TEST_HARNESS_DETECTED "
                "(local file-pair coverage not applicable)"
            )

            notes.append(
                "CENTRALIZED_TEST_HARNESS_DETECTED: Repository appears to use "
                "a centralized or shared test execution architecture."
            )

            notes.append(
                "Local 1:1 source-to-test filename matching is not reliable "
                "for this repository."
            )

        elif 0.0 < pct < LOW_COVERAGE_THRESHOLD:
            # Coverage is low but not zero — check for harness evidence
            # before labelling as CENTRALIZED or as an untested liability
            centralized_detected = self._detect_centralized_test_harness(root)

            if centralized_detected:
                coverage_note = (
                    f"{pct}% (CENTRALIZED_TEST_HARNESS_DETECTED)"
                )
                notes.append(
                    f"CENTRALIZED_TEST_HARNESS_DETECTED: Coverage is {pct}% "
                    f"(below the {LOW_COVERAGE_THRESHOLD}% floor) but physical "
                    "harness evidence was found. Hybrid test architecture suspected."
                )
            else:
                # Evidence not found — honest result, no automatic claim
                coverage_note = (
                    f"{total_cov}/{total_src} source files have test counterparts "
                    f"by naming convention ({pct}%) — LOW_COVERAGE_DETECTED"
                )
                notes.append(
                    f"LOW_COVERAGE_DETECTED: Coverage is {pct}% "
                    f"(below the {LOW_COVERAGE_THRESHOLD}% floor) and no "
                    "centralized test harness evidence was found. "
                    "This is an honest result — not automatically promoted to "
                    "CENTRALIZED_TEST_HARNESS_DETECTED without evidence."
                )

        else:
            coverage_note = (
                f"{total_cov}/{total_src} source files have test counterparts "
                f"by naming convention ({pct}%)"
            )

            if pct == 0.0:
                notes.append(
                    "TEST_COVERAGE_METRIC_UNRELIABLE: No local file-pair test "
                    "matches were found and no centralized test harness was detected."
                )

        notes.append(
            "SCOPE NOTE: Requirement->Code mapping is Module 9 (V3-106). "
            "This module traces document references and test structure only."
        )

        return TraceabilityResult(
            document_code_links=doc_links,
            code_test_links=code_test_links,
            untraced_source=untraced,
            total_doc_links=len(doc_links),
            total_test_links=total_cov,
            coverage_note=coverage_note,
            notes=notes,
        )

    def _collect_source_files(self, root: Path) -> list[Path]:
        files: list[Path] = []

        for ext in self.SOURCE_EXTENSIONS:
            files.extend(root.rglob(f"*{ext}"))

        return sorted(files)

    def _collect_test_files(self, root: Path) -> list[Path]:
        test_files: list[Path] = []

        for file in self._collect_source_files(root):
            if self._is_test_file(file):
                test_files.append(file)

        return sorted(test_files)

    def _is_test_file(self, file: Path) -> bool:
        name = file.name.lower()
        path_parts = {part.lower() for part in file.parts}

        if name.startswith("test_"):
            return True

        if name.endswith("_test.py"):
            return True

        if name.endswith(".test.js") or name.endswith(".test.ts"):
            return True

        if name.endswith(".spec.js") or name.endswith(".spec.ts"):
            return True

        if any(marker in path_parts for marker in self.TEST_DIR_MARKERS):
            return True

        return False

    def _find_test_counterpart(
        self,
        source_file: Path,
        root: Path,
        test_files: list[Path],
    ) -> Path | None:
        source_name = source_file.name
        stem = source_file.stem
        suffix = source_file.suffix

        expected_names = {
            f"test_{source_name}",
            f"{stem}_test{suffix}",
            f"{stem}.test{suffix}",
            f"{stem}.spec{suffix}",
        }

        for test_file in test_files:
            if test_file.name in expected_names:
                return test_file

        return None

    def _extract_document_references(
        self,
        source_file: Path,
        root: Path,
    ) -> list[DocumentCodeLink]:
        links: list[DocumentCodeLink] = []

        try:
            lines = source_file.read_text(
                encoding="utf-8",
                errors="ignore",
            ).splitlines()
        except Exception:
            return links

        rel = str(source_file.relative_to(root))

        for line_no, line in enumerate(lines, start=1):
            for match in _DOC_REFERENCE_PATTERN.finditer(line):
                doc_name = (
                    match.group(1)
                    or match.group(2)
                    or ""
                ).strip()

                if not doc_name:
                    continue

                links.append(
                    DocumentCodeLink(
                        document_name=doc_name,
                        source_file=rel,
                        source_line=line_no,
                        reference_text=line.strip()[:120],
                    )
                )

        return links

    def _detect_centralized_test_harness(self, root: Path) -> bool:
        """
        Detects centralized/shared test execution files.

        Checks both naming indicators AND harness config files.
        Returns True only when physical evidence exists.
        Does NOT automatically claim CENTRALIZED_TEST_HARNESS_DETECTED
        without finding real files — that would violate the Truth Boundary.
        """
        # Check harness config files first (strongest evidence)
        for marker in HARNESS_CONFIG_MARKERS:
            if (root / marker).exists():
                return True

        # Then check for centralized test execution filenames
        for file in root.rglob("*"):
            if not file.is_file():
                continue
            name = file.name.lower()
            rel  = str(file.relative_to(root)).lower()
            if any(ind in name for ind in CENTRALIZED_TEST_INDICATORS):
                return True
            if any(ind in rel  for ind in CENTRALIZED_TEST_INDICATORS):
                return True

        return False
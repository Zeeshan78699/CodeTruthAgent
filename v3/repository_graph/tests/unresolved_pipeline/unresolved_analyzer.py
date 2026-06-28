"""
unresolved_analyzer.py

Experimental Module 2.5 validation harness.

Purpose:
Analyze unresolved graph entries and produce a clear breakdown before
any resolver attempts to fix them.

This file does NOT resolve anything.
It only explains the current unresolved state.

Truth Boundary:
- No guessing
- No forced resolution
- Unknown remains UNKNOWN
"""

from collections import Counter, defaultdict
from typing import Any, Dict, List


class UnresolvedAnalyzer:
    """
    Analyzes unresolved entries from Module 2 graph output.
    """

    def __init__(self, unresolved_entries: List[Dict[str, Any]]):
        self.unresolved_entries = unresolved_entries or []

    def total_unresolved(self) -> int:
        return len(self.unresolved_entries)

    def count_by_pattern(self) -> Dict[str, int]:
        """
        Groups unresolved entries by their existing pattern field.

        Example:
        - attribute_call
        - name_call_unresolved
        - self_method_not_found
        - parse_error
        """
        counter = Counter()

        for entry in self.unresolved_entries:
            pattern = entry.get("pattern", "unknown")
            counter[pattern] += 1

        return dict(counter)

    def count_by_module(self) -> Dict[str, int]:
        """
        Groups unresolved entries by module name.
        """
        counter = Counter()

        for entry in self.unresolved_entries:
            module = entry.get("module", "unknown")
            counter[module] += 1

        return dict(counter)

    def examples_by_pattern(self, limit: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """
        Keeps a few examples for each unresolved pattern.
        Useful for manual inspection.
        """
        examples = defaultdict(list)

        for entry in self.unresolved_entries:
            pattern = entry.get("pattern", "unknown")

            if len(examples[pattern]) < limit:
                examples[pattern].append(entry)

        return dict(examples)

    def summary(self) -> Dict[str, Any]:
        """
        Full unresolved analysis report.
        """
        return {
            "total_unresolved": self.total_unresolved(),
            "by_pattern": self.count_by_pattern(),
            "by_module": self.count_by_module(),
            "examples_by_pattern": self.examples_by_pattern(),
        }


def analyze_unresolved(unresolved_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Convenience function for pipeline usage.
    """
    analyzer = UnresolvedAnalyzer(unresolved_entries)
    return analyzer.summary()
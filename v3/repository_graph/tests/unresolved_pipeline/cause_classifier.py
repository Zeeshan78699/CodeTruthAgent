"""
cause_classifier.py

FIX: the original version checked entry.get("target")/"name"/"reason" -
none of which exist on real unresolved entries (only module/lineno/
pattern/note do). So the granular sub-classification for attribute_call
(getattr, external library, factory) never actually fired on real
data - every attribute_call fell through to the generic
"attribute_type_unknown" bucket regardless of its real content.

This now extracts the actual name being called (same regexes
fact_extractor.py already uses) and applies the SAME granular
heuristics already proven on the 327-item return-statement subset
(known_framework_functions.py, BUILTIN_LIKE_METHOD_NAMES, the
PascalCase/lowercase naming-convention fallback) - but applied here to
the FULL unresolved log (all 2,732 entries: attribute_call,
self_method_not_found, AND name_call_unresolved), not just return
statements. Same proven approach, full scope instead of a 327-item
subset.

This file does NOT resolve graph edges. It only explains WHY an
unresolved entry may exist.

Truth Boundary:
- Classification is conservative
- Unknown stays UNKNOWN
- Naming-convention guesses are labeled "_unconfirmed", never asserted
  as proven fact
- No edge is marked resolved here
"""

import re
from typing import Any, Dict, List

from .known_framework_functions import (
    KNOWN_FRAMEWORK_FUNCTIONS,
    BUILTIN_LIKE_METHOD_NAMES,
)

CLASS_ALIAS_PATTERNS = {
    "response_class",
    "session_class",
}

ATTRIBUTE_PATTERN = re.compile(r"\.([A-Za-z_][A-Za-z0-9_]*)\(")
SELF_METHOD_PATTERN = re.compile(r"self\.([A-Za-z_][A-Za-z0-9_]*)\(")
NAME_CALL_PATTERN = re.compile(r"Call to '([^']+)'")


class CauseClassifier:

    def _extract_called_name(self, entry: Dict[str, Any]):
        """The one thing missing before: the actual name being called,
        pulled from the real note text (not a nonexistent field)."""
        note = str(entry.get("note", ""))
        pattern = entry.get("pattern")

        if pattern == "attribute_call":
            match = ATTRIBUTE_PATTERN.search(note)
            return match.group(1) if match else None
        if pattern == "self_method_not_found":
            match = SELF_METHOD_PATTERN.search(note)
            return match.group(1) if match else None
        if pattern == "name_call_unresolved":
            match = NAME_CALL_PATTERN.search(note)
            return match.group(1) if match else None
        return None

    def _classify_called_name(self, called_name):
        """Same granular heuristics already validated on the 327-item
        return-statement subset, reused here at full scope."""
        if not called_name:
            return "attribute_type_unknown"

        if called_name in KNOWN_FRAMEWORK_FUNCTIONS:
            return "framework_helper"
        if called_name in CLASS_ALIAS_PATTERNS:
            return "class_alias"
        if called_name in BUILTIN_LIKE_METHOD_NAMES:
            return "builtin_like"

        # Naming-convention guesses, NOT proven facts - disclosed as such.
        if called_name[0].islower():
            return "name_suggests_object_method_unconfirmed"
        if called_name[0].isupper():
            return "name_suggests_external_class_unconfirmed"

        return "attribute_type_unknown"

    def classify_entry(self, entry: Dict[str, Any]) -> str:
        pattern = entry.get("pattern", "unknown")

        if pattern == "parse_error":
            return "parse_error"

        called_name = self._extract_called_name(entry)
        return self._classify_called_name(called_name)

    def classify_all(self, unresolved_entries):
        counts, examples = {}, {}
        for entry in unresolved_entries or []:
            cause = self.classify_entry(entry)
            counts[cause] = counts.get(cause, 0) + 1
            if cause not in examples:
                examples[cause] = []
            if len(examples[cause]) < 5:
                examples[cause].append(entry)
        return {"cause_counts": counts, "cause_examples": examples}


def classify_unresolved_causes(unresolved_entries):
    return CauseClassifier().classify_all(unresolved_entries)

"""
fact_extractor_v2.py

Experimental Module 2.5 validation harness.

Purpose:
Enrich unresolved entries with additional deterministic facts for
advanced resolvers.

V1 Extracted: attribute_name, method_name, class_name
V2 Adds: constructor_class, factory_function, property_name

Truth Boundary:
- Extract only proven facts
- Never infer
- Never guess

FIX (found via reflection_resolver.py synthetic test - the note text
for a name_call_unresolved entry is literally formatted as
"Call to 'NAME(...)' not found..." where "(...)" is call_graph.py's
own fixed display template, not real source text. The original
NAME_CALL_PATTERN (r"Call to '([^']+)'") is greedy and captured
"NAME(...)" whole - including that trailing template suffix - instead
of just "NAME". Any downstream code trying to look this up against an
assignment_table key (which only ever stores the bare name, e.g.
"module:handler") would silently never match, since "handler(...)" !=
"handler". Now stops capturing at the first literal "(" the same way
ATTRIBUTE_PATTERN / SELF_METHOD_PATTERN already do elsewhere in this
file, so only the real identifier is captured.
"""

import re
from typing import Any, Dict, List


ATTRIBUTE_PATTERN = re.compile(r"\.([A-Za-z_][A-Za-z0-9_]*)\(")
SELF_METHOD_PATTERN = re.compile(r"self\.([A-Za-z_][A-Za-z0-9_]*)\(")
CLASS_PATTERN = re.compile(r"class '([^']+)'")
# FIX: was r"Call to '([^']+)'" - see module docstring.
NAME_CALL_PATTERN = re.compile(r"Call to '([A-Za-z_][A-Za-z0-9_]*)\(")


class FactExtractorV2:

    def __init__(self, unresolved_entries: List[Dict[str, Any]]):
        self.unresolved_entries = unresolved_entries or []

    def _extract_attribute_name(self, note: str):
        match = ATTRIBUTE_PATTERN.search(note)
        return match.group(1) if match else None

    def _extract_self_method(self, note: str):
        match = SELF_METHOD_PATTERN.search(note)
        return match.group(1) if match else None

    def _extract_class_name(self, note: str):
        match = CLASS_PATTERN.search(note)
        return match.group(1) if match else None

    def _extract_name_call(self, note: str):
        match = NAME_CALL_PATTERN.search(note)
        return match.group(1) if match else None

    def extract_fact(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        fact = dict(entry)
        note = str(entry.get("note", ""))
        pattern = entry.get("pattern", "")

        fact["attribute_name"] = None
        fact["method_name"] = None
        fact["class_name"] = None
        fact["variable_name"] = None
        fact["constructor_class"] = None
        fact["factory_function"] = None
        fact["property_name"] = None

        if pattern == "attribute_call":
            fact["attribute_name"] = self._extract_attribute_name(note)
            # constructor_class / factory_function left None here -
            # see resolution_pipeline.py's _enrich_origin_facts for the
            # real, working version of this enrichment.

        elif pattern == "self_method_not_found":
            fact["method_name"] = self._extract_self_method(note)
            fact["class_name"] = self._extract_class_name(note)
            if fact["method_name"]:
                fact["property_name"] = fact["method_name"]

        elif pattern == "name_call_unresolved":
            fact["variable_name"] = self._extract_name_call(note)

        return fact

    def extract_all(self) -> List[Dict[str, Any]]:
        return [self.extract_fact(entry) for entry in self.unresolved_entries]


def extract_facts_v2(unresolved_entries: List[Dict[str, Any]]):
    extractor = FactExtractorV2(unresolved_entries)
    return extractor.extract_all()
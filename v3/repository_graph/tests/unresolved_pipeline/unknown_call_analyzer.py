"""
unknown_call_analyzer.py

FIX 1: FRAMEWORK_APIS replaced with the shared
known_framework_functions.KNOWN_FRAMEWORK_FUNCTIONS - was previously
its own separate list, missing send_file.

FIX 2: the fallback heuristics (lowercase name -> object_method,
PascalCase name -> external_library) are naming-convention guesses,
not proven facts - a locally-defined PascalCase helper or a constant
would be mis-bucketed with no real evidence behind it. Renamed to
disclose this rather than presenting them as confident categories.

This is NOT a resolver. It is a measurement tool that tells us where
the remaining deterministic gains exist.
"""

from collections import Counter

from .known_framework_functions import (
    KNOWN_FRAMEWORK_FUNCTIONS,
    BUILTIN_LIKE_METHOD_NAMES,
)

CLASS_ALIAS_PATTERNS = {
    "response_class",
    "session_class",
}


class UnknownCallAnalyzer:

    def __init__(self, classification_results):
        self.results = classification_results
        self.counter = Counter()
        self.examples = {}

    def _classify(self, call_name):
        if call_name in KNOWN_FRAMEWORK_FUNCTIONS:
            return "framework_api"
        if call_name in CLASS_ALIAS_PATTERNS:
            return "class_alias"
        if call_name in BUILTIN_LIKE_METHOD_NAMES:
            return "builtin_like"

        # FIX: renamed from "object_method"/"external_library" - these
        # are naming-convention heuristics, not proven categories.
        if call_name and call_name[0].islower():
            return "name_suggests_object_method_unconfirmed"
        if call_name and call_name[0].isupper():
            return "name_suggests_external_class_unconfirmed"

        return "true_unknown"

    def build(self):
        for item in self.results:
            if item["category"] != "unknown":
                continue
            call_name = item["call"]
            bucket = self._classify(call_name)
            self.counter[bucket] += 1
            self.examples.setdefault(bucket, [])
            if len(self.examples[bucket]) < 20:
                self.examples[bucket].append(call_name)

        return {"counts": dict(self.counter), "examples": self.examples}


def analyze_unknown_calls(classification_results):
    return UnknownCallAnalyzer(classification_results).build()

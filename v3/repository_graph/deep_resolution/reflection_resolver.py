"""
reflection_resolver.py

FIX (main-pipeline integration), two separate issues found:

1. class_graph is now keyed by fully qualified name, not bare name -
   same fix as inheritance_resolver.py and the same reasoning
   (collision risk across many repos, not just one). Qualifies using
   entry["module"] + entry["class_name"], reliable for the same reason
   as elsewhere - a method's enclosing class is defined in the same file.

2. The gate below used to check entry.get("cause") ==
   "reflection_or_dynamic_attribute" - a label the rewritten
   cause_classifier.py (today's classification-gap fix) no longer
   produces at all, so this gate could never fire for ANY repo,
   regardless of whether real reflection-style calls existed. Now
   checks the note text directly for a literal "getattr" mention,
   decoupling this resolver from a specific classifier label that may
   change independently of it.

FIX (corpus validation - 69-repo run, dr_reflection == 0 on every
single repo, confirmed via direct code inspection, not guessed):

resolve_entry() required entry.get("reflection_name") to be truthy,
but NOTHING in the pipeline ever set that field. fact_extractor_v2.py
initializes attribute_name / method_name / class_name / variable_name /
constructor_class / factory_function / property_name on every fact -
reflection_name was simply never one of them, in any branch. So
resolve_entry() returned None unconditionally, on every call, for
every repo - completely independent of whether resolve_batch()'s
"getattr" note-text gate was correctly identifying candidates or not.
Same root-cause shape as the constructor_class/factory_function gap
_enrich_origin_facts (resolution_pipeline.py) already fixed elsewhere
in this pipeline - a resolver expecting a fact field nothing upstream
ever populated.

Scope of this fix, stated honestly (Truth Boundary):
Only resolves getattr(self, "literal_string")(...) - a literal string
second argument, on `self` specifically (since class_name is only
ever populated for self_method_not_found-pattern entries upstream in
fact_extractor_v2.py - there is no qualified-class information
available for getattr() on an arbitrary non-self object without
further work not built here).

Deliberately NOT attempted here, and NOT a bug in this file -
genuinely unresolvable without runtime value-tracing, correctly stays
unresolved per this project's Truth Boundary:
  - getattr(self, some_variable)(...)        - name is a variable, not
                                                 a literal; the engine
                                                 cannot know what string
                                                 it holds without
                                                 tracing its value
  - getattr(some_other_obj, "name")(...)      - non-self target; this
                                                 object's class isn't
                                                 available on the entry
  - dispatch_dict.get(key)(...)               - dynamic dict key
  - self.module_list[i](...)                  - ModuleList/Sequential
                                                 indexing; a different,
                                                 larger problem, already
                                                 tracked separately (see
                                                 model_graph_tracer.py's
                                                 documented gap and the
                                                 Data Flow decision
                                                 record)

Verified against real source before merging: re-run
reflection_diagnostic.py and the full pipeline against transformers
and a handful of other 69-corpus repos, and confirm dr_reflection
moves only on repos that actually contain literal-string
getattr(self, "...")(...) calls - it is expected to remain 0 on repos
(like transformers) that only use variable-named getattr calls. Do
not claim this "fixes reflection" broadly without that per-repo
re-check - that distinction matters for honest disclosure.
"""

import re
from typing import Any, Dict, List, Optional

# Matches getattr(self, "name") or getattr(self, 'name') - LITERAL
# string second argument only, target is literally "self". Deliberately
# narrow: see module docstring for what this does NOT attempt to catch
# and why those cases are correctly left unresolved rather than guessed.
REFLECTION_GETATTR_PATTERN = re.compile(
    r"getattr\(\s*self\s*,\s*['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]"
)


class ReflectionResolver:
    def __init__(self, class_graph: Dict[str, Any]):
        self.class_graph = class_graph or {}

    def _method_exists(self, qualified_class_name, method_name) -> bool:
        class_info = self.class_graph.get(qualified_class_name)
        if not class_info:
            return False
        methods = set(class_info.get("methods", []))
        return method_name in methods

    def _extract_reflection_name(self, note: str) -> Optional[str]:
        """FIX: the missing piece. Pulls the literal string argument
        out of a getattr(self, "literal") call directly from the note
        text - same self-contained regex-extraction approach
        cause_classifier.py and fact_extractor_v2.py already use
        elsewhere in this codebase. Returns None (not a guess) for any
        shape that doesn't match - variable-named getattr, non-self
        target, etc. - which then correctly falls through to staying
        unresolved, same as before this fix."""
        match = REFLECTION_GETATTR_PATTERN.search(note)
        return match.group(1) if match else None

    def resolve_entry(self, entry):
        class_name = entry.get("class_name")
        module = entry.get("module")

        # FIX: reflection_name was never populated upstream - extract
        # it here directly from the note text if it isn't already on
        # the entry. Only ever yields a value for the literal-string
        # getattr(self, "...") shape; everything else correctly
        # returns None here, same as it silently always did before -
        # the difference is THIS specific shape now actually has a
        # chance to resolve instead of being unconditionally blocked.
        reflection_name = entry.get("reflection_name")
        if not reflection_name:
            note_text = str(entry.get("note", ""))
            reflection_name = self._extract_reflection_name(note_text)

        if not class_name or not module or not reflection_name or not isinstance(reflection_name, str):
            return None
        qualified_class_name = f"{module}.{class_name}"
        if not self._method_exists(qualified_class_name, reflection_name):
            return None
        return {"resolved": True, "resolver": "reflection", "resolution_source": "STATIC_GETATTR",
                "class_name": qualified_class_name, "method_name": reflection_name, "original_entry": entry}

    def resolve_batch(self, unresolved_entries):
        resolved, remaining = [], []
        for entry in unresolved_entries:
            note = str(entry.get("note", "")).lower()
            if "getattr" not in note:
                remaining.append(entry)
                continue
            result = self.resolve_entry(entry)
            if result:
                resolved.append(result)
            else:
                remaining.append(entry)
        return {"resolver": "reflection", "resolved_count": len(resolved), "remaining_count": len(remaining),
                "resolved_entries": resolved, "remaining_entries": remaining}


def run_reflection_resolution(unresolved_entries, class_graph):
    return ReflectionResolver(class_graph).resolve_batch(unresolved_entries)
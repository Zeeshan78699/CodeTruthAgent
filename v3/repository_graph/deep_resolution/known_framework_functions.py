"""
known_framework_functions.py

FIX: there were three separate, independently-maintained lists of
"known framework function names" scattered across
constructor_call_classifier.py (FRAMEWORK_HELPERS - had send_file, not
url_for/render_template_string), unknown_call_analyzer.py
(FRAMEWORK_APIS - had url_for/render_template_string, not send_file),
and object_method_resolver.py (its own separate, unrelated category
scheme entirely). The same real call (url_for, jsonify,
render_template) was getting a different category label depending on
which tool looked at it. This is the single shared list every
classifier should import instead.

These are Flask's own public helper functions with genuinely provable
return types (e.g. jsonify really does return flask.Response) - a
real, scoped, deterministic category, not a guess. Distinct from
BUILTIN_LIKE_METHOD_NAMES below.

FIX: BUILTIN_LIKE_METHOD_NAMES used to be its own separate, smaller
hand-maintained set (7 names) that drifted out of sync with
builtin_type_engine.py's own, more complete BUILTIN_METHODS table
(~35 names across str/list/dict/set). Real examples like .endswith,
.rsplit, .strip were genuinely known-resolvable there but missing
here, so they were misclassified as "unconfirmed" by cause_classifier.
Now derived directly from that one real source instead of a second,
separately-maintained list.
"""

from .builtin_type_engine import BUILTIN_METHODS

KNOWN_FRAMEWORK_FUNCTIONS = {
    "jsonify",
    "redirect",
    "render_template",
    "render_template_string",
    "send_file",
    "send_from_directory",
    "stream_with_context",
    "url_for",
}

BUILTIN_LIKE_METHOD_NAMES = set().union(*BUILTIN_METHODS.values())

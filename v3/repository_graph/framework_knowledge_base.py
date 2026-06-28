"""
framework_knowledge_base.py

A small, explicit, hand-curated knowledge base of well-known framework
helper functions whose return type is genuinely provable - not a
guess. Flask is the first, validated entry.

Pluggable by design, not "knows every framework automatically":
detection works by checking which framework package names actually
appear in a repo's real absolute imports (the same root_counts already
computed elsewhere in this pipeline - repo-agnostic by construction,
since it just reads whatever the repo actually imports). Adding a
second or third framework later means adding another entry to
FRAMEWORK_KNOWLEDGE_BASES, not redesigning anything here or in
type_inference.py.

Honesty boundary: a repo using a framework with no entry in this file
gets ZERO additional resolution from it - falls through cleanly to the
existing builtin/naming-heuristic classification, exactly as before
this file existed. Nothing here ever guesses a framework's behavior;
each entry is real, specific, documented knowledge about one named
public function.

type_info shapes used (consumed by type_inference.py's
_ReturnClassifier and, downstream, TypeAwareCallResolver):
    ("builtin", name)
        - same shape used everywhere else in this pipeline.
    ("framework_class", framework_name, class_name)
        - a known, externally-defined class (e.g. flask.Response).
          Deliberately a DIFFERENT kind tag than ("class", module,
          name), which means "defined inside THIS scanned repo's own
          class_graph". A framework's classes live in the framework's
          OWN source, not the application repo being scanned - so
          this is disclosed as external knowledge, never something a
          consumer should expect to find by looking up class_graph.
"""

FRAMEWORK_KNOWLEDGE_BASES = {
    "flask": {
        "jsonify": ("framework_class", "flask", "Response"),
        "redirect": ("framework_class", "flask", "Response"),
        "send_file": ("framework_class", "flask", "Response"),
        "send_from_directory": ("framework_class", "flask", "Response"),
        "render_template": ("builtin", "str"),
        "render_template_string": ("builtin", "str"),
        "url_for": ("builtin", "str"),
    },
}


def detect_active_frameworks(root_counts):
    """
    Returns the set of framework names (keys of
    FRAMEWORK_KNOWLEDGE_BASES) actually imported by this repo, based
    on its real absolute-import root counts. Dynamic and
    repo-agnostic - the same function runs correctly whether a repo
    uses Flask, some other framework, or none at all.
    """
    if not root_counts:
        return set()
    return {fw for fw in FRAMEWORK_KNOWLEDGE_BASES if fw in root_counts}


def build_active_knowledge_base(root_counts):
    """
    Merges the knowledge bases of every framework actually detected in
    this repo into one {function_name: type_info} dict. Empty for a
    repo using no recognized framework - never activates a framework's
    knowledge for a repo that doesn't actually import it.
    """
    active = {}
    for fw in detect_active_frameworks(root_counts):
        active.update(FRAMEWORK_KNOWLEDGE_BASES[fw])
    return active

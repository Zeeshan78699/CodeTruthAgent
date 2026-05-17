def suggest_merge(func1, func2, best_function, duplicate_info=None):
    """
    Suggest safe merge strategy.

    Extended functionality:
    - Keeps old behavior for safe duplicates
    - Blocks auto-merge when semantic review is required
    """

    duplicate_info = duplicate_info or {}

    auto_merge_safe = duplicate_info.get("auto_merge_safe", True)
    duplicate_type = duplicate_info.get("duplicate_type", "SAFE_LOGICAL_DUPLICATE")
    semantic_reason = duplicate_info.get("semantic_reason", "")

    if best_function == func1["name"]:
        remove = func2["name"]
        keep = func1["name"]
    else:
        remove = func1["name"]
        keep = func2["name"]

    if not auto_merge_safe:
        return {
            "keep": keep,
            "remove": remove,
            "action": "Manual review required. Do not auto-replace.",
            "merge_allowed": False,
            "duplicate_type": duplicate_type,
            "reason": semantic_reason,
            "warning": (
                "Logic is similar, but business meaning may be different. "
                "Merging may reduce readability or break domain intent."
            )
        }

    return {
        "keep": keep,
        "remove": remove,
        "action": f"Replace all usages of {remove}() with {keep}()",
        "merge_allowed": True,
        "duplicate_type": duplicate_type,
        "reason": "Safe logical duplicate detected."
    }
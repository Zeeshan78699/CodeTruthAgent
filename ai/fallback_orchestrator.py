from validation.approval_engine import request_approval


LOW_CONFIDENCE_THRESHOLD = 0.60


def should_fallback(confidence_score):
    """
    Decide whether V2 should fallback to V1.

    Existing V1 remains frozen.
    """

    return confidence_score < LOW_CONFIDENCE_THRESHOLD


def route_to_v1(
    finding,
    confidence_score,
    v1_handler=None
):
    """
    Safe fallback orchestration layer.

    If confidence is low:
    - route through approval engine
    - optionally invoke V1 deterministic handler
    """

    fallback_required = should_fallback(confidence_score)

    if not fallback_required:

        return {
            "fallback": False,
            "status": "V2_CONFIDENT",
            "finding": finding
        }

    approval_result = request_approval(finding)

    result = {
        "fallback": True,
        "status": "V1_FALLBACK_TRIGGERED",
        "approval": approval_result
    }

    # Optional frozen V1 invocation
    if v1_handler:

        try:

            v1_result = v1_handler(finding)

            result["v1_result"] = v1_result

        except Exception as error:

            result["v1_error"] = str(error)

    return result


def build_fallback_record(
    finding,
    confidence_score,
    reason
):
    """
    Build fallback audit metadata.
    """

    return {
        "file_path": finding.get("file_path"),
        "function_name": finding.get("function_name"),
        "severity": finding.get("severity"),
        "category": finding.get("category"),
        "confidence_score": confidence_score,
        "fallback_reason": reason
    }


def fallback_due_to_unknown_api(
    finding,
    confidence_score
):
    """
    Unknown API routing.
    """

    return route_to_v1(
        finding,
        confidence_score
    )


def fallback_due_to_semantic_uncertainty(
    finding,
    confidence_score
):
    """
    Semantic uncertainty routing.
    """

    return route_to_v1(
        finding,
        confidence_score
    )
from validation.syntax_validator import validate_python_syntax
from validation.rollback_manager import RollbackManager

from validation.approval_engine import request_approval

from ai.fallback_orchestrator import route_to_v1


def execute_governed_action(
    finding,
    target_file,
    proposed_action,
    confidence_score=1.0,
    v1_handler=None
):
    """
    Final V2 governance execution gate.

    Responsibilities:
    - approval routing
    - fallback orchestration
    - rollback creation
    - syntax validation
    - controlled execution
    """

    approval_result = request_approval(finding)

    approval_status = approval_result.get("status")

    # BLOCKED / rejected
    if approval_status == "REJECTED":

        return {
            "execution_status": "BLOCKED",
            "reason": "Governance approval rejected.",
            "approval": approval_result
        }

    # REVIEW queue
    if approval_status == "PENDING_REVIEW":

        return {
            "execution_status": "WAITING_FOR_HUMAN",
            "approval": approval_result
        }

    # Low-confidence fallback
    fallback_result = route_to_v1(
        finding=finding,
        confidence_score=confidence_score,
        v1_handler=v1_handler
    )

    # Create rollback before execution
    rollback_result = RollbackManager.create_backup(target_file)

    rollback_path = rollback_result["backup_path"]

    # Execute proposed action
    try:

        proposed_action()

    except Exception as error:

        return {
            "execution_status": "FAILED",
            "reason": str(error),
            "rollback_created": rollback_path,
            "fallback": fallback_result
        }

    # Validate syntax after execution
    syntax_valid = validate_python_syntax(target_file)

    if not syntax_valid:

        return {
            "execution_status": "SYNTAX_VALIDATION_FAILED",
            "rollback_created": rollback_path,
            "fallback": fallback_result
        }

    return {
        "execution_status": "EXECUTED_SUCCESSFULLY",
        "rollback_created": rollback_path,
        "fallback": fallback_result,
        "syntax_validation": "PASSED"
    }


def simulate_safe_execution(
    finding,
    target_file,
    proposed_action
):
    """
    Dry-run governance execution.
    """

    return execute_governed_action(
        finding=finding,
        target_file=target_file,
        proposed_action=proposed_action,
        confidence_score=1.0
    )
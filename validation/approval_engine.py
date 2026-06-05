import json
import os
from datetime import datetime, timezone



APPROVAL_LOG_FILE = "approval_audit_log.json"


def load_approval_log():
    """
    Load governance approval history.
    """

    if not os.path.exists(APPROVAL_LOG_FILE):
        return []

    with open(APPROVAL_LOG_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_approval_log(log_data):
    """
    Save governance approval history.
    """

    with open(APPROVAL_LOG_FILE, "w", encoding="utf-8") as file:
        json.dump(log_data, file, indent=4)


def create_approval_entry(
    file_path,
    function_name,
    severity,
    category,
    decision,
    reviewer="human_reviewer",
    reason=""
):
    """
    Create governance approval record.
    """

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "file_path": file_path,
        "function_name": function_name,
        "severity": severity,
        "category": category,
        "decision": decision,
        "reviewer": reviewer,
        "reason": reason
    }


def log_decision(entry):
    """
    Persist governance decision.
    """

    log_data = load_approval_log()

    log_data.append(entry)

    save_approval_log(log_data)


def request_approval(finding):
    """
    Human-In-The-Loop governance routing.

    Rules:
    - BLOCK → auto reject
    - REVIEW → requires approval
    - SAFE → auto approve
    """

    severity = finding.get("severity", "UNKNOWN")

    if severity == "BLOCK":

        entry = create_approval_entry(
            file_path=finding.get("file_path"),
            function_name=finding.get("function_name"),
            severity=severity,
            category=finding.get("category"),
            decision="REJECTED",
            reviewer="system",
            reason="BLOCK severity automatically rejected."
        )

        log_decision(entry)

        return {
            "status": "REJECTED",
            "entry": entry
        }

    if severity == "REVIEW":

        entry = create_approval_entry(
            file_path=finding.get("file_path"),
            function_name=finding.get("function_name"),
            severity=severity,
            category=finding.get("category"),
            decision="PENDING_REVIEW",
            reviewer="human_required",
            reason="Human approval required."
        )

        log_decision(entry)

        return {
            "status": "PENDING_REVIEW",
            "entry": entry
        }

    entry = create_approval_entry(
        file_path=finding.get("file_path"),
        function_name=finding.get("function_name"),
        severity=severity,
        category=finding.get("category"),
        decision="APPROVED",
        reviewer="system",
        reason="SAFE severity automatically approved."
    )

    log_decision(entry)

    return {
        "status": "APPROVED",
        "entry": entry
    }


def approve_finding(finding, reviewer="human_reviewer"):
    """
    Human approves governance finding.
    """

    entry = create_approval_entry(
        file_path=finding.get("file_path"),
        function_name=finding.get("function_name"),
        severity=finding.get("severity"),
        category=finding.get("category"),
        decision="APPROVED",
        reviewer=reviewer,
        reason="Human approved governance action."
    )

    log_decision(entry)

    return entry


def reject_finding(
    finding,
    reviewer="human_reviewer",
    reason="Rejected by reviewer."
):
    """
    Human rejects governance finding.
    """

    entry = create_approval_entry(
        file_path=finding.get("file_path"),
        function_name=finding.get("function_name"),
        severity=finding.get("severity"),
        category=finding.get("category"),
        decision="REJECTED",
        reviewer=reviewer,
        reason=reason
    )

    log_decision(entry)

    return entry


def get_pending_reviews():
    """
    Return all pending governance reviews.
    """

    log_data = load_approval_log()

    pending = []

    for entry in log_data:

        if entry.get("decision") == "PENDING_REVIEW":
            pending.append(entry)

    return pending
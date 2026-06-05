import json
import os
from datetime import datetime


GOVERNANCE_MEMORY_FILE = "governance_memory.json"


def load_governance_memory():
    """
    Load governance memory database.
    """

    if not os.path.exists(GOVERNANCE_MEMORY_FILE):
        return []

    with open(GOVERNANCE_MEMORY_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_governance_memory(memory):
    """
    Save governance memory database.
    """

    with open(GOVERNANCE_MEMORY_FILE, "w", encoding="utf-8") as file:
        json.dump(memory, file, indent=4)


def build_memory_entry(
    file_path,
    function_name,
    severity,
    category,
    decision,
    confidence_score,
    source="V2"
):
    """
    Create governance memory entry.
    """

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "file_path": file_path,
        "function_name": function_name,
        "severity": severity,
        "category": category,
        "decision": decision,
        "confidence_score": confidence_score,
        "source": source
    }


def store_governance_decision(
    file_path,
    function_name,
    severity,
    category,
    decision,
    confidence_score,
    source="V2"
):
    """
    Persist governance decision.
    """

    memory = load_governance_memory()

    entry = build_memory_entry(
        file_path=file_path,
        function_name=function_name,
        severity=severity,
        category=category,
        decision=decision,
        confidence_score=confidence_score,
        source=source
    )

    memory.append(entry)

    save_governance_memory(memory)

    return entry


def find_previous_decision(
    function_name,
    category
):
    """
    Search for previous governance decisions.
    """

    memory = load_governance_memory()

    matches = []

    for entry in memory:

        if (
            entry.get("function_name") == function_name
            and entry.get("category") == category
        ):
            matches.append(entry)

    return matches


def get_high_risk_history():
    """
    Return all BLOCK governance history.
    """

    memory = load_governance_memory()

    high_risk = []

    for entry in memory:

        if entry.get("severity") == "BLOCK":
            high_risk.append(entry)

    return high_risk


def get_repeat_offenders():
    """
    Detect repeatedly flagged functions.
    """

    memory = load_governance_memory()

    counts = {}

    for entry in memory:

        key = (
            entry.get("function_name"),
            entry.get("category")
        )

        counts[key] = counts.get(key, 0) + 1

    repeat_offenders = []

    for key, count in counts.items():

        if count >= 2:

            repeat_offenders.append({
                "function_name": key[0],
                "category": key[1],
                "count": count
            })

    return repeat_offenders


def build_governance_summary():
    """
    Build governance statistics summary.
    """

    memory = load_governance_memory()

    summary = {
        "total_entries": len(memory),
        "approved": 0,
        "rejected": 0,
        "review": 0,
        "block": 0
    }

    for entry in memory:

        decision = entry.get("decision")
        severity = entry.get("severity")

        if decision == "APPROVED":
            summary["approved"] += 1

        if decision == "REJECTED":
            summary["rejected"] += 1

        if severity == "REVIEW":
            summary["review"] += 1

        if severity == "BLOCK":
            summary["block"] += 1

    return summary
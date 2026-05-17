import json
import os

MEMORY_FILE = "memory_template.json"


def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return []

    with open(MEMORY_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_memory(memory):
    with open(MEMORY_FILE, "w", encoding="utf-8") as file:
        json.dump(memory, file, indent=4)


def store_decision(func1, func2, best_choice, reason, decision="approved"):
    memory = load_memory()

    entry = {
        "function_1": func1,
        "function_2": func2,
        "best": best_choice,
        "reason": reason,
        "decision": decision
    }

    for existing in memory:
        if (
            existing.get("function_1") == func1 and existing.get("function_2") == func2
        ) or (
            existing.get("function_1") == func2 and existing.get("function_2") == func1
        ):
            existing["best"] = best_choice
            existing["reason"] = reason
            existing["decision"] = decision
            save_memory(memory)
            return

    memory.append(entry)
    save_memory(memory)


def store_rejection(func1, func2, best_choice, reason):
    store_decision(
        func1,
        func2,
        best_choice,
        reason,
        decision="rejected"
    )


def check_memory(func1, func2):
    memory = load_memory()

    best_match = None

    for entry in memory:

        f1 = entry.get("function_1")
        f2 = entry.get("function_2")

        if (
            (f1 == func1 and f2 == func2) or
            (f1 == func2 and f2 == func1)
        ):

            # 🔥 PRIORITIZE REJECTED DECISIONS
            if entry.get("decision") == "rejected":
                return entry

            # Store approved/default match
            best_match = entry

    # Return approved/default if no rejected found
    if best_match:
        if "decision" not in best_match:
            best_match["decision"] = "approved"

        return best_match

    return None
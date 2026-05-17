# risk_analyzer.py
# V1: Local risk scoring — partially active
# V2: Will become primary governance + semantic safety engine
# Do NOT delete — contains valuable business semantic logic


import re
import os


CORE_FILES = {
    "main.py",
    "code_modifier.py",
    "memory_store.py",
    "duplicate_detector.py",
    "merge_advisor.py",
    "risk_analyzer.py"
}


BUSINESS_WORDS = {
    "invoice", "tax", "price", "amount", "total", "vat", "payment",
    "customer", "vendor", "supplier", "order", "po", "contract",
    "employee", "salary", "account", "balance", "journal", "asset"
}


def find_function_usage(file_path, function_name):
    """
    Find how many times a function is used in the file.
    Counts function calls only.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        code = file.read()

    pattern = rf"\b{function_name}\("
    matches = re.findall(pattern, code)

    return len(matches)


def find_project_usage(project_root, function_name):
    """
    Scan all Python files for function usage.

    Returns:
        total_usage,
        dependency_map
    """

    total_usage = 0
    dependency_map = {}

    for root, _, files in os.walk(project_root):

        for file in files:

            if not file.endswith(".py"):
                continue

            full_path = os.path.join(root, file)

            try:
                count = find_function_usage(full_path, function_name)

                if count > 0:
                    dependency_map[full_path] = count
                    total_usage += count

            except Exception:
                continue

    return total_usage, dependency_map


def has_business_meaning(function_name):
    name = function_name.lower()
    return any(word in name for word in BUSINESS_WORDS)


def analyze_risk(file_path, function_name, duplicate_info=None):
    """
    Analyze risk before modification.

    Extended functionality:
    - Usage count risk
    - Core file protection
    - Business semantic protection
    - Duplicate semantic conflict protection
    - Cross-file dependency awareness
    """

    duplicate_info = duplicate_info or {}

    project_root = "."

    usage_count, dependency_map = find_project_usage(
        project_root,
        function_name
    )

    risk_points = 0
    reasons = []

    # Usage analysis
    if usage_count == 0:
        reasons.append("Function is not used anywhere")

    elif usage_count <= 2:
        risk_points += 1
        reasons.append(f"Function used {usage_count} times")

    else:
        risk_points += 2
        reasons.append(f"Function heavily used ({usage_count} times)")

    # 🔥 TC21 Dependency Escalation
    if len(dependency_map) >= 3:
        risk_points += 2
        reasons.append(
            f"Function affects {len(dependency_map)} dependent files"
        )

    normalized_file = file_path.replace("\\", "/").split("/")[-1]

    # Core system protection
    if normalized_file in CORE_FILES:
        risk_points += 2
        reasons.append("Core system file detected")

    # Business/domain awareness
    if has_business_meaning(function_name):
        risk_points += 1
        reasons.append("Function name has business/domain meaning")

    # Semantic safety
    if duplicate_info.get("auto_merge_safe") is False:
        risk_points += 2
        reasons.append(
            "Semantic conflict detected; manual review required"
        )

    # Final risk level
    if risk_points == 0:
        risk_level = "Low"

    elif risk_points <= 2:
        risk_level = "Medium"

    else:
        risk_level = "High"

    return risk_level, "; ".join(reasons)
import os
import re


def is_production_file(file_path):
    """
    Decide whether a file should be counted in production dependency risk.

    Purpose:
    - Exclude test files
    - Exclude UAT runner files
    - Exclude revision files
    - Exclude temporary/sandbox files

    This prevents test/revision files from inflating usage_count
    and incorrectly converting Medium risk into High/Critical risk.
    """

    normalized = file_path.replace("\\", "/").lower()

    excluded_patterns = [
        "/tests/",
        "run_uat",
        "uat_test",
        "_rev",
        "/test_",
        "_test.py",
        "mock",
        "sandbox",
        "temp",
        "__pycache__",
        ".venv",
        ".git"
    ]

    for pattern in excluded_patterns:
        if pattern in normalized:
            return False

    return True


def find_function_usage_across_project(project_path, function_name):
    """
    Find all production usages of a function across project files.

    Existing logic preserved:
    - Walk project folders
    - Read Python files
    - Count function calls
    - Return same structure:
      [
        {"file": file_path, "count": count}
      ]

    Extended logic:
    - Excludes tests, UAT, revision, sandbox, temp files
    """

    usage_locations = []

    for root, dirs, files in os.walk(project_path):

        # Ignore unnecessary folders
        dirs[:] = [
            d for d in dirs
            if d not in [".venv", "__pycache__", ".git"]
        ]

        for file in files:

            if file.endswith(".py"):

                file_path = os.path.join(root, file)

                # NEW SAFE FILTER:
                # Do not count non-production files in dependency risk.
                if not is_production_file(file_path):
                    continue

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        code = f.read()

                    matches = re.findall(
                        rf"\b{re.escape(function_name)}\(",
                        code
                    )

                    if matches:
                        usage_locations.append({
                            "file": file_path,
                            "count": len(matches)
                        })

                except Exception:
                    # Safe protection against unreadable files
                    continue

    return usage_locations


def analyze_global_risk(project_path, function_name):
    """
    Analyze project-wide dependency risk.

    Existing functionality preserved:
    - Tracks total usage count
    - Tracks dependent file count
    - Preserves existing return structure:
      (risk_level, risk_detail, usages)

    Extended functionality:
    - Risk is now based only on production files.
    """

    usages = find_function_usage_across_project(
        project_path,
        function_name
    )

    total_usage = sum(
        u["count"] for u in usages
    )

    dependency_count = len(usages)
    
    
    # No usage
    if total_usage == 0:

        return (
            "Low",
            "Function not used anywhere in production project files",
            usages
        )

    # Small production impact
    elif total_usage <= 3:

        return (
            "Medium",
            (
                f"Function used {total_usage} times across production files; "
                f"affects {dependency_count} dependent files"
            ),
        usages
    )

    # Moderate production impact
    elif total_usage <= 7:

        return (
            "High",
            (
                f"Function heavily used ({total_usage} times); "
                f"affects {dependency_count} dependent files"
            ),
            usages
        )

    # Large blast radius
    else:

        return (
            "Critical",
            (
             f"Function extremely critical ({total_usage} times); "
             f"affects {dependency_count} dependent files"
            ),
            usages
        )

   
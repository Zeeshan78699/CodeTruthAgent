import shutil
import re
import os


def create_backup(file_path):
    """
    Create backup before modification.
    Existing functionality preserved.
    """
    backup_path = file_path + ".bak"
    shutil.copy(file_path, backup_path)
    return backup_path


def should_skip_path(file_path):
    """
    Skip unsafe/non-project folders during cross-file refactor.
    """
    normalized = file_path.replace("\\", "/").lower()

    skip_patterns = [
        "/.venv/",
        "/__pycache__/",
        "/.git/",
        "/.idea/",
        "/.vscode/"
    ]

    return any(pattern in normalized for pattern in skip_patterns)


def replace_function_calls(file_path, old_func, new_func):
    """
    Replace all calls of old_func() with new_func() in one file.
    Existing functionality preserved.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        code = file.read()

    updated_code = re.sub(
        rf"\b{re.escape(old_func)}\(",
        f"{new_func}(",
        code
    )

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(updated_code)


def replace_import_references(file_path, old_func, new_func):
    """
    Replace import references safely.

    Example:
    from helpers import format_name
    becomes:
    from helpers import format_name
    """
    with open(file_path, "r", encoding="utf-8") as file:
        code = file.read()

    updated_code = re.sub(
        rf"\b{re.escape(old_func)}\b",
        new_func,
        code
    )

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(updated_code)


def replace_function_calls_across_project(project_path, old_func, new_func):
    """
    Cross-file orchestration.

    Scans all project .py files and replaces:
    - function calls
    - import references

    Creates backup only for files that are actually changed.
    """

    changed_files = []

    for root, dirs, files in os.walk(project_path):

        dirs[:] = [
            d for d in dirs
            if d not in [".venv", "__pycache__", ".git", ".idea", ".vscode"]
        ]

        for file in files:

            if not file.endswith(".py"):
                continue

            file_path = os.path.join(root, file)

            if should_skip_path(file_path):
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    original_code = f.read()

                updated_code = re.sub(
                    rf"\b{re.escape(old_func)}\(",
                    f"{new_func}(",
                    original_code
                )

                updated_code = re.sub(
                    rf"\b{re.escape(old_func)}\b",
                    new_func,
                    updated_code
                )

                if updated_code != original_code:
                    create_backup(file_path)

                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(updated_code)

                    changed_files.append(file_path)

            except Exception:
                continue

    return changed_files


def remove_function_definition(file_path, function_name):
    """
    Remove duplicate function definition safely
    without breaking neighboring functions.

    Existing functionality preserved.
    """

    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    new_lines = []
    inside_function = False

    for line in lines:

        if line.startswith(f"def {function_name}("):
            inside_function = True
            continue

        if inside_function:

            if line.startswith("def "):
                inside_function = False
                new_lines.append(line)
                continue

            continue

        new_lines.append(line)

    with open(file_path, "w", encoding="utf-8") as file:
        file.writelines(new_lines)


def apply_safe_merge(file_path, remove_func, keep_func):
    """
    Full safe modification pipeline.

    Existing behavior preserved:
    - backup original source file
    - remove duplicate function definition

    New extension:
    - update calls/imports across project
    """

    backup = create_backup(file_path)

    remove_function_definition(
        file_path,
        remove_func
    )

    replace_function_calls_across_project(
        ".",
        remove_func,
        keep_func
    )

    return backup
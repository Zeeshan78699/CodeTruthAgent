import os


EXCLUDED_FILES = {
    "main.py",
    "run_uat.py",
    "run_uat_per_case.py",
    "uat_test_cases.py",
}

EXCLUDED_DIRS = {
    ".venv",
    "__pycache__",
    ".git",
    ".idea",
    ".vscode",
}


def get_python_files(project_path):
    """
    Recursively find all Python files in a project folder.

    Excludes:
    - Virtual environments (.venv)
    - Cache folders (__pycache__)
    - Git folders (.git)
    - IDE folders (.idea, .vscode)
    - Hidden/system folders
    - Engine and test runner files
    """

    python_files = []

    for root, dirs, files in os.walk(project_path):

        # Exclude unwanted directories
        dirs[:] = [
            d for d in dirs
            if d not in EXCLUDED_DIRS
            and not d.startswith(".")
        ]

        # Find Python files
        for file in files:
            if file.endswith(".py"):

                # Skip excluded files
                if file in EXCLUDED_FILES:
                    continue

                full_path = os.path.join(root, file)
                python_files.append(full_path)

    return python_files
import os

ROOT = r"C:\AI_Project\CodeTruthAgent"

EXCLUDE_FOLDERS = {
    ".venv",
    "__pycache__",
    ".git",
    ".pytest_cache",
    "site-packages",
    "node_modules",
    "dist",
    "build",
    ".mypy_cache",
    ".idea",
    ".vscode"
}

OUTPUT_FILE = "PROJECT_STRUCTURE.txt"

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:

    for root, dirs, files in os.walk(ROOT):

        # Remove excluded folders
        dirs[:] = [d for d in dirs if d not in EXCLUDE_FOLDERS]

        level = root.replace(ROOT, "").count(os.sep)

        indent = "│   " * level

        folder_name = os.path.basename(root)

        f.write(f"{indent}📂 {folder_name}\n")

        subindent = "│   " * (level + 1)

        for file in files:

            # Skip compiled/cache files
            if file.endswith((".pyc", ".pyo")):
                continue

            f.write(f"{subindent}📄 {file}\n")

print(f"\nProject structure saved to: {OUTPUT_FILE}")
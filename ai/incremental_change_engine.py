import hashlib
import json
import os


SNAPSHOT_FILE = "repository_snapshot.json"


def calculate_file_hash(file_path):
    """
    Generate deterministic file hash.
    """

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:

        while chunk := file.read(4096):
            sha256.update(chunk)

    return sha256.hexdigest()


def should_skip_path(file_path):
    """
    Skip unsafe/non-project folders.
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


def build_repository_snapshot(project_path):
    """
    Build repository hash snapshot.
    """

    snapshot = {}

    for root, dirs, files in os.walk(project_path):

        dirs[:] = [
            d for d in dirs
            if d not in [
                ".venv",
                "__pycache__",
                ".git",
                ".idea",
                ".vscode"
            ]
        ]

        for file in files:

            if not file.endswith(".py"):
                continue

            file_path = os.path.abspath(
                os.path.join(root, file)
            )

            if should_skip_path(file_path):
                continue

            try:

                snapshot[file_path] = calculate_file_hash(file_path)

            except Exception:
                continue

    return snapshot


def save_snapshot(snapshot):
    """
    Persist repository snapshot.
    """

    with open(SNAPSHOT_FILE, "w", encoding="utf-8") as file:
        json.dump(snapshot, file, indent=4)


def load_snapshot():
    """
    Load previous repository snapshot.
    """

    if not os.path.exists(SNAPSHOT_FILE):
        return {}

    with open(SNAPSHOT_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def detect_incremental_changes(project_path):
    """
    Detect changed repository files.
    """

    previous_snapshot = load_snapshot()
    
    previous_snapshot = {
        os.path.abspath(path): value
        for path, value in previous_snapshot.items()
    }

    current_snapshot = build_repository_snapshot(project_path)

    changed_files = []

    for file_path, current_hash in current_snapshot.items():

        previous_hash = previous_snapshot.get(file_path)

        if previous_hash != current_hash:

            changed_files.append({
                "file_path": file_path,
                "change_type": "MODIFIED_OR_NEW"
            })

    deleted_files = []

    for file_path in previous_snapshot:

        if file_path not in current_snapshot:

            deleted_files.append({
                "file_path": file_path,
                "change_type": "DELETED"
            })

    save_snapshot(current_snapshot)

    return {
        "changed_files": changed_files,
        "deleted_files": deleted_files,
        "total_changed": len(changed_files),
        "total_deleted": len(deleted_files)
    }


def get_changed_python_files(project_path):
    """
    Lightweight helper for orchestration.
    """

    result = detect_incremental_changes(project_path)

    return [
        entry["file_path"]
        for entry in result["changed_files"]
    ]
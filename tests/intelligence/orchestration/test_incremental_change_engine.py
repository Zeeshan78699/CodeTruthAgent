from ai.incremental_change_engine import (
    detect_incremental_changes,
    get_changed_python_files
)


PROJECT_PATH = "."


print("\n=== TEST 1 — FIRST SNAPSHOT ===")

result_1 = detect_incremental_changes(PROJECT_PATH)

print(result_1)


print("\n=== TEST 2 — SECOND RUN (NO CHANGES EXPECTED) ===")

result_2 = detect_incremental_changes(PROJECT_PATH)

print(result_2)


print("\n=== TEST 3 — CHANGED PYTHON FILES ===")

changed_files = get_changed_python_files(PROJECT_PATH)

print(changed_files)
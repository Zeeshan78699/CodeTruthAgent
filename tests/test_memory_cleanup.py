"""
CodeTruth Agent V2
Memory Cleanup Enforcement Tests
"""

import os

from memory.memory_store_v2 import MemoryStoreV2


TEST_MEMORY_FILE = "test_memory_cleanup.json"


def cleanup_test_files():

    if os.path.exists(TEST_MEMORY_FILE):
        os.remove(TEST_MEMORY_FILE)


def test_memory_cleanup_enforcement():

    cleanup_test_files()

    memory_store = MemoryStoreV2(
        memory_file=TEST_MEMORY_FILE
    )

    # ===================================================
    # INSERT MANY DECISIONS
    # ===================================================

    for index in range(120):

        memory_store.store_approved_decision(
            {
                "decision": f"decision_{index}",
                "risk_level": "LOW"
            }
        )

    memory_data = memory_store.get_memory()

    # ===================================================
    # VERIFY CLEANUP LIMIT
    # ===================================================

    assert (
        len(memory_data["approved_decisions"])
        <= memory_store.max_approved_decisions
    )

    # ===================================================
    # VERIFY CLEANUP EVENT EXISTS
    # ===================================================

    assert (
        len(memory_data["cleanup_events"])
        >= 1
    )

    # ===================================================
    # VERIFY MEMORY STILL WORKS
    # ===================================================

    result = memory_store.store_approved_decision(
        {
            "decision": "final_decision",
            "risk_level": "LOW"
        }
    )

    assert result["success"] is True

    cleanup_test_files()


def test_manual_cleanup_execution():

    cleanup_test_files()

    memory_store = MemoryStoreV2(
        memory_file=TEST_MEMORY_FILE
    )

    result = memory_store.enforce_cleanup()

    assert result["success"] is True

    assert (
        "memory"
        in result
    )

    cleanup_test_files()
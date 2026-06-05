from validation.approval_engine import request_approval
from ai.fallback_orchestrator import route_to_v1


def fake_v1_handler(finding):
    return {
        "v1_status": "SAFE_V1_EXECUTION"
    }


# TEST 1 — REVIEW approval
review_finding = {
    "file_path": "demo.py",
    "function_name": "run_process",
    "severity": "REVIEW",
    "category": "PROCESS_OPERATION"
}

review_result = request_approval(review_finding)

print("\n=== TEST 1 — REVIEW ===")
print(review_result)


# TEST 2 — BLOCK rejection
block_finding = {
    "file_path": "danger.py",
    "function_name": "execute_eval",
    "severity": "BLOCK",
    "category": "DYNAMIC_EXEC"
}

block_result = request_approval(block_finding)

print("\n=== TEST 2 — BLOCK ===")
print(block_result)


# TEST 3 — SAFE approval
safe_finding = {
    "file_path": "safe.py",
    "function_name": "format_name",
    "severity": "SAFE",
    "category": "UTILITY"
}

safe_result = request_approval(safe_finding)

print("\n=== TEST 3 — SAFE ===")
print(safe_result)


# TEST 4 — fallback triggered
fallback_result = route_to_v1(
    finding=review_finding,
    confidence_score=0.30,
    v1_handler=fake_v1_handler
)

print("\n=== TEST 4 — FALLBACK ===")
print(fallback_result)


# TEST 5 — no fallback
no_fallback_result = route_to_v1(
    finding=review_finding,
    confidence_score=0.95
)

print("\n=== TEST 5 — NO FALLBACK ===")
print(no_fallback_result)
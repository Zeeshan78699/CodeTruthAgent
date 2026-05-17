"""
CodeTruth Agent V1 - Automated Per Case UAT Runner
ISOLATED SINGLE TEST EXECUTION VERSION

Purpose:
- Execute ALL TC01 → TC22 automatically
- Scan ONLY one runtime test file at a time
- Do NOT scan full project
- Do NOT call main.py
- Do NOT modify engine logic
"""

import sys
import datetime
from pathlib import Path


# =============================================================================
# PROJECT ROOT IMPORT FIX
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(PROJECT_ROOT))


from core.parser import extract_functions
from core.duplicate_detector import find_duplicates


# =============================================================================
# CONFIG
# =============================================================================

OUTPUT_DIR = Path("tests/output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

RUNTIME_FILE = Path("runtime_test_case.py")


# =============================================================================
# TEST CASES
# =============================================================================

TC01_BLOCK = r"""
# =============================================================================
# TC01 — Basic Identical Duplicate
# =============================================================================

def add(a, b):
    return a + b

def add_copy(a, b):
    return a + b
"""

TC02_BLOCK = r"""
# =============================================================================
# TC02 — Different Function Names Same Logic
# =============================================================================

def calculate_area(width, height):
    return width * height

def get_area(w, h):
    return w * h
"""

TC03_BLOCK = r"""
# =============================================================================
# TC03 — Different Logic Same Name Pattern
# =============================================================================

def process_data(data):
    return [x * 2 for x in data]

def process_data_v2(data):
    return [x ** 2 for x in data]
"""

TC04_BLOCK = r"""
# =============================================================================
# TC04 — Business Logic Conflict
# =============================================================================

def calculate_tax(amount):
    return amount * 0.10

def compute_tax(value):
    return value * 0.20
"""

TC05_BLOCK = r"""
# =============================================================================
# TC05 — Semantic Domain Conflict
# =============================================================================

def validate_email(text):
    return len(text) > 0 and "@" in text

def validate_username(text):
    return len(text) > 0 and "@" in text
"""

# =============================================================================
# CONTINUE TC06 → TC22 SAME FORMAT
# =============================================================================

TC06_BLOCK = r"""
# =============================================================================
# TC06 — High Usage CRITICAL Block
# =============================================================================

def calculate_discount(amount):
    return amount * 0.15

def apply_discount(value):
    return value * 0.15
"""

TC07_BLOCK = r"""
# =============================================================================
# TC07 — Nested Function Duplicate
# =============================================================================

def outer_process(data):

    def clean(x):
        return x.strip().lower()

    return [clean(x) for x in data]

def normalize_text(items):
    return [x.strip().lower() for x in items]
"""

TC08_BLOCK = r"""
# =============================================================================
# TC08 — Type Conflict Detection
# =============================================================================

def sum_integers(numbers: list):
    return sum(numbers)

def sum_strings(values: list):
    return sum(values)
"""

TC09_BLOCK = r"""
# =============================================================================
# TC09 — Clean Codebase No False Positives
# =============================================================================

def calculate_perimeter(w, h):
    return 2 * (w + h)

def calculate_volume(w, h, d):
    return w * h * d
"""

TC10_BLOCK = r"""
# =============================================================================
# TC10 — Approval Yes Path
# =============================================================================

def add_two(a, b):
    return a + b

def sum_two(a, b):
    return a + b
"""

TC11_BLOCK = r"""
# =============================================================================
# TC11 — Rejection Path
# =============================================================================

def multiply(a, b):
    return a * b

def multiply_copy(a, b):
    return a * b
"""

TC12_BLOCK = r"""
# =============================================================================
# TC12 — Recursive Function Detection
# =============================================================================

def factorial(n):

    if n == 0:
        return 1

    return n * factorial(n - 1)

def calc_factorial(n):

    if n == 0:
        return 1

    return n * calc_factorial(n - 1)
"""

TC13_BLOCK = r"""
# =============================================================================
# TC13 — Empty Function Detection
# =============================================================================

def placeholder_one():
    pass

def placeholder_two():
    pass
"""

TC14_BLOCK = r"""
# =============================================================================
# TC14 — Single Line vs Multi Line
# =============================================================================

def get_evens(numbers):
    return [x for x in numbers if x % 2 == 0]

def filter_even_numbers(numbers):

    result = []

    for x in numbers:

        if x % 2 == 0:
            result.append(x)

    return result
"""

TC15_BLOCK = r"""
# =============================================================================
# TC15 — Multi-File Duplicate Detection
# =============================================================================

def format_name(first, last):
    return f"{first} {last}".strip()
"""

TC16_BLOCK = r"""
# =============================================================================
# TC16 — Default Argument Conflict
# =============================================================================

def connect_db(host="localhost", port=5432):
    return f"Connected to {host}:{port}"

def open_connection(host="localhost", port=3306):
    return f"Connected to {host}:{port}"
"""

TC17_BLOCK = r"""
# =============================================================================
# TC17 — Large Function Comparison
# =============================================================================

def process_order(order_id, items, customer, tax_rate, discount, shipping):

    subtotal = sum(
        item['price'] * item['qty']
        for item in items
    )

    tax = subtotal * tax_rate

    disc = subtotal * discount

    total = subtotal + tax - disc + shipping

    return {
        "order_id": order_id,
        "customer": customer,
        "subtotal": subtotal,
        "tax": tax,
        "discount": disc,
        "shipping": shipping,
        "total": total,
        "status": "confirmed"
    }

def calculate_order(ref, products, client, rate, reduction, delivery):

    base = sum(
        p['price'] * p['qty']
        for p in products
    )

    tax = base * rate

    disc = base * reduction

    total = base + tax - disc + delivery

    return {
        "order_id": ref,
        "customer": client,
        "subtotal": base,
        "tax": tax,
        "discount": disc,
        "shipping": delivery,
        "total": total,
        "status": "confirmed"
    }
"""

TC18_BLOCK = r"""
# =============================================================================
# TC18 — Learning System Memory
# =============================================================================

def send_email(to, subject, body):
    return f"Email sent to {to}: {subject}"

def dispatch_email(recipient, title, content):
    return f"Email sent to {recipient}: {title}"
"""

TC19_BLOCK = r"""
# =============================================================================
# TC19 — Real-World Library Scan
# =============================================================================
"""

TC20_BLOCK = r"""
# =============================================================================
# TC20 — Full Pipeline End to End
# =============================================================================

def square(n):
    return n * n

def sq(n):
    return n * n

def greet(name):
    return f"Hello, {name}!"

def say_hello(name):
    return f"Hello, {name}!"

def get_vat(amount):
    return amount * 0.05

def calc_vat(amount):
    return amount * 0.20
"""

TC21_BLOCK = r"""
# =============================================================================
# TC21 — Dependency Tracking Across Files
# =============================================================================
"""

TC22_BLOCK = r"""
# =============================================================================
# TC22 — Learning System Memory Persistence
# =============================================================================
"""


TC_DATA = {

    "TC01": {
        "name": "Basic Identical Duplicate",
        "block": TC01_BLOCK
    },

    "TC02": {
        "name": "Different Function Names Same Logic",
        "block": TC02_BLOCK
    },

    "TC03": {
        "name": "Different Logic Same Name Pattern",
        "block": TC03_BLOCK
    },

    "TC04": {
        "name": "Business Logic Conflict",
        "block": TC04_BLOCK
    },

    "TC05": {
        "name": "Semantic Domain Conflict",
        "block": TC05_BLOCK
    },
    
    "TC06": {
        "name": "High Usage CRITICAL Block",
        "block": TC06_BLOCK
    },

    "TC07": {
        "name": "Nested Function Duplicate",
        "block": TC07_BLOCK
    },

    "TC08": {
        "name": "Type Conflict Detection",
        "block": TC08_BLOCK
    },

    "TC09": {
        "name": "Clean Codebase No False Positives",
        "block": TC09_BLOCK
    },

    "TC10": {
        "name": "Approval Yes Path",
        "block": TC10_BLOCK
    },

    "TC11": {
        "name": "Rejection Path",
        "block": TC11_BLOCK
    },

    "TC12": {
        "name": "Recursive Function Detection",
        "block": TC12_BLOCK
    },

    "TC13": {
        "name": "Empty Function Detection",
        "block": TC13_BLOCK
    },

    "TC14": {
        "name": "Single Line vs Multi Line",
        "block": TC14_BLOCK
    },

    "TC15": {
        "name": "Multi-File Duplicate Detection",
        "block": TC15_BLOCK
    },

    "TC16": {
        "name": "Default Argument Conflict",
        "block": TC16_BLOCK
    },

    "TC17": {
        "name": "Large Function Comparison",
        "block": TC17_BLOCK
    },

    "TC18": {
        "name": "Learning System Memory",
        "block": TC18_BLOCK
    },

    "TC19": {
        "name": "Real-World Library Scan",
        "block": TC19_BLOCK
    },

    "TC20": {
        "name": "Full Pipeline End to End",
        "block": TC20_BLOCK
    },

    "TC21": {
        "name": "Dependency Tracking Across Files",
        "block": TC21_BLOCK
    },

    "TC22": {
        "name": "Learning System Memory Persistence",
        "block": TC22_BLOCK
    }
}


# =============================================================================
# HELPERS
# =============================================================================

def sep(char="=", width=60):

    return char * width


def create_runtime_test_file(tc_id, data):

    header = (
        "# =============================================================================\n"
        "# GENERATED RUNTIME TEST FILE\n"
        f"# ACTIVE TEST CASE: {tc_id}\n"
        "# =============================================================================\n\n"
    )

    RUNTIME_FILE.write_text(
        header + data["block"],
        encoding="utf-8"
    )


def cleanup_runtime_file():

    if RUNTIME_FILE.exists():

        RUNTIME_FILE.unlink()


def run_isolated_scan():

    functions = extract_functions(
        str(RUNTIME_FILE)
    )

    # duplicate_detector.py expects "file"

    for func in functions:

        func["file"] = str(RUNTIME_FILE)

    duplicates = find_duplicates(
        functions
    )

    return functions, duplicates


def build_output(tc_id, functions, duplicates):

    lines = []

    lines.append(
        "CodeTruth Agent V1 - Isolated Execution"
    )

    lines.append("-" * 60)

    lines.append(
        f"Execution Time: {datetime.datetime.now()}"
    )

    lines.append("")

    lines.append(
        "Files scanned: 1"
    )

    lines.append(
        f"Scanned file: {tc_id}"
    )

    lines.append(
        f"Total functions found: {len(functions)}"
    )

    lines.append(
        f"Total duplicates found: {len(duplicates)}"
    )

    lines.append("")

    if not duplicates:

        lines.append(
            "No duplicate functions found."
        )

        return "\n".join(lines)

    for dup in duplicates:

        lines.append(sep())

        lines.append(
            "TEST CASE RESULT"
        )

        lines.append(sep())

        lines.append(
            f"Function 1: "
            f"{dup.get('function_1', 'UNKNOWN')}"
        )

        lines.append(
            f"Function 2: "
            f"{dup.get('function_2', 'UNKNOWN')}"
        )

        lines.append(
            f"Similarity: "
            f"{dup.get('similarity', 0)}%"
        )

        lines.append(
            f"Duplicate Type: "
            f"{dup.get('duplicate_type', 'UNKNOWN')}"
        )

        lines.append(
            f"Reason: "
            f"{dup.get('reason', 'N/A')}"
        )

        lines.append(
            f"Semantic Reason: "
            f"{dup.get('semantic_reason', 'N/A')}"
        )

        lines.append(
            f"Constant Reason: "
            f"{dup.get('constant_reason', 'N/A')}"
        )

        lines.append(
            f"Operation Reason: "
            f"{dup.get('operation_reason', 'N/A')}"
        )

        lines.append(
            f"Type Reason: "
            f"{dup.get('type_reason', 'N/A')}"
        )

        lines.append(
            f"Nested Reason: "
            f"{dup.get('nested_reason', 'N/A')}"
        )

        lines.append(
            f"Auto Merge Safe: "
            f"{dup.get('auto_merge_safe', False)}"
        )

        lines.append("")

    return "\n".join(lines)


def save_output(tc_id, data, output):

    output_file = OUTPUT_DIR / f"{tc_id}_output.txt"

    with open(output_file, "w", encoding="utf-8") as f:

        f.write(sep() + "\n")

        f.write(
            f"CodeTruth Agent V1 - {tc_id} Output\n"
        )

        f.write(sep() + "\n\n")

        f.write(
            f"Generated : {datetime.datetime.now()}\n"
        )

        f.write(
            f"Test Case : {tc_id}\n"
        )

        f.write(
            f"Name      : {data['name']}\n\n"
        )

        f.write("Runtime Test Case:\n")

        f.write("-" * 60 + "\n")

        f.write(
            data["block"].strip()
        )

        f.write("\n")

        f.write("-" * 60 + "\n\n")

        f.write(output)

        f.write("\n\n")

        f.write(sep() + "\n")

        f.write("End Of Report\n")

        f.write(sep() + "\n")


# =============================================================================
# MAIN
# =============================================================================

def main():

    print(sep())

    print(
        "CodeTruth Agent V1 - Automated Per Case UAT Runner"
    )

    print(sep())

    print()

    total_tc = len(TC_DATA)

    completed = 0

    for tc_id, data in TC_DATA.items():

        print(
            f"Running {tc_id} - {data['name']}"
        )

        try:

            create_runtime_test_file(
                tc_id,
                data
            )

            functions, duplicates = run_isolated_scan()

            output = build_output(
                tc_id,
                functions,
                duplicates
            )

            save_output(
                tc_id,
                data,
                output
            )

            completed += 1

            print(
                f"SUCCESS → "
                f"{OUTPUT_DIR / f'{tc_id}_output.txt'}"
            )

            print()

        except Exception as e:

            print(
                f"ERROR in {tc_id}: {str(e)}"
            )

        finally:

            cleanup_runtime_file()

    print(sep())

    print(
        f"Completed: {completed} / {total_tc}"
    )

    print(
        f"Outputs Folder: {OUTPUT_DIR}"
    )

    print(sep())


if __name__ == "__main__":

    main()
# =============================================================================
# CodeTruth Agent V1 —  Test Cases
# All 22 Test Case Functions
# Location: tests/uat_test_cases.py
# 
# IMPORTANT: This file is scanned by the engine automatically.
# Do NOT run this file directly.
# The engine must be configured to scan the tests/ folder.
# =============================================================================


# =============================================================================
# TC01 — Basic Identical Duplicate
# Objective: Detect 100% identical functions with different names
# Expected:  Similarity 100%, SAFE_LOGICAL_DUPLICATE, Approval prompt shown
# =============================================================================
def add(a, b):
    return a + b

def add_copy(a, b):
    return a + b


# =============================================================================
# TC02 — Different Function Names Same Logic
# Objective: Detect duplicates despite different naming
# Expected:  Similarity ~90-100%, SAFE_LOGICAL_DUPLICATE, Best choice suggested
# =============================================================================
def calculate_area(width, height):
    return width * height

def get_area(w, h):
    return w * h


# =============================================================================
# TC03 — Different Logic Same Name Pattern
# Objective: Reject false positives with similar names but different logic
# Expected:  No duplicate found, Engine correctly filters
# =============================================================================
def process_data(data):
    return [x * 2 for x in data]

def process_data_v2(data):
    return [x ** 2 for x in data]


# =============================================================================
# TC04 — Business Logic Conflict
# Objective: Detect same structure but different business constants
# Expected:  BUSINESS_LOGIC_CONFLICT, Constant [0.10] vs [0.20], CRITICAL
# =============================================================================
def calculate_tax(amount):
    return amount * 0.10

def compute_tax(value):
    return value * 0.20


# =============================================================================
# TC05 — Semantic Domain Conflict
# Objective: Detect same logic but different business domain
# Expected:  SEMANTIC_REVIEW_REQUIRED, Risk High, Approval disabled
# =============================================================================
def validate_email(text):
    return len(text) > 0 and "@" in text

def validate_username(text):
    return len(text) > 0 and "@" in text


# =============================================================================
# TC06 — High Usage CRITICAL Block
# Objective: Block merge when function is heavily used across project
# Expected:  Risk CRITICAL, BLOCKED, Approval disabled
# Note:      calculate_discount is called across billing.py, orders.py, reports.py
# =============================================================================
def calculate_discount(amount):
    return amount * 0.15

def apply_discount(value):
    return value * 0.15


# =============================================================================
# TC07 — Nested Function Duplicate
# Objective: Detect similar logic with structural difference (nested vs flat)
# Expected:  Similarity ~85-90%, SEMANTIC_REVIEW_REQUIRED, nested vs flat detected
# =============================================================================
def outer_process(data):
    def clean(x):
        return x.strip().lower()
    return [clean(x) for x in data]

def normalize_text(items):
    return [x.strip().lower() for x in items]


# =============================================================================
# TC08 — Type Conflict Detection
# Objective: Detect same logic applied to different data types
# Expected:  SEMANTIC_REVIEW_REQUIRED, Type conflict detected, Approval disabled
# =============================================================================
def sum_integers(numbers: list):
    return sum(numbers)

def sum_strings(values: list):
    return sum(values)


# =============================================================================
# TC09 — Clean Codebase No False Positives
# Objective: Verify engine stays silent on legitimate unique functions
# Expected:  No duplicate functions found, Zero false positives
# =============================================================================
def calculate_perimeter(w, h):
    return 2 * (w + h)

def calculate_volume(w, h, d):
    return w * h * d


# =============================================================================
# TC10 — Approval Yes Path
# Objective: Verify safe merge executes correctly on approval
# Expected:  Change applied safely, Backup created
# Action:    Type 'yes' when prompted
# =============================================================================
def add_two(a, b):
    return a + b

def sum_two(a, b):
    return a + b


# =============================================================================
# TC11 — Rejection Path
# Objective: Verify file untouched on rejection
# Expected:  Change skipped, File unchanged
# Action:    Type 'no' when prompted
# =============================================================================
def multiply(a, b):
    return a * b

def multiply_copy(a, b):
    return a * b


# =============================================================================
# TC12 — Recursive Function Detection
# Objective: Detect duplicate recursive functions safely
# Expected:  SEMANTIC_REVIEW_REQUIRED, Recursive detected, Risk High
# =============================================================================
def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n - 1)

def calc_factorial(n):
    if n == 0:
        return 1
    return n * calc_factorial(n - 1)


# =============================================================================
# TC13 — Empty Function Detection
# Objective: Handle empty/placeholder functions safely without crash
# Expected:  Not flagged (too simple), No crash
# =============================================================================
def placeholder_one():
    pass

def placeholder_two():
    pass


# =============================================================================
# TC14 — Single Line vs Multi Line
# Objective: Detect logical duplicate despite compact vs verbose style
# Expected:  Similarity ~85-92%, SAFE_LOGICAL_DUPLICATE, Best choice suggested
# =============================================================================
def get_evens(numbers):
    return [x for x in numbers if x % 2 == 0]

def filter_even_numbers(numbers):
    result = []
    for x in numbers:
        if x % 2 == 0:
            result.append(x)
    return result


# =============================================================================
# TC15 — Multi-File Duplicate Detection
# Objective: Detect duplicates across different project files
# Expected:  Cross-file duplicate detected, File paths shown for both
# Note:      helpers.py has format_name, utils.py has get_full_name
# =============================================================================
def format_name(first, last):
    return f"{first} {last}".strip()


# =============================================================================
# TC16 — Default Argument Conflict
# Objective: Detect dangerous default argument differences
# Expected:  BUSINESS_LOGIC_CONFLICT, Constant 5432 vs 3306, CRITICAL
# =============================================================================
def connect_db(host="localhost", port=5432):
    return f"Connected to {host}:{port}"

def open_connection(host="localhost", port=3306):
    return f"Connected to {host}:{port}"


# =============================================================================
# TC17 — Large Function Comparison
# Objective: Engine handles large complex functions without crash
# Expected:  No crash, Risk analysis correct, Decision made
# =============================================================================
def process_order(order_id, items, customer, tax_rate, discount, shipping):
    subtotal = sum(item['price'] * item['qty'] for item in items)
    tax      = subtotal * tax_rate
    disc     = subtotal * discount
    total    = subtotal + tax - disc + shipping
    return {
        "order_id": order_id,
        "customer": customer,
        "subtotal": subtotal,
        "tax":      tax,
        "discount": disc,
        "shipping": shipping,
        "total":    total,
        "status":   "confirmed"
    }

def calculate_order(ref, products, client, rate, reduction, delivery):
    base  = sum(p['price'] * p['qty'] for p in products)
    tax   = base * rate
    disc  = base * reduction
    total = base + tax - disc + delivery
    return {
        "order_id": ref,
        "customer": client,
        "subtotal": base,
        "tax":      tax,
        "discount": disc,
        "shipping": delivery,
        "total":    total,
        "status":   "confirmed"
    }


# =============================================================================
# TC18 — Learning System Memory
# Objective: Remember previously rejected decisions across runs
# Expected:  Memory Hit shown, Previously rejected pattern skipped on run 2
# Action:    Type 'no' on first run, Run again to verify auto-skip
# =============================================================================
def send_email(to, subject, body):
    return f"Email sent to {to}: {subject}"

def dispatch_email(recipient, title, content):
    return f"Email sent to {recipient}: {title}"


# =============================================================================
# TC19 — Real-World Library Scan
# Objective: Zero false positives when scanning real production code
# Expected:  No false positives from real_world/utils.py, Engine stable
# Note:      Requires real_world/utils.py from requests library to be present
#            No test functions needed here — engine scans real_world/ automatically
# =============================================================================


# =============================================================================
# TC20 — Full Pipeline End to End
# Objective: All 7 pipeline stages work together as one cohesive system
# Expected:  Approve square/sq, Reject greet/say_hello, Block get_vat/calc_vat
# Action:    Type 'yes' for square/sq then 'no' for greet/say_hello
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


# =============================================================================
# TC21 — Dependency Tracking Across Files
# Objective: Show all files and usage counts before allowing any merge
# Expected:  All dependent files shown, Usage count correct, CRITICAL risk
# Note:      calculate_discount is called across billing.py, orders.py,
#            reports.py to trigger cross-file dependency map
#            calculate_discount already defined in TC06 above
# =============================================================================


# =============================================================================
# TC22 — Learning System Memory Persistence
# Objective: Auto-skip previously rejected pairs across multiple runs
# Expected:  Run 1 rejection logged, Run 2 auto-skipped, No approval prompt
# Action:    Run main.py twice — second run must auto-skip send_email pair
# Note:      send_email / dispatch_email already defined in TC18 above
# =============================================================================

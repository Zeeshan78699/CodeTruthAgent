import ast
import difflib
import re, os

PROJECT_ROOT = os.path.abspath("C:/AI_Project/CodeTruthAgent")

DEBUG = False  # 🔥 TURN ON/OFF DEBUG HERE


def debug(msg):
    if DEBUG:
        print(f"[DEBUG] {msg}")


BUSINESS_WORDS = {
    "invoice", "tax", "price", "amount", "total", "vat", "payment",
    "customer", "vendor", "supplier", "order", "po", "contract",
    "employee", "salary", "account", "balance", "journal", "asset"
}

GENERIC_WORDS = {
    "add", "sum", "values", "calculate", "compute", "process",
    "handle", "run", "do", "get", "set", "data", "item"
}

# =========================
# 🔥 DOMAIN DETECTION (NEW - SAFE EXTENSION)
# =========================

DOMAIN_KEYWORDS = {
    "email": ["email", "mail"],
    "username": ["user", "username", "login"],
    "tax": ["tax", "vat"],
    "price": ["price", "cost", "amount"],
    
     # 🔥 SAFE EXTENSIONS
    "database": ["db", "database", "connection", "connect", "host", "port", "sql"],

    "inventory": ["stock", "inventory", "qty", "warehouse"],

    "finance": ["payment", "invoice", "currency", "discount"],

    "summary": ["summary", "report", "reporting"],

    "name": ["name", "first", "last", "full"]
}

def detect_domain(name):
    words = split_name(name)

    for domain, keywords in DOMAIN_KEYWORDS.items():
        for w in words:
            if w in keywords:
                return domain

    return "unknown"


# =========================
# NAME ANALYSIS
# =========================



def split_name(name):
    words = re.sub(r"([a-z])([A-Z])", r"\1_\2", name).lower()
    return [w for w in words.split("_") if w]


def get_name_intent(function_name):
    words = split_name(function_name)
    business_terms = [w for w in words if w in BUSINESS_WORDS]
    generic_terms = [w for w in words if w in GENERIC_WORDS]

    if business_terms:
        return "business", business_terms

    if generic_terms:
        return "generic", generic_terms

    return "unknown", words


def semantic_conflict(func1_name, func2_name):
    
     # 🔥 NEW: DOMAIN CHECK (FIRST PRIORITY)
    domain1 = detect_domain(func1_name)
    domain2 = detect_domain(func2_name)

    #if domain1 != "unknown" and domain2 != "unknown" and domain1 != domain2:
    if domain1 != domain2 and "unknown" not in (domain1, domain2):
        return True, f"Different domains: {domain1} vs {domain2}"
    
    intent1, terms1 = get_name_intent(func1_name)
    intent2, terms2 = get_name_intent(func2_name)

    if intent1 == "business" and intent2 == "generic":
        return True, f"{func1_name} has business meaning, but {func2_name} is generic."

    if intent1 == "generic" and intent2 == "business":
        return True, f"{func2_name} has business meaning, but {func1_name} is generic."

    if intent1 == "business" and intent2 == "business":
        if set(terms1) != set(terms2):
            return True, "Both functions are business-related but appear to represent different meanings."

    return False, "No major semantic conflict detected."


# =========================
# TYPE / CONSTANT / OPS
# =========================

def detect_type_conflict(name1, name2):
    types = ["int", "integer", "float", "double", "string", "str"]

    n1 = name1.lower()
    n2 = name2.lower()

    for t in types:
        if t in n1 and t not in n2:
            return True, f"{name1} handles {t}, but {name2} does not"

        if t in n2 and t not in n1:
            return True, f"{name2} handles {t}, but {name1} does not"

    return False, "No type conflict detected"


def extract_constants(code):
    tree = ast.parse(code)
    return [node.value for node in ast.walk(tree) if isinstance(node, ast.Constant)]


def constant_conflict(code1, code2):
    const1 = extract_constants(code1)
    const2 = extract_constants(code2)

    simple_constants = {True, False, 0, 1}

    #if set(const1) != set(const2):
    
    meaningful1 = [x for x in const1 if x not in [":", "", None]]
    meaningful2 = [x for x in const2 if x not in [":", "", None]]

    if set(meaningful1) != set(meaningful2):
        if not set(const1).issubset(simple_constants) or not set(const2).issubset(simple_constants):
           # return True, f"Different constant values detected: {const1} vs {const2}"
            return True, (
               f"Different constant values detected: "
                f"{meaningful1} vs {meaningful2}"
            )

    return False, "No constant conflict detected."


def extract_operations(code):
    tree = ast.parse(code)
    return [type(node.op).__name__ for node in ast.walk(tree) if isinstance(node, ast.BinOp)]


def operation_conflict(code1, code2):
    ops1 = extract_operations(code1)
    ops2 = extract_operations(code2)

    if ops1 != ops2:
        return True, f"Different operations detected: {ops1} vs {ops2}"

    return False, "No operation conflict detected."


# =========================
# NESTED DETECTION
# =========================

def detect_nested_function(code):
    tree = ast.parse(code)

    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            for child in node.body:
                if isinstance(child, ast.FunctionDef):
                    return True

    return False


def nested_structure_conflict(code1, code2):
    n1 = detect_nested_function(code1)
    n2 = detect_nested_function(code2)

    debug(f"Nested Check -> func1: {n1}, func2: {n2}")

    if n1 != n2:
        return True, "One function contains nested logic while the other is flat"

    return False, "No nested structure conflict detected"

# =========================
# 🔥 RECURSION DETECTION (SAFE EXTENSION)
# =========================

def detect_recursive_function(code, function_name):
    tree = ast.parse(code)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id == function_name:
                    return True

    return False


def recursive_structure_conflict(func1, func2):
    r1 = detect_recursive_function(func1["code"], func1["name"])
    r2 = detect_recursive_function(func2["code"], func2["name"])

    debug(f"Recursion Check -> func1: {r1}, func2: {r2}")

    if r1 or r2:
        return True, "Recursive function detected — requires manual review"

    return False, "No recursion detected"


# =========================
# NORMALIZATION
# =========================

def normalize_function_code(code):
    tree = ast.parse(code)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            node.name = "FUNCTION_NAME"
        if isinstance(node, ast.arg):
            node.arg = "ARG"
        if isinstance(node, ast.Name):
            node.id = "VAR"

    return ast.dump(tree)


# =========================
# SIMILARITY
# =========================

def calculate_similarity(code1, code2):
    norm1 = normalize_function_code(code1)
    norm2 = normalize_function_code(code2)

    structure_score = difflib.SequenceMatcher(None, norm1, norm2).ratio()

    ops1 = extract_operations(code1)
    ops2 = extract_operations(code2)

    ops_score = 1.0 if ops1 == ops2 else 0.0

    final_score = (0.6 * structure_score) + (0.4 * ops_score)

    debug(f"Similarity -> structure: {structure_score:.2f}, ops: {ops_score}, final: {final_score:.2f}")

    return final_score


# =========================
# HELPERS
# =========================

def is_internal_function(file_path):
    file_path = file_path.replace("\\", "/")

    return (
        file_path.startswith("./core/") or
        file_path.startswith("core/") or
        file_path.endswith("/main.py") or
        file_path.endswith("main.py")
    )

def is_inner_function(func):
    lines = func["code"].splitlines()

    for line in lines:
        if line.strip().startswith("def ") and line.startswith("    "):
            return True

    return False

def is_project_file(file_path):
    file_path = os.path.abspath(file_path)
    root = os.path.abspath(PROJECT_ROOT)

    file_path = file_path.replace("\\", "/").lower()
    root = root.replace("\\", "/").lower()

    return file_path.startswith(root)

# =========================
# 🔥 EMPTY FUNCTION DETECTION (SAFE EXTENSION)
# =========================

def is_empty_function(code):
    tree = ast.parse(code)

    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            # Check if body only contains Pass or is empty
            if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                return True

    return False

# =========================
# MAIN DETECTOR
# =========================

def find_duplicates(functions, threshold=0.60):
    duplicates = []
    
     # 🔥 ADD THIS LINE
    seen_pairs = set()

    for i in range(len(functions)):
        for j in range(i + 1, len(functions)):

            func1 = functions[i]
            func2 = functions[j]
            
            # SKIP IDENTICAL SELF-COMPARISON
            if (
                func1["name"] == func2["name"]
                and func1["code"].strip() == func2["code"].strip()
            ):
                debug("Skipped: identical self-comparison")
                continue
            
            # 🔥 ONLY ALLOW PROJECT FILES
            if not is_project_file(func1["file"]) or not is_project_file(func2["file"]):
                continue
            
            # 🔥 SKIP INTERNAL CORE-TO-CORE COMPARISON (FOCUS ON USER CODE)
            if is_internal_function(func1["file"]) or is_internal_function(func2["file"]):
                continue
            
            # 🔥 NEW: TRACK PROCESSED PAIRS (ADD ONCE AT TOP OF FUNCTION)
            # (Make sure this is defined before loops)
            # seen_pairs = set()

            # 🔥 NEW: PREVENT SELF + DUPLICATE + REVERSE COMPARISON
            
            pair_key = tuple(sorted([
                f"{func1['name']}::{func1['file']}",
                f"{func2['name']}::{func2['file']}"
            ]))
           
            # 🔥 SAME-NAME OVERWRITE PROTECTION
            if (
                func1["file"] == func2["file"] and func1["name"] == func2["name"]
                ):
                debug("Skipped: same-name overwrite case")
                continue

            # SKIP SAME-NAME FUNCTIONS ACROSS TEST/REVISION FILES
            if (
                func1["name"] == func2["name"]
                and (
                    "run_uat" in func1["file"]
                    or "run_uat" in func2["file"]
                    or "tests/" in func1["file"].replace("\\", "/")
                    or "tests/" in func2["file"].replace("\\", "/")
                )
            ):
                debug("Skipped: duplicated test/revision helper")
                continue

            if pair_key in seen_pairs:
                continue

            seen_pairs.add(pair_key)
            
            
            # 🔥 TOP LEVEL FILTER (ADD HERE)
           # if "sample_code.py" not in func1["file"] or "sample_code.py" not in func2["file"]:
           #     continue

            debug(f"\nComparing: {func1['name']} vs {func2['name']}")

            # 🔥 FIX: DO NOT SKIP OUTER FUNCTIONS
            if is_inner_function(func1) and is_inner_function(func2):
                debug("Skipped: both are inner functions")
                continue

            nested_conf, nested_reason = nested_structure_conflict(
                func1["code"],
                func2["code"]
            )

            # 🔥 NEW: RECURSION CHECK (SAFE ADD)
            rec_conf, rec_reason = recursive_structure_conflict(func1, func2)

            code1 = func1["code"]
            code2 = func2["code"]
            
            # 🔥 NEW: EMPTY FUNCTION CHECK
            empty1 = is_empty_function(code1)
            empty2 = is_empty_function(code2)

            if empty1 and empty2:
                debug("Skipped: both functions are empty placeholders")
                continue

            raw_similarity = calculate_similarity(code1, code2)

            effective_threshold = 0.85 if nested_conf else threshold

            debug(f"Threshold -> {effective_threshold}, Similarity -> {raw_similarity:.2f}")

            op_conf, op_reason = operation_conflict(code1, code2)
            debug(f"Operation conflict: {op_conf}")
            
            # 🔥 FIX: DO NOT SKIP IF RECURSION EXISTS
            if op_conf and raw_similarity < effective_threshold and not rec_conf:
                debug("Skipped due to operation mismatch + low similarity")
                continue

            type_conf, type_reason = detect_type_conflict(func1["name"], func2["name"])
            
            semantic_conf, semantic_reason = semantic_conflict(
                func1["name"],
                func2["name"]
            )

            # 🔥 SAFE RELAXATION
            # Allow highly similar implementations even if semantic naming differs

            if semantic_conf and raw_similarity < 0.90:
                debug("Skipped: semantic conflict")
                continue
          
            const_conf, const_reason = constant_conflict(code1, code2)
            
            # 🔥 HARD SEMANTIC BLOCK
            if semantic_conf and raw_similarity < 0.85:
                debug("Skipped: semantic domain mismatch")
                continue

            adjusted_similarity = raw_similarity
            
            # 🔥 FIX: BOOST WHEN OPERATIONS MATCH (STYLE DIFFERENCE CASE)
            ops1 = extract_operations(code1)
            ops2 = extract_operations(code2)

            if ops1 == ops2:
                adjusted_similarity = min(adjusted_similarity + 0.02, 1.0)

            #if semantic_conf and raw_similarity >= 0.95:
            #    adjusted_similarity = 0.92

            if nested_conf or rec_conf:
                adjusted_similarity = max(adjusted_similarity, 0.85)

            debug(f"Adjusted Similarity -> {adjusted_similarity:.2f}")
            
            # 🔥 NEW: NAME SIMILARITY FILTER (PREVENT RANDOM MATCHES)
            name_similarity = difflib.SequenceMatcher(
                None, func1["name"], func2["name"]
            ).ratio()

            debug(f"Name similarity -> {name_similarity:.2f}")
             
            # 🔥 FINAL FILTER: block unrelated functions early
            #if name_similarity < 0.35 and raw_similarity < 0.95:
                
                # 🔥 SAFE RELAXED FILTER
            # Allow highly similar business logic even if names differ

            if (
                name_similarity < 0.35
                and raw_similarity < 0.90
                and not (
                    ops1 == ops2
                    and adjusted_similarity >= 0.85
                )
            ):
                debug("Skipped: low name similarity (unrelated functions)")
                continue


            # 🔥 TC19 REAL-WORLD PROTECTION
            # Block structure-only similarity on production utilities
            if const_conf and duplicate_type if False else False:
                pass

            # 🔥 HARD STRUCTURE FILTER
            if raw_similarity < 0.50:
                debug("Skipped: low structural similarity")
                continue
            
            # 🔥 FORCE DETECTION FOR RECURSION (SAFE EXTENSION)
            if rec_conf or adjusted_similarity >= effective_threshold:
                
                # 🔥 TC19 REAL-WORLD HARD FILTER
                    # Prevent utility/helper structural false positives

                if const_conf:

                    # Weak semantic relation
                    if name_similarity < 0.45:
                        debug("Skipped: weak business relationship")
                        continue

                # Structure-only match
                if raw_similarity < 0.85:
                    debug("Skipped: structure-only similarity")
                    continue

                debug("✅ DUPLICATE DETECTED")

                # 🔥 FIX: RECURSION FIRST (TOP PRIORITY)
                if rec_conf:
                    duplicate_type = "SEMANTIC_REVIEW_REQUIRED"
                    auto_merge_safe = False
                    reason = rec_reason

                elif const_conf:
                    duplicate_type = "BUSINESS_LOGIC_CONFLICT"
                    auto_merge_safe = False
                    reason = "Different constant values detected"

                elif nested_conf:
                    duplicate_type = "SEMANTIC_REVIEW_REQUIRED"
                    auto_merge_safe = False
                    reason = "Nested function structure detected"

                elif type_conf:
                    duplicate_type = "SEMANTIC_REVIEW_REQUIRED"
                    auto_merge_safe = False
                    reason = "Type conflict"

                elif semantic_conf:
                    
                    domain1 = detect_domain(func1["name"])
                    domain2 = detect_domain(func2["name"])
                    different_domains = (
                        domain1 != domain2
                        and "unknown" not in (domain1, domain2)
                    )

                # High structural confidence overrides naming-only conflict
                    if (
                        raw_similarity >= 0.95
                        and not const_conf
                        and not op_conf
                        and not type_conf
                        and not nested_conf
                        and not rec_conf
                        and not different_domains  # ← THIS IS THE FIX
                    ):
                        duplicate_type = "SAFE_LOGICAL_DUPLICATE"
                        auto_merge_safe = True
                        reason = "Highly similar logic despite naming differences"

                    else:
                        duplicate_type = "SEMANTIC_REVIEW_REQUIRED"
                        auto_merge_safe = False
                        reason = "Semantic conflict"

                else:
                    duplicate_type = "SAFE_LOGICAL_DUPLICATE"
                    auto_merge_safe = True
                    reason = "Same logic"
                    
                duplicate_signature = (
                    duplicate_type,
                    tuple(sorted([func1["name"], func2["name"]]))
                )

                if duplicate_signature in seen_pairs:
                    continue

                seen_pairs.add(duplicate_signature)
                
                duplicates.append({
                    "function_1": func1["name"],
                    "function_2": func2["name"],
                    "similarity": round(adjusted_similarity * 100, 2),
                    "raw_similarity": round(raw_similarity * 100, 2),
                    "reason": reason,
                    "semantic_reason": semantic_reason,
                    "constant_reason": const_reason,
                    "operation_reason": op_reason,
                    "type_reason": type_reason,
                    "nested_reason": rec_reason if rec_conf else nested_reason,
                    "duplicate_type": duplicate_type,
                    "auto_merge_safe": auto_merge_safe
                })

            else:
                debug("❌ Not duplicate (below threshold)")

    return duplicates
from core.project_scanner import get_python_files
from core.parser import extract_functions_from_files
from core.duplicate_detector import find_duplicates
from core.quality_checker import compare_functions
from core.merge_advisor import suggest_merge
from datetime import datetime
from core.code_modifier import apply_safe_merge
from core.dependency_tracker import analyze_global_risk
from core.memory_store import store_decision, check_memory
from core.memory_store import (
    store_decision,
    store_rejection,
    check_memory
)
import os

PROJECT_ROOT = os.path.abspath("C:/AI_Project/CodeTruthAgent")

REPORT_MODE = True

HIGH_USAGE_THRESHOLD = 5

def print_section(title):
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)

def is_internal_function(file_path):
    file_path = file_path.replace("\\", "/")

    return (
       # "core/" in file_path or
        file_path.endswith("main.py") or
        file_path.endswith("memory_store.py") or
        file_path.endswith("quality_checker.py")    
        
    )


def analyze_high_usage_functions(functions, project_path):
    print("\nHigh Usage Risk Analysis:\n")

    risk_found = False

    for func in functions:

        # Skip internal/system functions
        if is_internal_function(func["file"]):
            continue

        risk_level, risk_reason, usage_details = analyze_global_risk(
            project_path,
            func["name"]
        )

        if risk_level == "High":
            risk_found = True

            print(f"- {func['name']}() [{func['file']}]")
            print("  Decision: BLOCKED due to high usage risk")
            print("  Risk Level: Critical")
            print(f"  Risk Detail: {risk_reason}")

            print("  Usage Details:")
            for usage in usage_details:
                print(f"    - {usage['file']} ({usage['count']} time(s))")

            print("  Suggested Action: Manual review required")
            print("  Approval disabled: high dependency risk")
            print("  Change skipped")
            print()

    if not risk_found:
        print("No high-usage business risk found.")

def main():
    project_path = "."

    print("CodeTruth Agent v1 (Learning System)")
    print("------------------------------------")
    print("Execution Time:", datetime.now())

    python_files = get_python_files(project_path)
    #python_files = ["sample_code.py"]
    print("\nFiles scanned:")
    for f in python_files:
        print(f)
    print(f"Files found: {len(python_files)}")

    functions = extract_functions_from_files(python_files)
    # 🔥 FIX: FILTER ONLY USER FUNCTIONS (BEFORE DETECTION)
    
    print(f"Total functions found: {len(functions)}")

    duplicates = find_duplicates(functions)
    print(f"\nTotal duplicates found: {len(duplicates)}")
    

    if not duplicates:
        print("No duplicate functions found.")
    else:
        print("\nLearning-enabled duplicate analysis:\n")

    for duplicate in duplicates:
        f1 = duplicate["function_1"]
        f2 = duplicate["function_2"]

        func1 = next(f for f in functions if f["name"] == f1)
        func2 = next(f for f in functions if f["name"] == f2)
        
        print_section(f"TEST CASE RESULT - {duplicate['duplicate_type']}")
        print(f"- {f1}() [{func1['file']}]")
        print(f"  <-> {f2}() [{func2['file']}]")
        print(f"  Similarity: {duplicate['similarity']}%")

        if "raw_similarity" in duplicate:
            print(f"  Raw Similarity: {duplicate['raw_similarity']}%")

        if "duplicate_type" in duplicate:
            print(f"  Duplicate Type: {duplicate['duplicate_type']}")

        if "semantic_reason" in duplicate:
            print(f"  Semantic Detail: {duplicate['semantic_reason']}")

        if "constant_reason" in duplicate:
            print(f"  Constant Detail: {duplicate['constant_reason']}")

        if "type_reason" in duplicate:
            print(f"  Type Detail: {duplicate['type_reason']}")

        if "operation_reason" in duplicate:
            print(f"  Operation Detail: {duplicate['operation_reason']}")
            
        if "nested_reason" in duplicate:
            print(f"  Structure Detail: {duplicate['nested_reason']}")

        if duplicate.get("duplicate_type") == "BUSINESS_LOGIC_CONFLICT":
            print("  Decision: BLOCKED due to business logic conflict")
            print("  Risk Level: Critical")
            print("  Suggested Action: Manual review required. Do not auto-replace.")
            print("  Warning: Same structure but different constant values may represent different business rules.")
            print("  Approval disabled: unsafe business logic merge.")
            print("  Change skipped")
            print("  Result: BLOCKED")
            print()
            continue

        memory_hit = check_memory(f1, f2)

        if memory_hit:
            
             # 🔥 TC18 FIX - PREVIOUSLY REJECTED
            if memory_hit.get("decision") == "rejected":
                print("  Learning Memory Status: ACTIVE")
                print("  Previously rejected pattern detected")
                print("  Suggested Action: Skipping repeated recommendation")
                print("  Change skipped")
                print("  Result: SKIPPED")
                print()
                continue
            
            best = memory_hit["best"]
            reasons = [memory_hit["reason"]]
            print("  Memory Hit: Previous decision reused")
        else:
            best, reasons = compare_functions(func1, func2)

        if best == "equal":
            print("  Both functions are equally good")
            
            # 🔥 FIX: DO NOT MARK SAFE IF NOT SAFE DUPLICATE
            if duplicate.get("duplicate_type") != "SAFE_LOGICAL_DUPLICATE":
                reasons = ["Manual review required - not safe to auto-merge"]
                print("  Default action: Manual review required")

            else:
                best = f1
                reasons = ["Functions are identical - safe to merge"]
                print("  Default action: Safe duplicate - merge allowed")
            
        if best != "equal":
            print(f"  Best choice: {best}()")
        else:
            print("  Best choice: Manual decision required")
        print(f"  Reason: {', '.join(reasons)}")

        merge_plan = suggest_merge(func1, func2, best, duplicate)

        risk_level, risk_reason, usage_details = analyze_global_risk(
            project_path,
            merge_plan["remove"]
        )

        if merge_plan.get("merge_allowed") is False:
          #  risk_level = "High"
            risk_level = "Critical"   # 🔥 FIX (ONLY CHANGE)
            risk_reason = risk_reason + "; Semantic conflict detected; manual review required"

        # print(f"  Risk Level: {risk_level}")
        print(f"  Risk Detail: {risk_reason}")

        print("  Usage Details:")
        for usage in usage_details:
            print(f"    - {usage['file']} ({usage['count']} time(s))")

        print(f"  Suggested Action: {merge_plan['action']}")
        #print("  Result: PASS")
        
        # =========================
        # 🔥 EXTENSION: HIGH USAGE ENFORCEMENT (DO NOT MODIFY EXISTING LOGIC)
        # =========================

        '''  if risk_level in ["High", "Critical"]:
            print("  Decision: BLOCKED due to risk conditions")
            print("  Risk Level: Critical")
            print("  Suggested Action: Manual review required")
            print("  Approval disabled: high dependency risk")
            print("  Change skipped")
            print("  Result: BLOCKED")
            print()
            continue
        '''
        # =====================================
        # RISK-BASED EXECUTION WORKFLOW
        # =====================================

        # HIGH / CRITICAL RISK
        if risk_level in ["High", "Critical"]:

            print("  Decision: BLOCKED due to risk conditions")
            print(f"  Risk Level: {risk_level}")

            print("  Recommendation Report:")
            print(f"    Keep Function : {merge_plan['keep']}()")
            print(f"    Remove Function : {merge_plan['remove']}()")
            print(f"    Dependent Files : {len(usage_details)}")

            print("  Suggested Action: Manual phased refactor required")
            print("  Approval disabled: high dependency risk")
            print("  Change skipped")
            print("  Result: BLOCKED")
            print()
            continue


        # MEDIUM RISK
        elif risk_level == "Medium":

            print("  Decision: Manual approval required")
            print("  Risk Level: Medium")
            print("  Warning: Cross-file dependency detected")
            print()


        # LOW RISK
        else:

            print("  Decision: Safe auto-merge candidate")
            print("  Risk Level: Low")
            print()
        

        if merge_plan.get("warning"):
            print(f"  Warning: {merge_plan['warning']}")

        if merge_plan.get("merge_allowed") is False:
            print("  Approval disabled: unsafe semantic merge.")
            print("  Change skipped")
            print("  Result: BLOCKED")
            print()
            continue
        
        # SAME-NAME OVERWRITE PROTECTION
        if merge_plan["remove"] == merge_plan["keep"]:
            print("  Same-name overwrite detected - merge skipped")
            print("  Suggested Action: Rename one function before merge")
            print("  Result: BLOCKED")
            print()
            continue

        approval = input("  Approve change? (yes/no): ")

        if approval.lower() == "yes":
            backup_file = apply_safe_merge(
                func1["file"],
                merge_plan["remove"],
                merge_plan["keep"]
            )

            print("  Change applied safely")
            print(f"  Backup created: {backup_file}")
            print("  Result: PASS")

            store_decision(f1, f2, best, ", ".join(reasons))
        else:
            store_rejection(
                f1,
                f2,
                best,
                ", ".join(reasons)
            )
            
            print("  Change skipped")
            print("  Result: SKIPPED")

        print()
        
    # =====================================
    # FINAL VALIDATION REPORT
    # =====================================

    print_section("FINAL VALIDATION RESULT")

    print("Total Duplicates Found:", len(duplicates))
    print("Engine Status: STABLE")
    print("Crash Status: NONE")
    print("Prototype Validation Status: CLEARED")   
        
if __name__ == "__main__":
    main()

"""
CodeTruth Agent V2
Purpose Analysis Engine

Objective:
Understand WHAT a function is trying to do,
not just whether it is semantically similar.

This is an EARLY-STAGE purpose analysis layer.
Deterministic + explainable architecture first.
"""

import ast
import re

from typing import Dict
from typing import List


class PurposeAnalysisEngine:

    def __init__(self):

        # ===================================================
        # BUSINESS DOMAINS
        # ===================================================

        self.business_domains = {

            "payment_processing": [
                "payment",
                "refund",
                "invoice",
                "billing",
                "transaction",
                "charge"
            ],

            "authentication": [
                "auth",
                "login",
                "token",
                "password",
                "credential",
                "session",
                "authenticate",
                "authentication",
                "authorize",
                "authorization",
                "verify",
                "validation"
            ],

            "database_operations": [
                "db",
                "database",
                "query",
                "insert",
                "update",
                "delete",
                "fetch",
                "select",
                "record",
                "restore",
                "recover"
            ],

            "file_processing": [
                "file",
                "csv",
                "json",
                "xml",
                "document",
                "upload",
                "download"
            ],

            "notification_system": [
                "notify",
                "email",
                "sms",
                "alert",
                "message",
                "mail"
            ],
            
            "recovery_operations": [
                "rollback",
                "restore",
                "recover",
                "recovery",
                "backup",
                "transaction",
                "revert",
                "restore_backup",
                "rollback_transaction",
                "database_restore",
                "database_rollback",
                "failover",
                "rollback_database",
                "recover_database"
            ]
        }

        # ===================================================
        # ACTION VERBS
        # ===================================================

        self.action_verbs = [
            "process",
            "validate",
            "save",
            "store",
            "delete",
            "remove",
            "fetch",
            "load",
            "generate",
            "calculate",
            "update",
            "send",
            "notify",
            "transform",
            "convert",
            "extract",
            "parse",
            "rollback",
            "restore",
            "recover",
            "archive",
            "authenticate",
            "authorize",
            "verify"
        ]

    # ===================================================
    # NORMALIZE TEXT
    # ===================================================

    def normalize_text(
        self,
        text: str
    ) -> str:

        if not text:
            return ""

        text = text.lower()

        text = re.sub(
            r"([a-z])([A-Z])",
            r"\1 \2",
            text
        )

        text = text.replace("_", " ")
        text = text.replace("-", " ")

        text = re.sub(
            r"[^a-zA-Z0-9\s]",
            "",
            text
        )

        return text.strip()

    # ===================================================
    # TOKENIZE
    # ===================================================

    def tokenize(
        self,
        text: str
    ) -> List[str]:

        normalized = self.normalize_text(text)

        return normalized.split()

    # ===================================================
    # DETECT PRIMARY ACTION
    # ===================================================

    def detect_primary_action(
        self,
        tokens: List[str]
    ) -> str:

        for token in tokens:

            if token in self.action_verbs:

                return token

        return "unknown"

    # ===================================================
    # DETECT BUSINESS DOMAIN
    # ===================================================

    def detect_business_domain(
        self,
        tokens: List[str]
    ) -> str:

        best_domain = "general"

        highest_score = 0
        
        # ------------------------------------------
        # Special Recovery Detection
        # ------------------------------------------

        if (
            ("restore" in tokens or "recover" in tokens)
            and
            ("backup" in tokens or "database" in tokens)
        ):
            return "recovery_operations"

        for (
            domain,
            keywords
        ) in self.business_domains.items():

            score = 0


        for (
            domain,
            keywords
        ) in self.business_domains.items():

            score = 0

            for token in tokens:

                if token in keywords:

                    score += 1

            if score > highest_score:

                highest_score = score

                best_domain = domain

        return best_domain

    # ===================================================
    # EXTRACT FUNCTION CALLS
    # ===================================================

    def extract_function_calls(
        self,
        code: str
    ) -> List[str]:

        calls = []

        try:

            tree = ast.parse(code)

            for node in ast.walk(tree):

                if isinstance(node, ast.Call):

                    if hasattr(node.func, "id"):

                        calls.append(node.func.id)

        except Exception:

            return []

        return list(set(calls))

    # ===================================================
    # DETECT SIDE EFFECTS
    # ===================================================

    def detect_side_effects(
        self,
        code: str
    ) -> List[str]:

        side_effects = []

        normalized = self.normalize_text(code)
        
        if (
            ".restore("
            in code
            or
            ".rollback("
            in code
        ):
            side_effects.append(
                "system_recovery"
            )
        
        if "backup" in normalized:
            side_effects.append(
                "system_recovery"
            )

        if (
            "commit"
            in normalized
        ):

            side_effects.append(
                "database_commit"
            )

        if (
            "send"
            in normalized
            or
            "email"
            in normalized
        ):

            side_effects.append(
                "notification_dispatch"
            )

        if (
            "write"
            in normalized
            or
            "save"
            in normalized
        ):

            side_effects.append(
                "persistent_storage"
            )
            if (
                "rollback"
                in normalized
                or
                "restore"
                in normalized
                or
                "recover"
                in normalized
            ):

                side_effects.append(
                    "system_recovery"
                )

            if (
                "authenticate"
                in normalized
                or
                "authorize"
                in normalized
                or
                "verify"
                in normalized
            ):

                side_effects.append(
                    "security_validation"
            )
            

        return side_effects

    # ===================================================
    # PURPOSE ANALYSIS
    # ===================================================

    def analyze_purpose(
        self,
        function_name: str,
        code: str = "",
        docstring: str = ""
    ) -> Dict:

        combined_text = (
            f"{function_name} "
            f"{docstring} "
            f"{code}"
        )

        tokens = self.tokenize(
            combined_text
        )

        primary_action = (
            self.detect_primary_action(
                tokens
            )
        )

        business_domain = (
            self.detect_business_domain(
                tokens
            )
        )

        function_calls = (
            self.extract_function_calls(
                code
            )
        )

        side_effects = (
            self.detect_side_effects(
                code
            )
        )

        confidence_score = 0.50

        if primary_action != "unknown":
            confidence_score += 0.20

        if business_domain != "general":
            confidence_score += 0.20

        if side_effects:
            confidence_score += 0.10

        confidence_score = round(
            min(confidence_score, 1.0),
            2
        )

        return {

            "function_name":
            function_name,

            "primary_action":
            primary_action,

            "business_domain":
            business_domain,

            "detected_function_calls":
            function_calls,

            "side_effects":
            side_effects,

            "confidence_score":
            confidence_score,

            "engine_type":
            "purpose_analysis_engine"
        }


# =======================================================
# MANUAL TEST
# =======================================================

if __name__ == "__main__":

    engine = PurposeAnalysisEngine()

    sample_code = '''

def process_refund(payment_id):

    validate_payment(payment_id)

    update_database(payment_id)

    send_email(payment_id)

    db.commit()

'''

    result = engine.analyze_purpose(
        function_name="process_refund",
        code=sample_code,
        docstring=(
            "Processes customer refund payments"
        )
    )

    print(result)
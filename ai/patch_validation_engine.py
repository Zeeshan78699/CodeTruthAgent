"""
CodeTruth Agent V2
Patch Validation Engine

Objective:
Validate generated patches before they enter:

Governance
→ HITL
→ Rollback
→ Safe Execution

V2 Philosophy:
- deterministic
- explainable
- governance-first
- safety-first
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import List

from ai.risk_classification_engine import (
    RiskClassificationEngine
)


# =========================================================
# VALIDATION RESULT
# =========================================================

@dataclass
class PatchValidationResult:

    approved: bool

    decision: str

    risk_level: str

    syntax_valid: bool

    governance_passed: bool

    confidence_passed: bool

    confidence_score: float
    
    risk_score: int

    approval_action: str

    reasons: List[str]


# =========================================================
# PATCH VALIDATION ENGINE
# =========================================================

class PatchValidationEngine:

    def __init__(self):

        self.high_risk_patterns = [

            "eval(",

            "exec(",

            "shell=True",

            "os.remove(",

            "shutil.rmtree(",
        ]

        self.risk_engine = (
            RiskClassificationEngine()
        )
        
    # =====================================================
    # MAIN VALIDATION
    # =====================================================

    def validate_patch(

        self,

        patch_candidate

    ) -> PatchValidationResult:

        reasons = []

        syntax_valid = self._validate_syntax(
            patch_candidate.modified_code
        )

        if not syntax_valid:

            reasons.append(
                "Syntax validation failed."
            )

        governance_passed = (
            self._validate_governance(
                patch_candidate.modified_code,
                reasons
            )
        )

        confidence_passed = (
            patch_candidate.confidence_score >= 0.60
        )

        if not confidence_passed:

            reasons.append(
                f"Confidence too low: "
                f"{patch_candidate.confidence_score}"
            )

        decision = self._determine_decision(

            syntax_valid,

            governance_passed,

            patch_candidate.confidence_score
        )
        
        risk_decision = (
            self.risk_engine.classify_risk(
                self._decision_to_score(
                    decision
                )
            )
        )

        risk_level = (
            risk_decision.risk_level
        )

        approval_action = (
            risk_decision.action
        )

        risk_score = (
            risk_decision.risk_score
        )

        approved = (
            decision == "APPROVE"
        )

        return PatchValidationResult(

            approved=approved,

            decision=decision,

            risk_level=risk_level,

            syntax_valid=syntax_valid,

            governance_passed=governance_passed,

            confidence_passed=confidence_passed,

            confidence_score=patch_candidate.confidence_score,
            
            risk_score=risk_score,

            approval_action=approval_action,

            reasons=reasons
        )

    # =====================================================
    # SYNTAX VALIDATION
    # =====================================================

    def _validate_syntax(

        self,

        source_code: str

    ) -> bool:

        try:

            ast.parse(source_code)

            return True

        except Exception:

            return False

    # =====================================================
    # GOVERNANCE VALIDATION
    # =====================================================

    def _validate_governance(

        self,

        source_code: str,

        reasons: List[str]

    ) -> bool:

        if (
            "eval(" in source_code
            and "safe_eval(" not in source_code
        ):
            reasons.append(
                "High risk pattern detected: eval("
            )
            return False

        if (
            "exec(" in source_code
            and "safe_exec(" not in source_code
        ):
            reasons.append(
                "High risk pattern detected: exec("
        )
            return False

        for pattern in [

            "shell=True",

            "os.remove(",

            "shutil.rmtree(",
        ]:

            if pattern in source_code:

                reasons.append(
                    f"High risk pattern detected: {pattern}"
                )

                return False

        return True

    # =====================================================
    # DECISION LOGIC
    # =====================================================

    def _determine_decision(

        self,

        syntax_valid: bool,

        governance_passed: bool,

        confidence_score: float

    ) -> str:

        if not syntax_valid:

            return "REJECT"

        if not governance_passed:

            return "REJECT"

        if confidence_score < 0.60:

            return "REJECT"

        if confidence_score < 0.90:

            return "REVIEW"

        return "APPROVE"

    # =====================================================
    # RISK LOGIC
    # =====================================================

    def _determine_risk(

        self,

        decision: str

    ) -> str:

        if decision == "APPROVE":

            return "LOW"

        if decision == "REVIEW":

            return "MEDIUM"

        return "HIGH"

    def _decision_to_score(

        self,

        decision: str

    ) -> int:

        if decision == "APPROVE":

            return 10

        if decision == "REVIEW":

            return 45

        return 90
# =========================================================
# MANUAL TEST
# =========================================================

if __name__ == "__main__":

    from ai.patch_generation_engine import (
        PatchGenerationEngine
    )

    generator = PatchGenerationEngine()

    validator = PatchValidationEngine()

    sample_code = """

def run_user_code(user_input):

    result = eval(user_input)

    return result

"""

    patch = generator.generate_patch(

        issue_type="unsafe_eval",

        source_code=sample_code,

        target_file="demo.py"
    )

    result = validator.validate_patch(
        patch
    )

    print("=" * 60)
    print("PATCH VALIDATION RESULT")
    print("=" * 60)

    print(result)
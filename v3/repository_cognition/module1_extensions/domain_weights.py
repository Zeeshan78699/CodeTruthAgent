"""
========================================================================
domain_weights.py
CodeTruth Agent V3 — Module 1 Extension
Cross-Cutting Rules Registry

PURPOSE:
    Generic domain subsumption hierarchy.
    Replaces hardcoded per-domain special cases with a structural rule.

RULE:
    When a Core Business Domain is paired with a Supporting Infrastructure
    Protocol, the conflict is resolved by subsumption — not flagged as
    a real domain disagreement.

    Core Domain + Infrastructure Protocol → RESOLVED_BY_SUBSUMPTION
    Core Domain + Another Core Domain     → DOMAIN_CONFLICT_DETECTED
    Unknown pairing                       → DOMAIN_CONFLICT_DETECTED

EXAMPLES:
    Medical  + Web      → RESOLVED_BY_SUBSUMPTION
    Finance  + Web      → RESOLVED_BY_SUBSUMPTION
    Robotics + Network  → RESOLVED_BY_SUBSUMPTION
    Climate  + Data     → RESOLVED_BY_SUBSUMPTION
    Medical  + Finance  → DOMAIN_CONFLICT_DETECTED  (two core domains)

TRUTH BOUNDARY:
    This module classifies conflict type only.
    It does not claim the repository IS a particular domain.
    That claim belongs to Module 1 Core (V3-001/002).

SCOPE NOTE:
    Does not touch Module 1 Core.
    Used by final_enterprise_report.py only.
========================================================================
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Domain hierarchy
# ---------------------------------------------------------------------------

# Normalisation map — framework_signatures.py uses inconsistent naming
# (CLIMATE_SCIENCE instead of CLIMATE_SCIENCE_SYSTEM etc.)
# This map is used for display normalisation only — core values are unchanged.
APPLICATION_TYPE_NORMALISE: dict[str, str] = {
    "CLIMATE_SCIENCE":     "CLIMATE_SCIENCE_SYSTEM",
    "FPGA_HARDWARE":       "FPGA_SYSTEM",
    "ML_PIPELINE":         "ML_SYSTEM",
    "AI_ML":               "AI_ML_SYSTEM",
    "ROBOTICS":            "ROBOTICS_SYSTEM",
    "MEDICAL":             "MEDICAL_SYSTEM",
}

def normalise_application_type(app_type: str) -> str:
    """Returns the standardised _SYSTEM form if a known variant is passed."""
    return APPLICATION_TYPE_NORMALISE.get(app_type, app_type)

CORE_BUSINESS_DOMAINS: set[str] = {
    "FINANCE_SYSTEM",
    "ERP_SYSTEM",
    "SAP_SYSTEM",
    "MEDICAL_SYSTEM",
    "AEROSPACE_SYSTEM",
    "ROBOTICS_SYSTEM",
    "FPGA_SYSTEM",
    "HARDWARE_SYSTEM",
    "ENERGY_SYSTEM",
    "MANUFACTURING_SYSTEM",
    "CLIMATE_SCIENCE_SYSTEM",
    "SCIENTIFIC_SYSTEM",
    "DEFENSE_SYSTEM",
    "AUTOMOTIVE_SYSTEM",
    "TELECOM_SYSTEM",
    # Non-standard variants from framework_signatures.py (OI-006)
    "CLIMATE_SCIENCE",
    "FPGA_HARDWARE",
    "ML_PIPELINE",
}

INFRASTRUCTURE_PROTOCOLS: set[str] = {
    "WEB_PROTOCOL",
    "WEB_APPLICATION",
    "DATA_SYSTEM",
    "NETWORK_IO",
    "API_SERVICE",
    "DATA_PIPELINE",
    "DEVOPS_SYSTEM",
    "CLI_TOOL",
    "Web",       # normalised form from signal_analyzer
    "Data",
    "DevOps",
    "API",
}


def evaluate_domain_hierarchy(
    primary_domain: str,
    secondary_domain: str,
) -> tuple[str, bool]:
    """
    Resolve potential domain conflict between primary and secondary domains.

    KEY RULE: If primary is a Core Business Domain and secondary is an
    Infrastructure Protocol — even on a tie-score — subsumption wins.
    Infrastructure noise should never block a valid core domain classification.

    Returns
    -------
    (conflict_status, trigger_warning)
    """
    p = primary_domain.upper()
    s = secondary_domain.upper()

    # No conflict — same domain
    if p == s or not secondary_domain:
        return "NONE", False

    infra_upper = {d.upper() for d in INFRASTRUCTURE_PROTOCOLS}

    # Core domain + infrastructure protocol → subsumption (includes tie-scores)
    if p in CORE_BUSINESS_DOMAINS and s in infra_upper:
        return "RESOLVED_BY_SUBSUMPTION", False

    # Also handle the reverse — if signal analyzer put infrastructure first
    if s in CORE_BUSINESS_DOMAINS and p in infra_upper:
        return "RESOLVED_BY_SUBSUMPTION", False

    # Two core domains → real conflict, warn
    if p in CORE_BUSINESS_DOMAINS and s in CORE_BUSINESS_DOMAINS:
        return "DOMAIN_CONFLICT_DETECTED", True

    # Unknown pairing → warn
    return "DOMAIN_CONFLICT_DETECTED", True
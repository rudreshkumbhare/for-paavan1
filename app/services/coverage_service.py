"""
Deterministic Coverage Calculation Service.
Performs strictly deterministic mathematical computations in Python (LLM never computes costs).
Supports:
  1. Sum insured
  2. Deductible
  3. Co-payment
  4. Treatment sub-limit
  5. Patient information & Pre-existing condition waiting period evaluation
"""

import re
from typing import Any

from app.services.cost_service import format_inr

# Standard policy requirement for pre-existing conditions
DEFAULT_PED_WAITING_MONTHS = 36


def extract_policy_config_from_chunks(chunks: list[dict]) -> dict[str, Any]:
    """
    Extract structured policy factors from page chunks if present.
    Extracts: sum_insured, deductible, copay_percent, sub_limits, ped_waiting_months, and citations.
    """
    config: dict[str, Any] = {
        "sum_insured": None,
        "deductible": None,
        "copay_percent": None,
        "ped_waiting_months": DEFAULT_PED_WAITING_MONTHS,
        "sub_limits": {},
        "rule_citations": {},
    }

    for c in chunks:
        text = c.get("text", "")
        page = c.get("page", 1)
        section = c.get("section", "")

        # 1. Sum Insured
        if config["sum_insured"] is None:
            m_si = re.search(r"Sum\s+Insured[:\s]+[I₹Rs.]*([\d,]+)", text, re.IGNORECASE)
            if m_si:
                raw = m_si.group(1).replace(",", "")
                try:
                    config["sum_insured"] = int(raw)
                    config["rule_citations"]["sum_insured"] = {
                        "page": page,
                        "section": section or "Policy Schedule",
                        "text": m_si.group(0),
                    }
                except ValueError:
                    pass

        # 2. Deductible
        if config["deductible"] is None:
            m_ded = re.search(r"(?:annual\s+)?deductible(?:\s+of)?[:\s]+[I₹Rs.]*([\d,]+)", text, re.IGNORECASE)
            if m_ded:
                raw = m_ded.group(1).replace(",", "")
                try:
                    config["deductible"] = int(raw)
                    config["rule_citations"]["deductible"] = {
                        "page": page,
                        "section": section or "Deductible and Co-pay",
                        "text": m_ded.group(0),
                    }
                except ValueError:
                    pass

        # 3. Copay Percent
        if config["copay_percent"] is None:
            m_copay = re.search(r"(\d+)%\s+co-?pay", text, re.IGNORECASE)
            if m_copay:
                try:
                    config["copay_percent"] = int(m_copay.group(1))
                    config["rule_citations"]["copay_percent"] = {
                        "page": page,
                        "section": section or "Deductible and Co-pay",
                        "text": m_copay.group(0),
                    }
                except ValueError:
                    pass

        # 4. Pre-existing disease waiting period
        m_ped = re.search(r"pre-existing\s+diseases\s+are\s+covered\s+after\s+a\s+waiting\s+period\s+of\s+(\d+)\s+months", text, re.IGNORECASE)
        if m_ped:
            try:
                config["ped_waiting_months"] = int(m_ped.group(1))
                config["rule_citations"]["ped_waiting"] = {
                    "page": page,
                    "section": section or "Waiting Periods",
                    "text": m_ped.group(0),
                }
            except ValueError:
                pass

        # 5. Procedure Sub-limits
        sublimit_patterns = [
            ("Cataract Surgery", r"Cataract\s+surgery[\s\n]+[I₹Rs.]*([\d,]+)"),
            ("Dental Treatment", r"Dental\s+treatment[^\n]*[\s\n]+[I₹Rs.]*([\d,]+)"),
            ("Ambulance Charges", r"Ambulance\s+charges[\s\n]+[I₹Rs.]*([\d,]+)"),
            ("Health Check-up", r"Health\s+check-up[\s\n]+[I₹Rs.]*([\d,]+)"),
            ("Knee Replacement", r"Knee\s+replacement[^\n]*[\s\n]+[I₹Rs.]*([\d,]+)"),
        ]
        for name, pat in sublimit_patterns:
            if name not in config["sub_limits"]:
                m_sub = re.search(pat, text, re.IGNORECASE)
                if m_sub:
                    raw = m_sub.group(1).replace(",", "")
                    try:
                        val = int(raw)
                        config["sub_limits"][name] = val
                        config["rule_citations"][f"sublimit_{name}"] = {
                            "page": page,
                            "section": section or "Sub-Limits",
                            "text": m_sub.group(0),
                        }
                    except ValueError:
                        pass

    return config


def calculate_coverage(
    estimated_treatment_cost: int | float | None,
    sum_insured: int | float | None,
    deductible: int | float | None,
    copay_percent: int | float | None,
    treatment_sub_limit: int | float | None = None,
    citations_info: dict[str, Any] | None = None,
    age: int | None = None,
    has_pre_existing_condition: bool | None = False,
    continuous_coverage_months: int | None = None,
    ped_waiting_months: int | None = DEFAULT_PED_WAITING_MONTHS,
) -> dict[str, Any]:
    """
    Deterministic Python computation of insurance coverage.
    Includes patient pre-existing condition verification.
    """
    citations = citations_info or {}
    ped_wait_target = ped_waiting_months or DEFAULT_PED_WAITING_MONTHS

    # 1. Validation: Do NOT guess missing rules
    if (
        estimated_treatment_cost is None
        or sum_insured is None
        or deductible is None
        or copay_percent is None
    ):
        return {
            "is_available": False,
            "error": "Coverage estimate unavailable because the policy does not provide enough information.",
        }

    cost = float(estimated_treatment_cost)
    si = float(sum_insured)
    ded = float(deductible)
    copay_pct = float(copay_percent)

    if cost <= 0 or si <= 0:
        return {
            "is_available": False,
            "error": "Coverage estimate unavailable because the policy does not provide enough information.",
        }

    # 2. Patient Pre-Existing Condition Verification (TEST 7, 8, 9)
    if has_pre_existing_condition:
        # Scenario C (TEST 9): Missing continuous coverage information
        if continuous_coverage_months is None:
            cite_ped = citations.get("ped_waiting", {})
            return {
                "is_available": False,
                "error": (
                    f"The policy states that expenses related to pre-existing diseases are covered after "
                    f"{ped_wait_target} months of continuous coverage. The duration of continuous coverage has "
                    f"not been provided, so eligibility cannot be determined from the available information."
                ),
                "policy_rules_applied": [
                    {
                        "rule": "Pre-Existing Condition Waiting Period",
                        "value": f"{ped_wait_target} Months Required",
                        "page": cite_ped.get("page", 1),
                        "section": cite_ped.get("section", "Waiting Periods"),
                        "note": "Continuous coverage duration is required to determine claim eligibility.",
                    }
                ],
            }

        # Scenario B (TEST 8): Continuous coverage < required waiting period (e.g. 12 < 36 months)
        if continuous_coverage_months < ped_wait_target:
            cite_ped = citations.get("ped_waiting", {})
            return {
                "is_available": True,
                "is_eligible": False,
                "estimated_treatment_cost": int(cost),
                "eligible_amount": 0,
                "deductible": 0,
                "copay": 0,
                "potentially_covered": 0,
                "estimated_out_of_pocket": int(cost),
                "formatted_values": {
                    "estimated_treatment_cost": format_inr(cost),
                    "eligible_amount": "₹0",
                    "deductible": "₹0",
                    "copay": "₹0",
                    "potentially_covered": "₹0",
                    "estimated_out_of_pocket": format_inr(cost),
                },
                "policy_rules_applied": [
                    {
                        "rule": "Pre-Existing Disease Waiting Period",
                        "value": f"{ped_wait_target} Months Required (Current: {continuous_coverage_months} Months)",
                        "page": cite_ped.get("page", 1),
                        "section": cite_ped.get("section", "Waiting Periods"),
                        "note": (
                            f"Ineligible: The policy requires {ped_wait_target} months of continuous coverage for pre-existing disease expenses. "
                            f"Current coverage ({continuous_coverage_months} months) is insufficient."
                        ),
                    }
                ],
                "warning": (
                    f"The policy states that expenses related to pre-existing diseases are covered after {ped_wait_target} months of continuous coverage "
                    f"(Page {cite_ped.get('page', 1)} — Waiting Periods). Because your continuous coverage is {continuous_coverage_months} months, "
                    f"this treatment is currently not eligible under pre-existing condition rules."
                ),
                "disclaimer": "Potential coverage estimate — not a claim approval.",
            }

    # Scenario A (TEST 7): Normal policy evaluation (or pre-existing waiting period satisfied)
    # 3. Apply treatment sub-limit
    if treatment_sub_limit is not None and float(treatment_sub_limit) > 0:
        sub_limit_val = float(treatment_sub_limit)
        eligible_amount = min(cost, sub_limit_val)
    else:
        sub_limit_val = None
        eligible_amount = min(cost, si)

    # Cap eligible amount at sum insured
    eligible_amount = min(eligible_amount, si)

    # 4. Apply deductible
    deductible_applied = min(eligible_amount, ded)
    after_deductible = max(0.0, eligible_amount - deductible_applied)

    # 5. Apply co-payment
    copay_rate = copay_pct / 100.0
    copay_amount = round(after_deductible * copay_rate, 2)

    # 6. Potentially covered amount
    potentially_covered = round(after_deductible - copay_amount, 2)
    potentially_covered = min(potentially_covered, si)

    # 7. Estimated out-of-pocket
    estimated_out_of_pocket = round(cost - potentially_covered, 2)

    # Build applied rules metadata with page citations
    rules_applied = []

    if has_pre_existing_condition and continuous_coverage_months and continuous_coverage_months >= ped_wait_target:
        cite_ped = citations.get("ped_waiting", {})
        rules_applied.append({
            "rule": "Pre-Existing Condition Rule",
            "value": f"{ped_wait_target} Months Waiting Period Met",
            "page": cite_ped.get("page", 1),
            "section": cite_ped.get("section", "Waiting Periods"),
            "note": f"Continuous coverage ({continuous_coverage_months} months) satisfies the {ped_wait_target}-month requirement.",
        })

    if sub_limit_val is not None:
        cite = citations.get("sub_limit", {})
        rules_applied.append({
            "rule": "Treatment Sub-Limit",
            "value": format_inr(sub_limit_val),
            "page": cite.get("page", 2),
            "section": cite.get("section", "Sub-Limits"),
            "note": f"Eligible amount capped at {format_inr(sub_limit_val)}.",
        })

    cite_ded = citations.get("deductible", {})
    rules_applied.append({
        "rule": "Annual Deductible",
        "value": format_inr(ded),
        "page": cite_ded.get("page", 1),
        "section": cite_ded.get("section", "Deductible and Co-pay"),
        "note": f"Deductible applied: {format_inr(deductible_applied)}.",
    })

    cite_copay = citations.get("copay_percent", {})
    rules_applied.append({
        "rule": "Co-payment",
        "value": f"{int(copay_pct)}%",
        "page": cite_copay.get("page", 1),
        "section": cite_copay.get("section", "Deductible and Co-pay"),
        "note": f"Co-pay amount: {format_inr(copay_amount)} on post-deductible amount.",
    })

    cite_si = citations.get("sum_insured", {})
    rules_applied.append({
        "rule": "Sum Insured",
        "value": format_inr(si),
        "page": cite_si.get("page", 1),
        "section": cite_si.get("section", "Policy Schedule"),
        "note": f"Overall annual coverage limit: {format_inr(si)}.",
    })

    return {
        "is_available": True,
        "is_eligible": True,
        "estimated_treatment_cost": int(cost),
        "eligible_amount": int(eligible_amount),
        "deductible": int(deductible_applied),
        "copay": int(copay_amount),
        "potentially_covered": int(potentially_covered),
        "estimated_out_of_pocket": int(estimated_out_of_pocket),
        "formatted_values": {
            "estimated_treatment_cost": format_inr(cost),
            "eligible_amount": format_inr(eligible_amount),
            "deductible": format_inr(deductible_applied),
            "copay": format_inr(copay_amount),
            "potentially_covered": format_inr(potentially_covered),
            "estimated_out_of_pocket": format_inr(estimated_out_of_pocket),
        },
        "policy_rules_applied": rules_applied,
        "disclaimer": "Potential coverage estimate — not a claim approval.",
    }

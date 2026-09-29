"""
Treatment cost estimation & deterministic coverage calculation routes:
  POST /api/treatment/estimate
  POST /api/treatment/coverage
  GET  /api/treatment/options
  GET  /api/treatment/catalog
"""

from typing import Any, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.services import cost_service, coverage_service, rag_service

router = APIRouter(prefix="/api/treatment", tags=["Treatment & Coverage Engine"])


# ── Treatment Cost Models ──────────────────────────────────────────────────────

class TreatmentCostEstimateRequest(BaseModel):
    treatment: Optional[str] = Field(None, description="Name of the treatment or procedure")
    treatment_name: Optional[str] = Field(None, description="Alias for treatment name")
    city: Optional[str] = Field("Pune", description="City for cost estimate")
    hospital_type: Optional[str] = Field("Private", description="Hospital type: Private, Government, etc.")


class TreatmentCostEstimateResponse(BaseModel):
    treatment: str
    city: str
    hospital_type: str
    min_cost: int
    typical_cost: int
    max_cost: int
    formatted_typical_cost: str
    formatted_cost_range: str
    disclaimer: str = "Demo estimate based on synthetic treatment-cost data."


class TreatmentOptionsResponse(BaseModel):
    treatments: list[str]
    cities: list[str]
    hospital_types: list[str]


# ── Deterministic Coverage Models ──────────────────────────────────────────────

class CoverageCalculateRequest(BaseModel):
    treatment: Optional[str] = Field(None, description="Treatment name")
    city: Optional[str] = Field("Pune", description="City")
    hospital_type: Optional[str] = Field("Private", description="Hospital type")
    estimated_treatment_cost: Optional[int] = Field(None, description="Treatment cost in INR")
    sum_insured: Optional[int] = Field(None, description="Sum insured in INR")
    deductible: Optional[int] = Field(None, description="Deductible in INR")
    copay_percent: Optional[float] = Field(None, description="Co-payment percentage (e.g. 10)")
    treatment_sub_limit: Optional[int] = Field(None, description="Treatment sub-limit in INR")
    age: Optional[int] = Field(None, description="Patient age in years")
    has_pre_existing_condition: Optional[bool] = Field(None, description="Whether patient has pre-existing condition")
    continuous_coverage_months: Optional[int] = Field(None, description="Continuous coverage duration in months")


class RuleAppliedItem(BaseModel):
    rule: str
    value: str
    page: int
    section: Optional[str] = "Policy"
    note: str


class FormattedCoverageValues(BaseModel):
    estimated_treatment_cost: str
    eligible_amount: str
    deductible: str
    copay: str
    potentially_covered: str
    estimated_out_of_pocket: str


class CoverageCalculateResponse(BaseModel):
    is_available: bool = True
    is_eligible: Optional[bool] = True
    estimated_treatment_cost: Optional[int] = None
    eligible_amount: Optional[int] = None
    deductible: Optional[int] = None
    copay: Optional[int] = None
    potentially_covered: Optional[int] = None
    estimated_out_of_pocket: Optional[int] = None
    formatted_values: Optional[FormattedCoverageValues] = None
    policy_rules_applied: list[RuleAppliedItem] = []
    warning: Optional[str] = None
    disclaimer: str = "Potential coverage estimate — not a claim approval."
    error: Optional[str] = None


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get(
    "/options",
    response_model=TreatmentOptionsResponse,
    summary="Get available treatments, cities, and hospital types",
)
def get_treatment_options():
    """Return distinct options for frontend dropdowns from the synthetic dataset."""
    return cost_service.get_options()


@router.get(
    "/catalog",
    summary="Get full synthetic treatment catalog",
)
def get_catalog():
    """Return all records in the synthetic treatment dataset."""
    return cost_service.get_all_records()


@router.post(
    "/estimate",
    response_model=TreatmentCostEstimateResponse,
    summary="Estimate synthetic treatment cost",
)
def estimate_treatment(request: TreatmentCostEstimateRequest):
    """
    Look up synthetic demo treatment cost by treatment, city, and hospital_type.
    If no match is found, returns 'No cost estimate is available for this treatment in the current demonstration dataset.'
    """
    treatment_target = request.treatment or request.treatment_name
    if not treatment_target or not treatment_target.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Treatment name must be provided.",
        )

    city = request.city or "Pune"
    hospital_type = request.hospital_type or "Private"

    result = cost_service.lookup_cost(
        treatment=treatment_target,
        city=city,
        hospital_type=hospital_type,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No cost estimate is available for this treatment in the current demonstration dataset.",
        )

    return TreatmentCostEstimateResponse(**result)


@router.post(
    "/coverage",
    response_model=CoverageCalculateResponse,
    summary="Deterministic Coverage Calculator",
)
def calculate_treatment_coverage(request: CoverageCalculateRequest):
    """
    Deterministically computes insurance coverage in Python.
    Sequence:
      estimated treatment cost
              ↓
      apply treatment sub-limit
              ↓
      apply deductible
              ↓
      apply co-payment
              ↓
      potentially covered amount
              ↓
      estimated out-of-pocket
    """
    treatment_name = request.treatment or "Knee Replacement"
    city = request.city or "Pune"
    hospital_type = request.hospital_type or "Private"

    # 1. Resolve estimated treatment cost
    cost = request.estimated_treatment_cost
    if cost is None or cost <= 0:
        cost_info = cost_service.lookup_cost(treatment_name, city, hospital_type)
        if cost_info:
            cost = cost_info.get("typical_cost")

    # 2. Resolve policy configuration
    active_config = rag_service.get_active_policy_config()
    citations_info = active_config.get("rule_citations", {})

    sum_insured = request.sum_insured
    if sum_insured is None:
        sum_insured = active_config.get("sum_insured")

    deductible = request.deductible
    if deductible is None:
        deductible = active_config.get("deductible")

    copay_percent = request.copay_percent
    if copay_percent is None:
        copay_percent = active_config.get("copay_percent")

    sub_limit = request.treatment_sub_limit
    if sub_limit is None:
        # Check if procedure has a specific sub-limit extracted from policy
        sub_limits_dict = active_config.get("sub_limits", {})
        for k, v in sub_limits_dict.items():
            if k.lower() in treatment_name.lower() or treatment_name.lower() in k.lower():
                sub_limit = v
                citations_info["sub_limit"] = citations_info.get(f"sublimit_{k}", {"page": 2, "section": "Sub-Limits"})
                break

    # 3. If required rule missing, do NOT guess
    if cost is None or sum_insured is None or deductible is None or copay_percent is None:
        return CoverageCalculateResponse(
            is_available=False,
            error="Coverage estimate unavailable because the policy does not provide enough information.",
        )

    # 4. Perform deterministic arithmetic in Python
    calc = coverage_service.calculate_coverage(
        estimated_treatment_cost=cost,
        sum_insured=sum_insured,
        deductible=deductible,
        copay_percent=copay_percent,
        treatment_sub_limit=sub_limit,
        citations_info=citations_info,
        age=request.age,
        has_pre_existing_condition=request.has_pre_existing_condition,
        continuous_coverage_months=request.continuous_coverage_months,
    )

    if not calc.get("is_available"):
        return CoverageCalculateResponse(
            is_available=False,
            error=calc.get("error", "Coverage estimate unavailable because the policy does not provide enough information."),
            policy_rules_applied=calc.get("policy_rules_applied", []),
        )

    return CoverageCalculateResponse(**calc)

"""
Treatment Cost Estimation Service.
Uses synthetic treatment cost dataset for demo purposes.
"""

import json
import os
from typing import Any

# Check both backend/data and app/data paths
_POSSIBLE_PATHS = [
    os.path.join(os.path.dirname(__file__), "..", "..", "backend", "data", "treatment_costs.json"),
    os.path.join(os.path.dirname(__file__), "..", "data", "treatment_costs.json"),
]

_DATA_PATH = None
for p in _POSSIBLE_PATHS:
    if os.path.exists(p):
        _DATA_PATH = p
        break

if not _DATA_PATH:
    _DATA_PATH = _POSSIBLE_PATHS[0]


def get_all_records() -> list[dict[str, Any]]:
    """Load all synthetic treatment records."""
    if not os.path.exists(_DATA_PATH):
        return []
    with open(_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def format_inr(amount: int | float) -> str:
    """Format integer as Indian Rupee (e.g. 180000 -> ₹1,80,000)."""
    s = str(int(amount))
    if len(s) <= 3:
        return f"₹{s}"
    last3 = s[-3:]
    remaining = s[:-3]
    parts = []
    while remaining:
        parts.insert(0, remaining[-2:])
        remaining = remaining[:-2]
    return f"₹{','.join(parts)},{last3}"


def lookup_cost(treatment: str, city: str = "Pune", hospital_type: str = "Private") -> dict[str, Any] | None:
    """
    Find matching record in synthetic dataset.
    Returns None if no matching entry is found.
    """
    records = get_all_records()
    t_clean = treatment.strip().lower()
    c_clean = city.strip().lower()
    h_clean = hospital_type.strip().lower()

    # Exact match on treatment, city, hospital_type
    for r in records:
        if (
            r.get("treatment", "").strip().lower() == t_clean
            and r.get("city", "").strip().lower() == c_clean
            and r.get("hospital_type", "").strip().lower() == h_clean
        ):
            return {
                "treatment": r["treatment"],
                "city": r["city"],
                "hospital_type": r["hospital_type"],
                "typical_cost": r["typical_cost"],
                "min_cost": r["min_cost"],
                "max_cost": r["max_cost"],
                "formatted_typical_cost": format_inr(r["typical_cost"]),
                "formatted_cost_range": f"{format_inr(r['min_cost'])} – {format_inr(r['max_cost'])}",
                "disclaimer": "Demo estimate based on synthetic treatment-cost data.",
            }

    # Fallback to match treatment if city/hospital matches partially
    for r in records:
        if (
            r.get("treatment", "").strip().lower() == t_clean
            and r.get("hospital_type", "").strip().lower() == h_clean
        ):
            return {
                "treatment": r["treatment"],
                "city": r["city"],
                "hospital_type": r["hospital_type"],
                "typical_cost": r["typical_cost"],
                "min_cost": r["min_cost"],
                "max_cost": r["max_cost"],
                "formatted_typical_cost": format_inr(r["typical_cost"]),
                "formatted_cost_range": f"{format_inr(r['min_cost'])} – {format_inr(r['max_cost'])}",
                "disclaimer": "Demo estimate based on synthetic treatment-cost data.",
            }

    return None


def get_options() -> dict[str, list[str]]:
    """Return distinct treatments, cities, and hospital types for dropdowns."""
    records = get_all_records()
    treatments = []
    cities = []
    hospital_types = []

    for r in records:
        t = r.get("treatment")
        c = r.get("city")
        h = r.get("hospital_type")
        if t and t not in treatments:
            treatments.append(t)
        if c and c not in cities:
            cities.append(c)
        if h and h not in hospital_types:
            hospital_types.append(h)

    return {
        "treatments": treatments,
        "cities": cities,
        "hospital_types": hospital_types,
    }

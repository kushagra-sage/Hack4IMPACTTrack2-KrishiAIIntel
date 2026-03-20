"""
Decision Support Module for KrishiIntel AI
Computes EMI options, recommends a plan, and classifies loan eligibility
based on extracted invoice fields (asset_cost, horse_power, model_name).

Supports Smart Mode (auto-configured) and Manual Mode (user-specified).
"""

from typing import Dict, Optional, Any
import math


# ─── Constants ───────────────────────────────────────────────────────────────
DEFAULT_ANNUAL_RATE = 10.5   # % per annum (typical agri-loan rate in India)
TENURE_OPTIONS = {
    "5_years": 60,   # months
    "7_years": 84,
    "9_years": 108,
}
RECOMMENDED_PLAN = "7_years"


# ─── Core EMI formula ───────────────────────────────────────────────────────

def compute_emi(principal: float, annual_rate: float, tenure_months: int) -> float:
    """
    Standard EMI formula:
        EMI = (P × r × (1+r)^n) / ((1+r)^n − 1)
    where P = principal, r = monthly interest rate, n = tenure in months.
    """
    if principal <= 0 or tenure_months <= 0:
        return 0.0
    r = annual_rate / (12 * 100)  # monthly rate as decimal
    if r == 0:
        return round(principal / tenure_months, 2)
    # math.pow((1 + r), n)
    factor = math.pow((1 + r), tenure_months)
    emi = principal * r * (factor / (factor - 1))
    return round(emi, 2)


def get_emi_options(asset_cost: float, annual_rate: float = DEFAULT_ANNUAL_RATE) -> Dict[str, float]:
    """Return EMI for each tenure option."""
    return {
        label: compute_emi(asset_cost, annual_rate, months)
        for label, months in TENURE_OPTIONS.items()
    }


# ─── Smart Mode ─────────────────────────────────────────────────────────────

def compute_emi_smart(asset_cost: float) -> Dict[str, Any]:
    """
    Smart Mode: auto-set interest rate and tenure based on asset cost bracket.

    Cost Brackets:
        ≤ ₹5L   → 9.5% rate, recommend 5-year tenure
        ≤ ₹10L  → 10.5% rate, recommend 7-year tenure
        > ₹10L  → 12.0% rate, recommend 9-year tenure

    Returns dict with EMI value, total payable, explanation, and all options.
    """
    if asset_cost <= 0:
        return {
            "emi": 0,
            "total_payable": 0,
            "explanation": "Invalid asset cost. Please provide a positive value.",
            "rate": 0,
            "tenure_months": 0,
            "all_options": {},
        }

    # Auto-select rate and tenure based on cost bracket
    if asset_cost <= 500_000:
        rate = 9.5
        recommended_tenure = "5_years"
        bracket = "Economy (≤ ₹5L)"
    elif asset_cost <= 1_000_000:
        rate = 10.5
        recommended_tenure = "7_years"
        bracket = "Standard (₹5L – ₹10L)"
    else:
        rate = 12.0
        recommended_tenure = "9_years"
        bracket = "Premium (> ₹10L)"

    tenure_months = TENURE_OPTIONS[recommended_tenure]
    emi = compute_emi(asset_cost, rate, tenure_months)
    total_payable = round(emi * tenure_months, 2)
    total_interest = round(total_payable - asset_cost, 2)

    # Compute all options at the auto-selected rate
    all_options = {}
    for label, months in TENURE_OPTIONS.items():
        opt_emi = compute_emi(asset_cost, rate, months)
        opt_total = round(opt_emi * months, 2)
        all_options[label] = {
            "emi": opt_emi,
            "total_payable": opt_total,
            "total_interest": round(opt_total - asset_cost, 2),
        }

    explanation = (
        f"For an asset cost of ₹{asset_cost:,.0f} ({bracket}), "
        f"the recommended plan is {recommended_tenure.replace('_', ' ')} "
        f"at {rate}% p.a. interest. "
        f"Monthly EMI: ₹{emi:,.0f}. "
        f"Total payable: ₹{total_payable:,.0f} "
        f"(interest component: ₹{total_interest:,.0f})."
    )

    return {
        "emi": emi,
        "total_payable": total_payable,
        "total_interest": total_interest,
        "rate": rate,
        "tenure_months": tenure_months,
        "recommended_tenure": recommended_tenure,
        "bracket": bracket,
        "explanation": explanation,
        "all_options": all_options,
    }


# ─── Manual Mode ────────────────────────────────────────────────────────────

def compute_emi_manual(
    principal: float,
    annual_rate: float,
    tenure_months: int,
) -> Dict[str, Any]:
    """
    Manual Mode: user specifies principal, rate, and tenure.

    Returns dict with EMI value, total payable, and explanation.
    """
    if principal <= 0:
        return {
            "emi": 0,
            "total_payable": 0,
            "total_interest": 0,
            "explanation": "Invalid principal amount. Please provide a positive value.",
        }

    if tenure_months <= 0:
        return {
            "emi": 0,
            "total_payable": 0,
            "total_interest": 0,
            "explanation": "Invalid tenure. Please provide a positive number of months.",
        }

    if annual_rate < 0 or annual_rate > 50:
        return {
            "emi": 0,
            "total_payable": 0,
            "total_interest": 0,
            "explanation": "Interest rate must be between 0% and 50%.",
        }

    emi = compute_emi(principal, annual_rate, tenure_months)
    total_payable = round(emi * tenure_months, 2)
    total_interest = round(total_payable - principal, 2)
    years = tenure_months / 12

    explanation = (
        f"For a principal of ₹{principal:,.0f} at {annual_rate}% p.a. "
        f"over {tenure_months} months ({years:.1f} years): "
        f"Monthly EMI is ₹{emi:,.0f}. "
        f"Total payable: ₹{total_payable:,.0f}. "
        f"Total interest: ₹{total_interest:,.0f}."
    )

    return {
        "emi": emi,
        "total_payable": total_payable,
        "total_interest": total_interest,
        "principal": principal,
        "annual_rate": annual_rate,
        "tenure_months": tenure_months,
        "explanation": explanation,
    }


# ─── Eligibility classification ─────────────────────────────────────────────

def classify_eligibility(asset_cost: float, horse_power: Optional[float]) -> Dict[str, str]:
    """
    Rule-based eligibility tiers.
    Returns dict with 'status' and 'reason'.
    """
    hp = horse_power or 0
    cost = asset_cost or 0

    if hp >= 50 and cost <= 1_000_000:
        return {
            "status": "High Eligibility",
            "reason": (
                f"Asset cost ₹{cost:,.0f} is within the ₹10L threshold and "
                f"horse power ({hp} HP) meets the ≥50 HP requirement, "
                "indicating a standard-category tractor with strong loan viability."
            ),
        }
    elif hp >= 35 and cost <= 1_500_000:
        return {
            "status": "Moderate Eligibility",
            "reason": (
                f"Asset cost ₹{cost:,.0f} is within ₹15L and horse power ({hp} HP) "
                "exceeds 35 HP. The application is viable but may require additional "
                "documentation or a higher down payment."
            ),
        }
    else:
        reasons = []
        if cost > 1_500_000:
            reasons.append(f"asset cost ₹{cost:,.0f} exceeds ₹15L")
        if hp < 35:
            reasons.append(f"horse power ({hp} HP) is below the 35 HP minimum")
        reason_text = " and ".join(reasons) if reasons else "parameters fall outside standard thresholds"
        return {
            "status": "Review Required",
            "reason": (
                f"Manual review recommended because {reason_text}. "
                "A field officer assessment or additional collateral may be needed."
            ),
        }


# ─── Public entry point ─────────────────────────────────────────────────────

def generate_decision_support(fields: Dict[str, Any]) -> Dict:
    """
    Generate the full decision_support block from extracted invoice fields.

    Args:
        fields: dict with at least 'asset_cost', optionally 'horse_power', 'model_name'

    Returns:
        {
            "decision_support": {
                "emi_options": { "5_years": ..., "7_years": ..., "9_years": ... },
                "recommended_plan": "7_years",
                "eligibility": "High Eligibility" | "Moderate Eligibility" | "Review Required",
                "reason": "...",
                "annual_interest_rate": 10.5,
                "asset_cost": ...,
                "model_name": ...,
                "horse_power": ...
            }
        }
    """
    asset_cost = fields.get("asset_cost") or 0
    horse_power = fields.get("horse_power")
    model_name = fields.get("model_name", "Unknown")

    emi_options = get_emi_options(asset_cost)
    eligibility = classify_eligibility(asset_cost, horse_power)

    return {
        "decision_support": {
            "emi_options": emi_options,
            "recommended_plan": RECOMMENDED_PLAN,
            "eligibility": eligibility["status"],
            "reason": eligibility["reason"],
            "annual_interest_rate": DEFAULT_ANNUAL_RATE,
            "asset_cost": asset_cost,
            "model_name": model_name,
            "horse_power": horse_power,
        }
    }

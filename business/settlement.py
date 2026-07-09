"""
Settlement calculation and validation logic.
Handles all driver payment computations.
"""

from dataclasses import dataclass
from utils.helpers import safe_float


@dataclass
class SettlementBreakdown:
    """Data class for settlement calculations."""
    gross_revenue: float
    fuel_deductions: float
    other_deductions: float
    subtotal_deductions: float
    dispatch_fee: float
    factoring_fee: float
    owner_final: float
    mj7_final: float


def calculate_settlement(gross_revenue, fuel_deductions=0.0, other_deductions=0.0, apply_factoring=False):
    """
    Calculate settlement breakdown.
    
    Flow:
    1. Calculate Owner Base from 85% of Gross Revenue
    2. Calculate MJ7 Base from 15% of Gross Revenue
    3. Calculate Dispatch Fee from 5% of Gross Revenue
    4. Calculate Factoring Fee from 2.15% of Gross Revenue
    5. Subtract fuel and other deductions from Owner Base
    6. If factoring is enabled, charge Factoring Fee to Owner
    7. If factoring is disabled, charge Factoring Fee to MJ7
    
    Args:
        gross_revenue: Total load amount ($)
        fuel_deductions: Fuel costs ($)
        other_deductions: Other deductions ($)
        apply_factoring: Whether to charge 2.15% factoring fee to Owner
    
    Returns:
        SettlementBreakdown object with all calculations
    """
    gross_revenue = safe_float(gross_revenue)
    fuel_deductions = safe_float(fuel_deductions)
    other_deductions = safe_float(other_deductions)
    
    # Calculate total deductions
    subtotal_deductions = fuel_deductions + other_deductions
    
    # All percentage-based amounts must be calculated from 100% gross.
    owner_base = gross_revenue * 0.85
    mj7_base = gross_revenue * 0.15
    dispatch_fee = gross_revenue * 0.05
    factoring_fee = gross_revenue * 0.0215

    if apply_factoring:
        owner_final = owner_base - subtotal_deductions - factoring_fee
        mj7_final = mj7_base - dispatch_fee
    else:
        owner_final = owner_base - subtotal_deductions
        mj7_final = mj7_base - dispatch_fee - factoring_fee
    
    return SettlementBreakdown(
        gross_revenue=gross_revenue,
        fuel_deductions=fuel_deductions,
        other_deductions=other_deductions,
        subtotal_deductions=subtotal_deductions,
        dispatch_fee=round(dispatch_fee, 2),
        factoring_fee=round(factoring_fee, 2),
        owner_final=round(owner_final, 2),
        mj7_final=round(mj7_final, 2)
    )


def validate_settlement(settlement):
    """
    Validate settlement calculations for consistency.
    
    Args:
        settlement (SettlementBreakdown): Settlement object to validate
    
    Returns:
        str: Error message if invalid, None if valid
    """
    if settlement.gross_revenue < 0:
        return "❌ Gross revenue cannot be negative"
    
    if settlement.owner_final < 0:
        return "❌ Owner payment cannot be negative"
    
    if settlement.mj7_final < 0:
        return "❌ MJ7 net cannot be negative"
    
    owner_base = settlement.gross_revenue * 0.85
    mj7_base = settlement.gross_revenue * 0.15
    expected_total = (
        settlement.owner_final
        + settlement.mj7_final
        + settlement.subtotal_deductions
        + settlement.dispatch_fee
        + settlement.factoring_fee
    )
    expected_gross_split = owner_base + mj7_base

    if abs(expected_total - expected_gross_split) > 0.05:
        return "❌ Settlement calculation mismatch"
    
    return None

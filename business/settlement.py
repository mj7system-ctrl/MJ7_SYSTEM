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
    1. Gross Revenue
    2. Subtract fuel & other deductions
    3. Subtract dispatch fee (5%)
    4. If enabled, subtract factoring fee (2.15%)
    5. Remainder = Owner final payment
    6. MJ7 keeps dispatch + factoring
    
    Args:
        gross_revenue: Total load amount ($)
        fuel_deductions: Fuel costs ($)
        other_deductions: Other deductions ($)
        apply_factoring: Whether to apply 2.15% factoring fee
    
    Returns:
        SettlementBreakdown object with all calculations
    """
    gross_revenue = safe_float(gross_revenue)
    fuel_deductions = safe_float(fuel_deductions)
    other_deductions = safe_float(other_deductions)
    
    # Calculate total deductions
    subtotal_deductions = fuel_deductions + other_deductions
    
    # Calculate dispatch fee (10% of gross)
    dispatch_fee = gross_revenue * 0.05
    
    # Calculate amount before factoring
    before_factoring = gross_revenue - subtotal_deductions - dispatch_fee
    
    # Apply factoring if enabled (2.15% of before_factoring)
    factoring_fee = 0.0
    if apply_factoring:
        factoring_fee = before_factoring * 0.0215
    
    # Owner gets: before_factoring - factoring_fee
    owner_final = before_factoring - factoring_fee
    
    # MJ7 gets: dispatch_fee + factoring_fee
    mj7_final = dispatch_fee + factoring_fee
    
    return SettlementBreakdown(
        gross_revenue=gross_revenue,
        fuel_deductions=fuel_deductions,
        other_deductions=other_deductions,
        subtotal_deductions=subtotal_deductions,
        dispatch_fee=dispatch_fee,
        factoring_fee=factoring_fee,
        owner_final=owner_final,
        mj7_final=mj7_final
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
    
    # Verify math: gross - deductions - dispatch - factoring = owner
    expected_owner = settlement.gross_revenue - settlement.subtotal_deductions - settlement.dispatch_fee - settlement.factoring_fee
    if abs(settlement.owner_final - expected_owner) > 0.01:  # Allow 1 cent rounding
        return "❌ Settlement calculation mismatch"
    
    return None

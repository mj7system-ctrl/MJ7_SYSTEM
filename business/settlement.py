"""
Settlement calculation and validation logic.
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
    
    Args:
        gross_revenue: Total load amount
        fuel_deductions: Fuel costs
        other_deductions: Other deductions
        apply_factoring: Whether to apply 2.15% factoring fee
    
    Returns:
        SettlementBreakdown object
    """
    gross_revenue = safe_float(gross_revenue)
    fuel_deductions = safe_float(fuel_deductions)
    other_deductions = safe_float(other_deductions)
    
    subtotal_deductions = fuel_deductions + other_deductions
    dispatch_fee = gross_revenue * 0.10  # 10%
    
    # Calculate before factoring
    before_factoring = gross_revenue - subtotal_deductions - dispatch_fee
    
    # Apply factoring if enabled
    factoring_fee = 0.0
    if apply_factoring:
        factoring_fee = before_factoring * 0.0215  # 2.15%
    
    owner_final = before_factoring - factoring_fee
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
    Validate settlement calculations.
    Returns error message or None if valid.
    """
    if settlement.gross_revenue < 0:
        return "Gross revenue cannot be negative"
    
    if settlement.owner_final < 0:
        return "Owner payment cannot be negative"
    
    if settlement.mj7_final < 0:
        return "MJ7 net cannot be negative"
    
    return None

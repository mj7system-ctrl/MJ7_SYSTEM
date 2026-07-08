"""
Validation functions for data integrity.
Ensures data consistency and quality across the application.
"""

import pandas as pd
from config.columns import get_col


def validate_dataframe(df, sheet_name):
    """
    Validate dataframe structure and content.
    Checks that required columns exist.
    
    Args:
        df: DataFrame to validate
        sheet_name: Name of the sheet for column mapping
    
    Returns:
        tuple: (is_valid: bool, errors_list: list)
    """
    if df.empty:
        return True, []
    
    errors = []
    
    # Check minimum columns
    try:
        cols = list(df.columns)
        if len(cols) < 3:
            errors.append("Too few columns - sheet may be empty or corrupted")
    except Exception as e:
        errors.append(f"Column check failed: {str(e)}")
    
    # Optional: Validate against COLUMN_MAPS
    try:
        from config.columns import validate_sheet_columns
        is_valid, col_error = validate_sheet_columns(df, sheet_name)
        if not is_valid:
            errors.append(col_error)
    except Exception:
        pass  # Skip if sheet_name not in COLUMN_MAPS
    
    return len(errors) == 0, errors


def validate_load_data(load_id, company, amount, driver):
    """
    Validate new load data before saving.
    
    Args:
        load_id: Load ID
        company: Company/Broker name
        amount: Load amount
        driver: Driver selection
    
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if not load_id or load_id.strip() == "":
        return False, "❌ Load ID is required"
    
    if not company or company.strip() == "":
        return False, "❌ Company/Broker name is required"
    
    try:
        amount_float = float(amount)
        if amount_float <= 0:
            return False, "❌ Amount must be greater than 0"
    except (ValueError, TypeError):
        return False, "❌ Amount must be a valid number"
    
    if driver in ["Select Driver", "No drivers available", ""]:
        return False, "❌ Valid driver selection required"
    
    return True, None


def validate_settlement_inputs(gross, owner_pay, mj7_net):
    """
    Validate settlement calculations for mathematical consistency.
    
    Args:
        gross: Gross amount
        owner_pay: Owner payment
        mj7_net: MJ7 net profit
    
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    try:
        gross = float(gross)
        owner_pay = float(owner_pay)
        mj7_net = float(mj7_net)
    except (ValueError, TypeError):
        return False, "❌ All values must be numeric"
    
    if gross < 0:
        return False, "❌ Gross amount cannot be negative"
    
    if owner_pay < 0:
        return False, "❌ Owner pay cannot be negative"
    
    if mj7_net < 0:
        return False, "❌ MJ7 net cannot be negative"
    
    if owner_pay > gross:
        return False, "❌ Owner pay cannot exceed gross amount"
    
    return True, None


def validate_deduction_data(date_val, load_id, driver_id, deduction_type, amount):
    """
    Validate deduction entry data.
    
    Args:
        date_val: Date of deduction
        load_id: Load ID
        driver_id: Driver ID
        deduction_type: Type of deduction (FUEL, OTHER)
        amount: Deduction amount
    
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if not date_val:
        return False, "❌ Date is required"
    
    if not load_id or load_id.strip() == "":
        return False, "❌ Load ID is required"
    
    if not driver_id or driver_id.strip() == "":
        return False, "❌ Driver ID is required"
    
    if deduction_type not in ["FUEL", "OTHER"]:
        return False, "❌ Invalid deduction type"
    
    try:
        amount_float = float(amount)
        if amount_float < 0:
            return False, "❌ Amount cannot be negative"
    except (ValueError, TypeError):
        return False, "❌ Amount must be a valid number"
    
    return True, None


def validate_driver_data(driver_id, full_name, status):
    """
    Validate driver registration data.
    
    Args:
        driver_id: Driver ID
        full_name: Driver full name
        status: Driver status (ACTIVE, ON LEAVE, INACTIVE)
    
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if not driver_id or driver_id.strip() == "":
        return False, "❌ Driver ID is required"
    
    if not full_name or full_name.strip() == "":
        return False, "❌ Full name is required"
    
    valid_statuses = ["ACTIVE", "ON LEAVE", "INACTIVE"]
    if status not in valid_statuses:
        return False, f"❌ Status must be one of: {', '.join(valid_statuses)}"
    
    return True, None

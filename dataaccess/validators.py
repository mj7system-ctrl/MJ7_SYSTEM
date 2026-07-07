"""
Validation functions for data integrity.
"""

import pandas as pd
from config.columns import get_col

def validate_dataframe(df, sheet_name):
    """
    Validate dataframe structure.
    Returns (is_valid, errors_list)
    """
    if df.empty:
        return True, []
    
    errors = []
    
    # Check required columns exist
    try:
        cols = list(df.columns)
        if len(cols) < 3:
            errors.append("Too few columns")
    except Exception as e:
        errors.append(f"Column check failed: {str(e)}")
    
    return len(errors) == 0, errors

def validate_load_data(load_id, company, amount, driver):
    """
    Validate new load data.
    Returns (is_valid, error_message)
    """
    if not load_id or load_id.strip() == "":
        return False, "Load ID is required"
    
    if not company or company.strip() == "":
        return False, "Company/Broker name is required"
    
    if amount <= 0:
        return False, "Amount must be greater than 0"
    
    if driver in ["Select Driver", "No drivers available"]:
        return False, "Valid driver selection required"
    
    return True, None

def validate_settlement_inputs(gross, owner_pay, mj7_net):
    """
    Validate settlement calculations.
    Returns (is_valid, error_message)
    """
    if gross < 0:
        return False, "Gross amount cannot be negative"
    
    if owner_pay < 0:
        return False, "Owner pay cannot be negative"
    
    if mj7_net < 0:
        return False, "MJ7 net cannot be negative"
    
    if owner_pay > gross:
        return False, "Owner pay cannot exceed gross amount"
    
    return True, None

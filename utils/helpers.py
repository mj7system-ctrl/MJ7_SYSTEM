"""
Utility helper functions.
Common functions used throughout the application for data manipulation and formatting.
"""

import pandas as pd
import re
from datetime import datetime


def safe_float(value, default=0.0):
    """
    Convert value to float safely without raising exceptions.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
    
    Returns:
        float: Converted value or default
    """
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value, default=0):
    """
    Convert value to int safely without raising exceptions.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
    
    Returns:
        int: Converted value or default
    """
    try:
        if pd.isna(value):
            return default
        return int(float(value))
    except (ValueError, TypeError):
        return default


def safe_to_numeric(series, errors='coerce'):
    """
    Convert pandas series to numeric safely.
    
    Args:
        series: Pandas Series to convert
        errors: How to handle errors ('coerce' = convert to NaN)
    
    Returns:
        pd.Series: Numeric series
    """
    try:
        return pd.to_numeric(series, errors=errors)
    except Exception:
        return series


def money(value):
    """
    Format value as USD currency.
    
    Args:
        value: Numeric value to format
    
    Returns:
        str: Formatted currency string (e.g., "$1,234.56")
    """
    try:
        value = safe_float(value)
        return f"${value:,.2f}"
    except Exception:
        return "$0.00"


def format_gallons(value):
    """
    Format value as gallons.
    
    Args:
        value: Numeric value to format
    
    Returns:
        str: Formatted gallons string (e.g., "100.50 gal")
    """
    try:
        value = safe_float(value)
        return f"{value:,.2f} gal"
    except Exception:
        return "0.00 gal"


def safe_date_str(value):
    """
    Convert date to string safely.
    Handles multiple date formats gracefully.
    
    Args:
        value: Date value to convert
    
    Returns:
        str: Date as YYYY-MM-DD string
    """
    try:
        if pd.isna(value):
            return ""
        if isinstance(value, str):
            return value
        return pd.to_datetime(value).strftime('%Y-%m-%d')
    except Exception:
        return ""


def parse_date(date_str):
    """
    Parse date string to datetime object.
    
    Args:
        date_str: Date string to parse
    
    Returns:
        datetime: Parsed datetime object or None
    """
    try:
        return pd.to_datetime(date_str)
    except Exception:
        return None


def sorted_unique_safe(series):
    """
    Get sorted unique values from pandas series safely.
    
    Args:
        series: Pandas Series to extract unique values from
    
    Returns:
        list: Sorted list of unique values
    """
    try:
        return sorted(series.dropna().astype(str).unique().tolist())
    except Exception:
        return []

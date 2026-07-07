"""
Utility helper functions.
"""

import pandas as pd
import re
from datetime import datetime

def safe_float(value, default=0.0):
    """Convert value to float safely."""
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int(value, default=0):
    """Convert value to int safely."""
    try:
        if pd.isna(value):
            return default
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_to_numeric(series, errors='coerce'):
    """Convert series to numeric safely."""
    return pd.to_numeric(series, errors=errors)

def money(value):
    """Format value as USD currency."""
    try:
        value = safe_float(value)
        return f"${value:,.2f}"
    except Exception:
        return "$0.00"

def format_gallons(value):
    """Format value as gallons."""
    try:
        value = safe_float(value)
        return f"{value:,.2f} gal"
    except Exception:
        return "0.00 gal"

def safe_date_str(value):
    """Convert date to string safely."""
    try:
        if pd.isna(value):
            return ""
        if isinstance(value, str):
            return value
        return pd.to_datetime(value).strftime('%Y-%m-%d')
    except Exception:
        return ""

def parse_date(date_str):
    """Parse date string to datetime."""
    try:
        return pd.to_datetime(date_str)
    except Exception:
        return None

def sorted_unique_safe(series):
    """Get sorted unique values from series safely."""
    try:
        return sorted(series.dropna().unique())
    except Exception:
        return []

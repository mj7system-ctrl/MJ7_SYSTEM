"""
Accounts Payable / Accounts Receivable business logic.
Completely independent from settlements.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
import pandas as pd
from utils.helpers import safe_float, safe_date_str

@dataclass
class APARMetrics:
    """Metrics for AP/AR reports."""
    total_amount: float
    paid_amount: float
    pending_amount: float
    overdue_amount: float
    due_soon_amount: float  # Due within 7 days
    count_total: int
    count_paid: int
    count_pending: int
    count_overdue: int
    count_due_soon: int

def calculate_ap_ar_metrics(df, today=None):
    """
    Calculate AP/AR metrics from dataframe.
    
    Args:
        df: DataFrame with AP/AR data
        today: Reference date (default: today)
    
    Returns:
        APARMetrics object
    """
    if today is None:
        today = pd.Timestamp.today().normalize()
    
    if df.empty:
        return APARMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    
    # Ensure date columns are datetime
    if 'DUE_DATE' in df.columns:
        df['DUE_DATE'] = pd.to_datetime(df['DUE_DATE'], errors='coerce')
    
    # Calculate amounts
    df_clean = df.copy()
    df_clean['AMOUNT'] = pd.to_numeric(df_clean['AMOUNT'], errors='coerce').fillna(0)
    
    total_amount = safe_float(df_clean['AMOUNT'].sum())
    
    # Status breakdown
    paid_mask = df_clean['STATUS'] == 'PAID'
    pending_mask = df_clean['STATUS'] == 'PENDING'
    
    paid_amount = safe_float(df_clean[paid_mask]['AMOUNT'].sum())
    pending_amount = safe_float(df_clean[pending_mask]['AMOUNT'].sum())
    
    # Overdue: PENDING records with due date < today
    overdue_mask = (pending_mask) & (df_clean['DUE_DATE'] < today)
    overdue_amount = safe_float(df_clean[overdue_mask]['AMOUNT'].sum())
    
    # Due soon: PENDING records with due date between today and today+7
    due_soon_mask = (pending_mask) & (df_clean['DUE_DATE'] >= today) & (df_clean['DUE_DATE'] <= today + timedelta(days=7))
    due_soon_amount = safe_float(df_clean[due_soon_mask]['AMOUNT'].sum())
    
    return APARMetrics(
        total_amount=total_amount,
        paid_amount=paid_amount,
        pending_amount=pending_amount,
        overdue_amount=overdue_amount,
        due_soon_amount=due_soon_amount,
        count_total=len(df_clean),
        count_paid=len(df_clean[paid_mask]),
        count_pending=len(df_clean[pending_mask]),
        count_overdue=len(df_clean[overdue_mask]),
        count_due_soon=len(df_clean[due_soon_mask])
    )

def get_aged_report(df, today=None):
    """
    Generate aged debtors/creditors report.
    
    Returns dataframe with aging buckets.
    """
    if today is None:
        today = pd.Timestamp.today().normalize()
    
    if df.empty:
        return pd.DataFrame()
    
    df_report = df.copy()
    df_report['AMOUNT'] = pd.to_numeric(df_report['AMOUNT'], errors='coerce').fillna(0)
    df_report['DUE_DATE'] = pd.to_datetime(df_report['DUE_DATE'], errors='coerce')
    
    # Only PENDING records
    df_report = df_report[df_report['STATUS'] == 'PENDING']
    
    # Calculate days overdue
    df_report['DAYS_OVERDUE'] = (today - df_report['DUE_DATE']).dt.days
    
    # Aging buckets
    def get_bucket(days):
        if days < 0:
            return "Not Yet Due"
        elif days <= 30:
            return "Current (0-30)"
        elif days <= 60:
            return "31-60 Days"
        elif days <= 90:
            return "61-90 Days"
        else:
            return "90+ Days"
    
    df_report['AGING_BUCKET'] = df_report['DAYS_OVERDUE'].apply(get_bucket)
    
    return df_report

def mark_payment(df, record_id, payment_date):
    """
    Mark a record as PAID.
    
    Args:
        df: DataFrame
        record_id: ID of record to mark
        payment_date: Date of payment
    
    Returns:
        Updated DataFrame
    """
    df_updated = df.copy()
    mask = df_updated['ID'] == record_id
    
    if mask.any():
        df_updated.loc[mask, 'STATUS'] = 'PAID'
        df_updated.loc[mask, 'PAYMENT_DATE'] = payment_date
    
    return df_updated

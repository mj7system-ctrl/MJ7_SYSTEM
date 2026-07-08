"""
UI components for AP/AR module.
Renders headers, metrics grids, and data rows.
"""

from utils.helpers import money
from business.ap_ar_logic import APARMetrics


def render_ap_ar_header(company_name, is_payable=True):
    """
    Render AP/AR section header.
    
    Args:
        company_name: Name of company (e.g., "MJ7 LOGISTICS")
        is_payable: True for Accounts Payable, False for Receivable
    
    Returns:
        HTML string for header
    """
    section_type = "ACCOUNTS PAYABLE" if is_payable else "ACCOUNTS RECEIVABLE"
    
    header = f"""
    <div style="background-color: #0F172A; color: #FFFFFF; padding: 20px; border-radius: 12px; margin-bottom: 20px;">
        <h2 style="margin: 0; font-size: 24px; font-weight: 700;">{company_name} — {section_type}</h2>
        <p style="margin: 5px 0 0 0; color: #CBD5E1; font-size: 14px;">Independent management module | Separate from Settlements</p>
    </div>
    """
    return header


def render_metrics_grid(metrics: APARMetrics):
    """
    Render AP/AR metrics dashboard.
    Displays 5-column grid with key metrics.
    
    Args:
        metrics: APARMetrics object with calculated values
    
    Returns:
        HTML string for metrics grid
    """
    
    grid = f"""
    <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 15px; margin-bottom: 25px;">
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 15px; text-align: center;">
            <div style="font-size: 11px; font-weight: 600; color: #64748B; text-transform: uppercase;">Total Amount</div>
            <div style="font-size: 24px; font-weight: 700; color: #0047AB; margin: 8px 0;">{money(metrics.total_amount)}</div>
            <div style="font-size: 12px; color: #94A3B8;">{metrics.count_total} records</div>
        </div>
        
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 15px; text-align: center;">
            <div style="font-size: 11px; font-weight: 600; color: #64748B; text-transform: uppercase;">Paid</div>
            <div style="font-size: 24px; font-weight: 700; color: #10B981; margin: 8px 0;">{money(metrics.paid_amount)}</div>
            <div style="font-size: 12px; color: #94A3B8;">{metrics.count_paid} records</div>
        </div>
        
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 15px; text-align: center;">
            <div style="font-size: 11px; font-weight: 600; color: #64748B; text-transform: uppercase;">Pending</div>
            <div style="font-size: 24px; font-weight: 700; color: #F59E0B; margin: 8px 0;">{money(metrics.pending_amount)}</div>
            <div style="font-size: 12px; color: #94A3B8;">{metrics.count_pending} records</div>
        </div>
        
        <div style="background: #FFFFFF; border: 1px solid #FCA5A5; border-radius: 10px; padding: 15px; text-align: center; background-color: #FEF2F2;">
            <div style="font-size: 11px; font-weight: 600; color: #DC2626; text-transform: uppercase;">Overdue</div>
            <div style="font-size: 24px; font-weight: 700; color: #DC2626; margin: 8px 0;">{money(metrics.overdue_amount)}</div>
            <div style="font-size: 12px; color: #991B1B;">{metrics.count_overdue} records</div>
        </div>
        
        <div style="background: #FFFFFF; border: 1px solid #FDE047; border-radius: 10px; padding: 15px; text-align: center; background-color: #FFFBEB;">
            <div style="font-size: 11px; font-weight: 600; color: #B45309; text-transform: uppercase;">Due Soon (7d)</div>
            <div style="font-size: 24px; font-weight: 700; color: #B45309; margin: 8px 0;">{money(metrics.due_soon_amount)}</div>
            <div style="font-size: 12px; color: #92400E;">{metrics.count_due_soon} records</div>
        </div>
    </div>
    """
    return grid


def render_ap_ar_row(row_id, date, supplier_or_client, invoice_num, description, amount, due_date, status, payment_date=""):
    """
    Render a single AP/AR record row for display.
    
    Args:
        row_id: Record ID
        date: Invoice date
        supplier_or_client: Supplier/Client name
        invoice_num: Invoice number
        description: Invoice description
        amount: Amount in USD
        due_date: Due date
        status: PAID or PENDING
        payment_date: Date payment was made (if paid)
    
    Returns:
        HTML string for table row
    """
    
    status_color = "#10B981" if status == "PAID" else "#F59E0B"
    status_bg = "#F0FDF4" if status == "PAID" else "#FFFBEB"
    
    row_html = f"""
    <tr style="border-bottom: 1px solid #E2E8F0;">
        <td style="padding: 12px; color: #0F172A; font-weight: 500; font-size: 13px;">{row_id}</td>
        <td style="padding: 12px; color: #475569; font-size: 13px;">{date}</td>
        <td style="padding: 12px; color: #475569; font-size: 13px;">{supplier_or_client}</td>
        <td style="padding: 12px; color: #475569; font-size: 13px;">{invoice_num}</td>
        <td style="padding: 12px; color: #475569; font-size: 13px;">{description}</td>
        <td style="padding: 12px; color: #0047AB; font-weight: 600; font-size: 13px; text-align: right;">{money(amount)}</td>
        <td style="padding: 12px; color: #475569; font-size: 13px;">{due_date}</td>
        <td style="padding: 12px; font-size: 13px;">
            <span style="background-color: {status_bg}; color: {status_color}; padding: 4px 8px; border-radius: 4px; font-weight: 600; font-size: 12px;">{status}</span>
        </td>
        <td style="padding: 12px; color: #94A3B8; font-size: 13px;">{payment_date if payment_date else '-'}</td>
    </tr>
    """
    return row_html

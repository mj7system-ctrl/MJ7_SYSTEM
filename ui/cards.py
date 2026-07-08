"""
UI Card components for load and settlement displays.
Handles rendering of performance cards, settlement previews, and metrics.
"""

from utils.helpers import money

def render_load_card(load_id, driver_id, driver_name, date_str, gross, owner_pay, mj7_net, logo_html=""):
    """Render a load performance card as HTML."""
    card_html = f"""<div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 24px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
<div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #F1F5F9; padding-bottom: 16px; margin-bottom: 16px;">
<div>
<h4 style="margin: 0; color: #0F172A; font-size: 14px; letter-spacing: 0.5px; font-weight: 800;">MJ7 LOGISTICS — LOAD CARD</h4>
<span style="font-size: 12px; color: #475569;">Date: {date_str}</span>
</div>
{logo_html}
</div>
<div style="background-color: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 6px; padding: 10px 14px; font-size: 13px; color: #334155; margin-bottom: 20px;">
<span style="color: #64748B; font-weight: 600;">DRIVER ID:</span> <span style="font-weight: 700; color: #0F172A;">{driver_id}</span> | 
<span style="color: #64748B; font-weight: 600;">NAME:</span> <span style="font-weight: 700; color: #0F172A;">{driver_name}</span> |
<span style="color: #64748B; font-weight: 600;">LOAD:</span> <span style="font-weight: 700; color: #0F172A;">{load_id}</span>
</div>
<table style="width: 100%; border-collapse: separate; border-spacing: 16px 0; margin-left: -16px; margin-right: -16px;">
<tr>
<td style="width: 33.33%; background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 8px; padding: 14px; text-align: center;">
<div style="font-size: 11px; text-transform: uppercase; color: #475569; font-weight: 700;">Gross Total</div>
<div style="font-size: 22px; color: #0F172A; font-weight: 800;">{money(gross)}</div>
</td>
<td style="width: 33.33%; background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 8px; padding: 14px; text-align: center;">
<div style="font-size: 11px; text-transform: uppercase; color: #475569; font-weight: 700;">Owner Pay</div>
<div style="font-size: 22px; color: #0F172A; font-weight: 800;">{money(owner_pay)}</div>
</td>
<td style="width: 33.33%; background-color: #2563EB; border: 1px solid #1D4ED8; border-radius: 8px; padding: 14px; text-align: center;">
<div style="font-size: 11px; text-transform: uppercase; color: #FFFFFF; font-weight: 700;">MJ7 Net Profit</div>
<div style="font-size: 22px; color: #FFFFFF; font-weight: 800;">{money(mj7_net)}</div>
</td>
</tr>
</table>
</div>"""
    return card_html

def render_settlement_preview(settlement):
    """Render settlement preview/breakdown as HTML."""
    preview_html = f"""<div style="background-color: #EFF6FF; border: 2px solid #BFDBFE; border-radius: 12px; padding: 20px; margin-bottom: 20px;">
<h4 style="margin: 0 0 16px 0; color: #0047AB; font-weight: 700;">Settlement Breakdown</h4>
<table style="width: 100%; font-size: 14px; color: #0F172A; border-collapse: collapse;">
<tr style="border-bottom: 1px solid #BFDBFE;">
<td style="padding: 10px 0; font-weight: 600;">Gross Revenue:</td>
<td style="padding: 10px 0; text-align: right; font-weight: 700;">{money(settlement.gross_revenue)}</td>
</tr>
<tr style="border-bottom: 1px solid #BFDBFE;">
<td style="padding: 10px 0; color: #64748B;">- Fuel Deductions:</td>
<td style="padding: 10px 0; text-align: right; color: #64748B;">{money(settlement.fuel_deductions)}</td>
</tr>
<tr style="border-bottom: 1px solid #BFDBFE;">
<td style="padding: 10px 0; color: #64748B;">- Other Deductions:</td>
<td style="padding: 10px 0; text-align: right; color: #64748B;">{money(settlement.other_deductions)}</td>
</tr>
<tr style="border-bottom: 1px solid #BFDBFE;">
<td style="padding: 10px 0; color: #64748B;">- Dispatch Fee (10%):</td>
<td style="padding: 10px 0; text-align: right; color: #64748B;">{money(settlement.dispatch_fee)}</td>
</tr>
<tr style="border-bottom: 1px solid #BFDBFE;">
<td style="padding: 10px 0; color: #64748B;">- Factoring Fee (2.15%):</td>
<td style="padding: 10px 0; text-align: right; color: #64748B;">{money(settlement.factoring_fee)}</td>
</tr>
<tr style="background-color: #FFF; border-top: 2px solid #1E40AF;">
<td style="padding: 12px 0; font-weight: 700; color: #1E40AF;">Owner Final Payment:</td>
<td style="padding: 12px 0; text-align: right; font-weight: 700; color: #1E40AF; font-size: 16px;">{money(settlement.owner_final)}</td>
</tr>
<tr>
<td style="padding: 12px 0; font-weight: 700; color: #0047AB;">MJ7 Net Income:</td>
<td style="padding: 12px 0; text-align: right; font-weight: 700; color: #0047AB; font-size: 16px;">{money(settlement.mj7_final)}</td>
</tr>
</table>
</div>"""
    return preview_html

def render_metric_card(label, value, unit="", color="#0047AB"):
    """Render a single metric card."""
    card = f"""<div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 20px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
<div style="font-size: 12px; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px;">{label}</div>
<div style="font-size: 28px; font-weight: 700; color: {color}; margin-bottom: 4px;">{value}</div>
<div style="font-size: 12px; color: #94A3B8;">{unit}</div>
</div>"""
    return card

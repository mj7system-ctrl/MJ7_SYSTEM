# app_refactored.py
"""
MJ7 LOGISTICS CONTROL CENTER - REFACTORED & MODULAR
====================================================
Versión 5.0: Arquitectura limpia, segura y mantenible
CON MÓDULO AP/AR INTEGRADO
ÚLTIMA ACTUALIZACIÓN: Correcciones finales aplicadas
"""

import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import plotly.express as px
from PIL import Image
import io
import os
import base64

# ReportLab
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus import Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# === IMPORTS INTERNOS ===
from config.columns import get_col, COLUMN_MAPS, validate_sheet_columns
from dataaccess.sheets_operations import SheetsOperations
from business.settlement import calculate_settlement, validate_settlement, SettlementBreakdown
from business.ap_ar_logic import calculate_ap_ar_metrics, get_aged_report
from ui.cards import render_load_card, render_settlement_preview, render_metric_card
from ui.ap_ar_components import render_ap_ar_header, render_metrics_grid
from utils.helpers import (
    safe_float, safe_int, money, safe_to_numeric, format_gallons,
    safe_date_str, parse_date, sorted_unique_safe
)
from dataaccess.validators import validate_dataframe, validate_load_data, validate_settlement_inputs

# ====================================
# CONFIGURACIÓN & AUTENTICACIÓN
# ====================================

st.set_page_config(
    page_title="MJ7 Logistics Control Center",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

scope = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive'
]

creds_dict = dict(st.secrets["gcp_service_account"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

SHEET_NAME = "MJ7_Database"

# Session state initialization
session_defaults = {
    "form_load": "",
    "form_company": "",
    "form_amount": None,
    "form_origin": "",
    "form_destination": "",
}
for key, value in session_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ====================================
# ESTILOS GLOBALES
# ====================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [data-testid="stSidebar"] { 
        font-family: 'Inter', sans-serif; 
        background-color: #F8FAFC; 
    }
    
    :root {
        --primary-color: #0047AB !important;
        --secondary-backend-color: #0047AB !important;
    }
    
    [data-testid="stSidebar"] { 
        background-color: #0F172A !important; 
        color: #F8FAFC !important; 
        border-right: 1px solid #1E293B;
    }
    
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] span, [data-testid="stSidebar"] p { 
        color: #E2E8F0 !important; 
    }
    
    h1 { 
        color: #0F172A; 
        font-weight: 700; 
        letter-spacing: -0.03em; 
        margin-bottom: 5px !important;
    }
    
    h2, h3 { 
        color: #1E293B; 
        font-weight: 600; 
        letter-spacing: -0.02em; 
    }
    
    [data-testid="metric-container"] { 
        background: #FFFFFF !important; 
        padding: 24px 20px !important; 
        border-radius: 12px !important; 
        border: 1px solid #E2E8F0 !important; 
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03) !important;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    [data-testid="metric-container"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.02) !important;
    }
    
    [data-testid="stMetricLabel"] { 
        color: #64748B !important; 
        font-weight: 600 !important; 
        font-size: 0.8rem !important; 
        text-transform: uppercase; 
        letter-spacing: 0.05em;
    }
    
    [data-testid="stMetricValue"] { 
        color: #0047AB !important; 
        font-weight: 700 !important; 
        font-size: 1.75rem !important; 
        letter-spacing: -0.02em;
    }
    
    button[data-baseweb="tab"] {
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        color: #64748B !important;
        border-bottom-width: 3px !important;
        border-bottom-color: transparent !important;
        padding: 12px 18px !important;
    }
    
    button[data-baseweb="tab"]:hover {
        color: #0F172A !important;
    }
    
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #0047AB !important; 
        border-bottom-color: #0047AB !important;
        font-weight: 600 !important;
    }
    
    [data-testid="stDataFrame"], [data-testid="stTable"], .stDataFrame {
        background: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        padding: 6px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02) !important;
    }

    div[data-testid="stDataFrame"] th, 
    .stDataFrame table thead th,
    div[data-baseweb="table-grid"] div[role="columnheader"] {
        background-color: #0047AB !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }

    ::-webkit-scrollbar-thumb {
        background: #0047AB !important;
        border-radius: 10px !important;
    }
    
    ::-webkit-scrollbar-track {
        background: #F1F5F9 !important;
    }
    
    .stButton button { 
        background: #1E293B !important; 
        color: #FFFFFF !important; 
        border-radius: 8px !important; 
        padding: 12px 24px !important; 
        font-weight: 600 !important; 
        border: none !important; 
        width: 100%; 
        transition: background 0.2s ease;
    }
    
    .stButton button:hover { 
        background: #0F172A !important; 
    }
    
    .financing-card-container {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 12px !important;
        padding: 24px !important;
        margin-bottom: 20px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02) !important;
    }
    
    .financing-card-header {
        display: flex !important;
        justify-content: space-between !important;
        border-bottom: 1px solid #F1F5F9 !important;
        padding-bottom: 14px !important;
        align-items: center !important;
    }
    
    .financing-card-driver {
        font-weight: 700 !important;
        color: #0047AB !important;
        font-size: 1.2rem !important;
    }
    
    .financing-grid {
        display: grid !important;
        grid-template-columns: repeat(3, 1fr) !important;
        gap: 20px !important;
        margin-top: 20px !important;
        text-align: center !important;
    }
    
    .financing-metric-label {
        color: #64748B !important;
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em;
    }
    
    .financing-metric-value {
        color: #0F172A !important;
        font-weight: 700 !important;
        font-size: 1.5rem !important;
        margin-top: 4px !important;
    }
    
    .financing-metric-value.highlighted {
        color: #0047AB !important;
    }
    
    .financing-timeline {
        margin-top: 20px !important;
        background: #F8FAFC !important;
        padding: 14px !important;
        border-radius: 8px !important;
        font-size: 0.85rem !important;
        color: #475569 !important;
        display: grid !important;
        grid-template-columns: repeat(4, 1fr) !important;
        text-align: center !important;
        border: 1px solid #F1F5F9 !important;
    }
    
    .timeline-item {
        border-right: 1px solid #E2E8F0 !important;
    }
    
    .timeline-item.last {
        border-right: none !important;
    }
    
    .timeline-item.completed {
        color: #94A3B8 !important;
        text-decoration: line-through !important;
    }
    
    .timeline-item.pending {
        font-weight: 600 !important;
        color: #0F172A !important;
    }
</style>
""", unsafe_allow_html=True)

today = pd.Timestamp.today().normalize()

# ====================================
# CARGAR DATOS (con validación)
# ====================================

@st.cache_data(ttl=600)
def load_data():
    """Cargar datos de todas las hojas con validación."""
    sh = client.open(SHEET_NAME)
    
    # Cargar hojas principales
    loads = pd.DataFrame(sh.worksheet("CARGAS").get_all_records())
    settlements = pd.DataFrame(sh.worksheet("SETTLEMENTS").get_all_records())
    deductions = pd.DataFrame(sh.worksheet("DEDUCTIONS").get_all_records())
    drivers = pd.DataFrame(sh.worksheet("DRIVERS").get_all_records())
    
    # Cargar hojas opcionales con fallback - CORREGIDO: EXPENSE_FINANCING
    try:
        expense_fin = pd.DataFrame(sh.worksheet("EXPENSE_FINANCING").get_all_records())
    except Exception:
        expense_fin = pd.DataFrame(columns=[get_col("EXPENSE_FINANCING", k) 
                                            for k in COLUMN_MAPS["EXPENSE_FINANCING"].values()])
    
    try:
        truck_pay = pd.DataFrame(sh.worksheet("TRUCK_PAYMENTS").get_all_records())
    except Exception:
        truck_pay = pd.DataFrame(columns=[get_col("TRUCK_PAYMENTS", k) 
                                          for k in COLUMN_MAPS["TRUCK_PAYMENTS"].values()])
    
    try:
        dispatch_track = pd.DataFrame(sh.worksheet("DISPATCH_TRACKER").get_all_records())
    except Exception:
        dispatch_track = pd.DataFrame(columns=[get_col("DISPATCH_TRACKER", k) 
                                               for k in COLUMN_MAPS["DISPATCH_TRACKER"].values()])
    
    # Convertir fechas
    for df in [loads, settlements, deductions]:
        for col in [get_col("CARGAS", "start_date"), get_col("CARGAS", "delivery_date"), get_col("SETTLEMENTS", "date"), get_col("DEDUCTIONS", "date")]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Validar estructuras críticas
    for sheet_name, df in [
        ("CARGAS", loads),
        ("SETTLEMENTS", settlements),
        ("DEDUCTIONS", deductions),
    ]:
        is_valid, errors = validate_dataframe(df, sheet_name)
        if not is_valid:
            st.warning(f"⚠️ {sheet_name}: {'; '.join(errors)}")
    
    return loads, settlements, deductions, drivers, expense_fin, truck_pay, dispatch_track

# Cargar datos
try:
    loads, settlements, deductions, drivers, expense_fin, truck_pay, dispatch_track = load_data()
except Exception as e:
    st.error(f"❌ Error loading data: {e}")
    st.stop()

# ====================================
# HEADER
# ====================================

st.sidebar.title("MJ7 OPERATIONS")
st.sidebar.caption("Control Panel v5.0 (Refactored)")

title_col, logo_col = st.columns([5, 1])
with title_col:
    st.title("MJ7 Logistics Control Center")
    st.caption(f"Management Terminal | {datetime.now().strftime('%A, %d %B %Y')}")
with logo_col:
    try:
        st.image("logo.jpeg", width=110)
    except Exception:
        pass

st.divider()

# ====================================
# MJ7 PROFITS METRICS
# ====================================

if not settlements.empty:
    date_col = get_col("SETTLEMENTS", "date")
    mj7_net_col = get_col("SETTLEMENTS", "mj7_net")
    
    settlements[date_col] = pd.to_datetime(settlements[date_col])
    
    net_today = settlements[settlements[date_col].dt.date == today.date()][mj7_net_col].sum()
    net_week = settlements[settlements[date_col] >= (today - timedelta(days=7))][mj7_net_col].sum()
    net_month = settlements[settlements[date_col].dt.month == today.month][mj7_net_col].sum()
    net_year = settlements[settlements[date_col].dt.year == today.year][mj7_net_col].sum()
else:
    net_today = net_week = net_month = net_year = 0.00

st.markdown("### MJ7 Profits")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Today", money(net_today))
k2.metric("This Week", money(net_week))
k3.metric("This Month", money(net_month))
k4.metric("This Year", money(net_year))
st.divider()

# ====================================
# TABS
# ====================================

tabs = st.tabs([
    ":material/insert_chart: Loads",
    ":material/payments: Settlements",
    ":material/trending_up: Performance",
    ":material/money_off: Deductions",
    ":material/edit_note: Data Entry",
    ":material/search: Search Engine",
    ":material/picture_as_pdf: PDF Reports",
    ":material/gavel: Status Verification",
    ":material/credit_score: Expense Financing",
    ":material/local_shipping: Truck Payments",
    ":material/pie_chart: Dispatch Tracker",
    ":material/account_balance: AP/AR Management"
])


# ====================================
# TAB 6: PDF REPORTS
# ====================================

with tabs[6]:
    st.subheader("Executive Report Engine")
    selected_scope = st.selectbox(
        "Select Report Type:",
        ["Complete Financial Overview", "Isolated Driver View", "Fuel Audit Ledger"]
    )
    
    def compile_pdf_document(df_source, heading, show_totals=False, sum_mj7=0.0, sum_owner=0.0):
        """Generar PDF con tabla completa."""
        byte_stream = io.BytesIO()
        pdf_canvas = SimpleDocTemplate(byte_stream, pagesize=letter, rightMargin=24, leftMargin=24, topMargin=30, bottomMargin=36)
        elements_list = []
        
        try:
            logo_element = RLImage("logo.jpeg", width=100, height=50)
            logo_element.hAlign = 'RIGHT'
            elements_list.append(logo_element)
            elements_list.append(Spacer(1, 10))
        except Exception:
            pass
        
        text_styles = getSampleStyleSheet()
        header_style = ParagraphStyle('DocHead', parent=text_styles['Heading1'], fontSize=16, leading=20,
                                      textColor=colors.HexColor('#0F172A'), spaceAfter=8)
        meta_style = ParagraphStyle('DocMeta', parent=text_styles['Normal'], fontSize=9,
                                    textColor=colors.HexColor('#475569'), spaceAfter=14)
        total_style = ParagraphStyle('DocTotals', parent=text_styles['Normal'], fontSize=11, fontName="Helvetica-Bold",
                                     textColor=colors.HexColor('#0F172A'), spaceAfter=10)
        cell_style = ParagraphStyle('DataCell', parent=text_styles['Normal'], fontSize=8, alignment=1)
        
        df_display = df_source.copy()
        
        if get_col("SETTLEMENTS", "driver_id") in df_display.columns:
            drivers_copy = drivers[[get_col("DRIVERS", "driver_id"), get_col("DRIVERS", "full_name")]].copy()
            drivers_copy[get_col("DRIVERS", "driver_id")] = drivers_copy[get_col("DRIVERS", "driver_id")].astype(str)
            df_display[get_col("SETTLEMENTS", "driver_id")] = df_display[get_col("SETTLEMENTS", "driver_id")].astype(str)
            df_display = df_display.merge(drivers_copy, left_on=get_col("SETTLEMENTS", "driver_id"),
                                         right_on=get_col("DRIVERS", "driver_id"), how="left")
            df_display.drop(columns=[get_col("SETTLEMENTS", "driver_id")], inplace=True)
            df_display.rename(columns={get_col("DRIVERS", "full_name"): "DRIVER"}, inplace=True)
        
        elements_list.append(Paragraph("MJ7 LOGISTICS CENTER MANAGEMENT REPORT", header_style))
        elements_list.append(Paragraph(f"Scope: {heading} | Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", meta_style))
        
        if show_totals:
            elements_list.append(Paragraph(f"TOTAL MJ7 NET: ${sum_mj7:,.2f} | TOTAL OWNER: ${sum_owner:,.2f}", total_style))
            elements_list.append(Spacer(1, 10))
        
        cols = df_display.columns.to_list()
        table_data = [[Paragraph(f"<b>{str(c).replace('_', ' ')}</b>", text_styles['Normal']) for c in cols]]
        
        for _, row in df_display.iterrows():
            row_items = []
            for col in cols:
                val = row[col]
                if col in [get_col("SETTLEMENTS", col_name) for col_name in ["gross", "owner_pay", "dispatch_fee", "factoring_fee", "mj7_net"]]:
                    item_text = money(val)
                elif isinstance(val, (datetime, pd.Timestamp)):
                    item_text = val.strftime('%Y-%m-%d')
                else:
                    item_text = str(val) if pd.notnull(val) else ""
                row_items.append(Paragraph(item_text, cell_style))
            table_data.append(row_items)
        
        report_table = Table(table_data, repeatRows=1)
        report_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#475569')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')])
        ]))
        elements_list.append(report_table)
        pdf_canvas.build(elements_list)
        return byte_stream.getvalue()
    
    if selected_scope == "Complete Financial Overview":
        if st.button("Generate Report"):
            if not settlements.empty:
                mj7_col = get_col("SETTLEMENTS", "mj7_net")
                owner_col = get_col("SETTLEMENTS", "owner_pay")
                pdf_binary = compile_pdf_document(
                    settlements, "General Financial Overview",
                    True, settlements[mj7_col].sum(), settlements[owner_col].sum()
                )
                st.download_button("📥 Download General Report", pdf_binary,
                                 f"MJ7_Report_{datetime.now().strftime('%Y%m%d')}.pdf", "application/pdf")
            else:
                st.warning("⚠️ No settlement data available.")
    
    elif selected_scope == "Isolated Driver View":
        driver_uid = st.selectbox("Select Driver:", drivers[get_col("DRIVERS", "driver_id")].unique() if not drivers.empty else [])
        if st.button("Generate Driver Report"):
            settle_driver_col = get_col("SETTLEMENTS", "driver_id")
            subset = settlements[settlements[settle_driver_col].astype(str) == str(driver_uid)]
            if not subset.empty:
                mj7_col = get_col("SETTLEMENTS", "mj7_net")
                owner_col = get_col("SETTLEMENTS", "owner_pay")
                pdf_binary = compile_pdf_document(
                    subset, f"Driver {driver_uid}",
                    True, subset[mj7_col].sum(), subset[owner_col].sum()
                )
                st.download_button(f"📥 Download {driver_uid} Report", pdf_binary,
                                 f"MJ7_Driver_{driver_uid}_{datetime.now().strftime('%Y%m%d')}.pdf", "application/pdf")
            else:
                st.warning(f"⚠️ No data for driver {driver_uid}.")
    
    elif selected_scope == "Fuel Audit Ledger":
        if st.button("Generate Fuel Report"):
            ded_type_col = get_col("DEDUCTIONS", "type")
            fuel_records = deductions[deductions[ded_type_col] == "FUEL"]
            if not fuel_records.empty:
                pdf_binary = compile_pdf_document(fuel_records, "Fuel Audit Ledger", False)
                st.download_button("📥 Download Fuel Report", pdf_binary,
                                 f"MJ7_Fuel_Audit_{datetime.now().strftime('%Y%m%d')}.pdf", "application/pdf")
            else:
                st.warning("⚠️ No fuel records found.")

# ====================================
# TAB 7: STATUS VERIFICATION
# ====================================

with tabs[7]:
    st.subheader("Load Status Verification Panel")
    st.caption("Automatic filtering and control by delivery date and transit status.")
    st.divider()
    
    if not loads.empty:
        load_id_col_name = get_col("CARGAS", "load_id")
        status_col_name = get_col("CARGAS", "status")
        company_col_name = get_col("CARGAS", "company")
        driver_col_name = get_col("CARGAS", "driver_id")
        delivery_col_name = get_col("CARGAS", "delivery_date")
        origin_col_name = get_col("CARGAS", "origin")
        destination_col_name = get_col("CARGAS", "destination")
        
        loads_alerts = loads.copy()
        loads_alerts["DELIVERY_DATE_DT"] = pd.to_datetime(loads_alerts[delivery_col_name], errors='coerce').dt.date
        
        criticas = []
        atencion = []
        entregadas = []
        en_tiempo = []
        
        for _, row in loads_alerts.iterrows():
            try:
                status = str(row[status_col_name]).strip().upper()
            except:
                status = "UNKNOWN"
            
            fecha_entrega = row.get("DELIVERY_DATE_DT")
            
            if status == "CLOSED / SETTLED" or pd.isna(fecha_entrega):
                continue
            
            try:
                dias_restantes = (pd.to_datetime(fecha_entrega).date() - pd.to_datetime(today).date()).days
            except Exception:
                dias_restantes = 999
            
            if status == "DELIVERED":
                entregadas.append((row, "Delivery confirmed. Pending settlement."))
            elif dias_restantes <= 0 and dias_restantes != 999:
                msg = "Delivered today" if dias_restantes == 0 else f"Overdue by {abs(dias_restantes)} days"
                criticas.append((row, msg))
            elif dias_restantes == 1:
                atencion.append((row, "Due tomorrow"))
            elif dias_restantes != 999:
                en_tiempo.append((row, f"On schedule ({dias_restantes} days left)"))
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Critical / Overdue", len(criticas))
        m2.metric("Due Tomorrow", len(atencion))
        m3.metric("Pending Settlement", len(entregadas))
        m4.metric("On Schedule", len(en_tiempo))
        st.write("")
        
        # Critical
        if criticas:
            st.markdown("<h5 style='color: #0F172A; font-weight: 600; margin-bottom: 15px;'>🔴 Critical Loads</h5>", unsafe_allow_html=True)
            for item, motivo in criticas:
                load_id = item.get(load_id_col_name, 'N/A')
                company = item.get(company_col_name, 'N/A')
                driver = item.get(driver_col_name, 'N/A')
                origin = item.get(origin_col_name, 'N/A')
                destination = item.get(destination_col_name, 'N/A')
                
                st.markdown(f"""
                <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-left: 5px solid #DC2626; border-radius: 8px; padding: 16px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 600; color: #0F172A;">Load: {load_id} | {company}</span>
                        <span style="font-size: 12px; color: #DC2626; background-color: #FEF2F2; padding: 4px 8px; border-radius: 4px;">{motivo}</span>
                    </div>
                    <div style="font-size: 13px; color: #475569; margin-top: 10px; border-top: 1px solid #F1F5F9; padding-top: 10px; display: flex; gap: 15px;">
                        <div><span style="color: #94A3B8; font-weight: 500;">Driver:</span> <span style="font-weight: 500;">{driver}</span></div>
                        <div><span style="color: #94A3B8; font-weight: 500;">Route:</span> <span style="font-weight: 500;">{origin} → {destination}</span></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            st.write("")
        
        # Attention
        if atencion:
            st.markdown("<h5 style='color: #0F172A; font-weight: 600; margin-bottom: 15px;'>🟠 Urgent Loads (Due Tomorrow)</h5>", unsafe_allow_html=True)
            for item, motivo in atencion:
                load_id = item.get(load_id_col_name, 'N/A')
                company = item.get(company_col_name, 'N/A')
                driver = item.get(driver_col_name, 'N/A')
                origin = item.get(origin_col_name, 'N/A')
                destination = item.get(destination_col_name, 'N/A')
                
                st.markdown(f"""
                <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-left: 5px solid #D97706; border-radius: 8px; padding: 16px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 600; color: #0F172A;">Load: {load_id} | {company}</span>
                        <span style="font-size: 12px; color: #B45309; background-color: #FEF3C7; padding: 4px 8px; border-radius: 4px;">{motivo}</span>
                    </div>
                    <div style="font-size: 13px; color: #475569; margin-top: 10px; border-top: 1px solid #F1F5F9; padding-top: 10px; display: flex; gap: 15px;">
                        <div><span style="color: #94A3B8; font-weight: 500;">Driver:</span> <span style="font-weight: 500;">{driver}</span></div>
                        <div><span style="color: #94A3B8; font-weight: 500;">Route:</span> <span style="font-weight: 500;">{origin} → {destination}</span></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            st.write("")
        
        # Pending settlement
        if entregadas:
            st.markdown("<h5 style='color: #0F172A; font-weight: 600; margin-bottom: 15px;'>🔵 Pending Settlement</h5>", unsafe_allow_html=True)
            for item, motivo in entregadas:
                load_id = item.get(load_id_col_name, 'N/A')
                company = item.get(company_col_name, 'N/A')
                driver = item.get(driver_col_name, 'N/A')
                origin = item.get(origin_col_name, 'N/A')
                destination = item.get(destination_col_name, 'N/A')
                
                st.markdown(f"""
                <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-left: 5px solid #2563EB; border-radius: 8px; padding: 16px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 600; color: #0F172A;">Load: {load_id} | {company}</span>
                        <span style="font-size: 12px; color: #1E40AF; background-color: #EFF6FF; padding: 4px 8px; border-radius: 4px;">{motivo}</span>
                    </div>
                    <div style="font-size: 13px; color: #475569; margin-top: 10px; border-top: 1px solid #F1F5F9; padding-top: 10px; display: flex; gap: 15px;">
                        <div><span style="color: #94A3B8; font-weight: 500;">Driver:</span> <span style="font-weight: 500;">{driver}</span></div>
                        <div><span style="color: #94A3B8; font-weight: 500;">Route:</span> <span style="font-weight: 500;">{origin} → {destination}</span></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            st.write("")
        
        # On Schedule
        if en_tiempo:
            st.markdown("<h5 style='color: #0F172A; font-weight: 600; margin-bottom: 15px;'>🟢 On Schedule</h5>", unsafe_allow_html=True)
            for item, motivo in en_tiempo:
                load_id = item.get(load_id_col_name, 'N/A')
                company = item.get(company_col_name, 'N/A')
                
                st.markdown(f"""
                <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-left: 5px solid #16A34A; border-radius: 8px; padding: 16px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 600; color: #0F172A;">Load: {load_id} | {company}</span>
                        <span style="font-size: 12px; color: #15803D; background-color: #DCFCE7; padding: 4px 8px; border-radius: 4px;">{motivo}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            st.write("")
        
        if not criticas and not atencion and not entregadas and not en_tiempo:
            st.success("✅ No active loads or all are settled.")
    else:
        st.info("ℹ️ No active load records.")

# ====================================
# TAB 8: EXPENSE FINANCING
# ====================================

with tabs[8]:
    st.subheader("Expense Financing Control")
    st.caption("Manage driver maintenance loans with custom financing terms.")
    
    col_fin1, col_fin2 = st.columns(2)
    
    with col_fin1:
        with st.form("form_expense_fin", clear_on_submit=True):
            st.markdown("<h5 style='color:#1E293B; margin-bottom:15px;'>New Financing</h5>", unsafe_allow_html=True)
            f_driver = st.text_input("Driver Name").strip()
            f_truck = st.text_input("Truck ID").strip()
            f_concept = st.selectbox("Expense", ["Tires", "Engine", "Repair", "Insurance", "Other"])
            f_base = st.number_input("Amount (USD)", min_value=0.0, step=100.0)
            f_rate = st.slider("Interest Rate (%)", 0, 10, 0)
            f_date = st.date_input("Agreement Date", datetime.today())
            
            if st.form_submit_button("Create Agreement"):
                if not f_driver or f_base <= 0:
                    st.error("❌ Driver and amount required.")
                else:
                    total_pay = f_base * (1 + (f_rate / 100))
                    fridays = []
                    d = pd.to_datetime(f_date)
                    while len(fridays) < 4:
                        d += timedelta(days=1)
                        if d.weekday() == 4:
                            fridays.append(d.strftime('%Y-%m-%d'))
                    
                    try:
                        ws_fin = get_ws("EXPENSE_FINANCING")
                        new_row = [f"FIN-{int(datetime.now().timestamp())}", f_driver, f_truck, f_concept, total_pay, 0] + fridays
                        ws_fin.append_row(new_row)
                        st.success("✅ Financing agreement created!")
                        st.cache_data.clear()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
    
    with col_fin2:
        st.markdown("<h5 style='color:#1E293B; margin-bottom:15px;'>Record Payment</h5>", unsafe_allow_html=True)
        
        if not expense_fin.empty:
            fin_paid_col = get_col("EXPENSE_FINANCING", "installments_paid")
            fin_total_col = get_col("EXPENSE_FINANCING", "total_to_pay")
            active = expense_fin[expense_fin[fin_paid_col].astype(float) < expense_fin[fin_total_col].astype(float)]
            
            if not active.empty:
                with st.form("form_fin_payment", clear_on_submit=True):
                    fin_driver_col = get_col("EXPENSE_FINANCING", "driver")
                    fin_id_col = get_col("EXPENSE_FINANCING", "id_fin")
                    fin_concept_col = get_col("EXPENSE_FINANCING", "concept")
                    
                    opts = active.apply(lambda r: f"{r[fin_driver_col]} ({r[fin_concept_col]}) | {r[fin_id_col]}", axis=1).tolist()
                    sel = st.selectbox("Agreement", opts)
                    sel_id = sel.split(" | ")[1]
                    
                    amount = st.number_input("Payment (USD)", min_value=0.0, step=50.0)
                    if st.form_submit_button("Apply"):
                        if amount <= 0:
                            st.error("❌ Amount > 0 required.")
                        else:
                            try:
                                ws_fin = get_ws("EXPENSE_FINANCING")
                                cell = ws_fin.find(sel_id)
                                current_paid = safe_float(ws_fin.cell(cell.row, 6).value or 0)
                                total_val = safe_float(ws_fin.cell(cell.row, 5).value or 0)
                                new_paid = min(current_paid + amount, total_val)
                                ws_fin.update_cell(cell.row, 6, new_paid)
                                st.success(f"✅ Payment applied: ${new_paid:,.2f} of ${total_val:,.2f}")
                                st.cache_data.clear()
                            except Exception as e:
                                st.error(f"❌ Error: {e}")
            else:
                st.info("ℹ️ All financing agreements paid.")
        else:
            st.info("ℹ️ No financing records.")
    
    st.divider()
    st.markdown("### Active Agreements")
    
    if not expense_fin.empty:
        fin_total_col = get_col("EXPENSE_FINANCING", "total_to_pay")
        fin_paid_col = get_col("EXPENSE_FINANCING", "installments_paid")
        
        for _, row in expense_fin.iterrows():
            total_val = safe_float(row[fin_total_col])
            paid = safe_float(row[fin_paid_col])
            debt = max(0, total_val - paid)
            pct = min(100, (paid / total_val * 100)) if total_val > 0 else 0
            
            fin_driver_col = get_col("EXPENSE_FINANCING", "driver")
            fin_truck_col = get_col("EXPENSE_FINANCING", "truck_id")
            fin_concept_col = get_col("EXPENSE_FINANCING", "concept")
            fin_id_col = get_col("EXPENSE_FINANCING", "id_fin")
            
            card = f"""
            <div class="financing-card-container">
                <div class="financing-card-header">
                    <div>
                        <span class="financing-card-driver">{row[fin_driver_col]}</span>
                        <span class="financing-card-meta"> | {row[fin_truck_col]}</span>
                    </div>
                    <span class="financing-card-id">{row[fin_id_col]}</span>
                </div>
                <div class="financing-grid">
                    <div>
                        <div class="financing-metric-label">Total Financed</div>
                        <div class="financing-metric-value">{money(total_val)}</div>
                        <div class="financing-metric-sub">{row[fin_concept_col]}</div>
                    </div>
                    <div>
                        <div class="financing-metric-label">Collected</div>
                        <div class="financing-metric-value">{money(paid)}</div>
                        <div class="financing-metric-sub">{pct:.1f}%</div>
                    </div>
                    <div>
                        <div class="financing-metric-label">Balance</div>
                        <div class="financing-metric-value highlighted">{money(debt)}</div>
                        <div class="financing-metric-sub">{"Complete" if debt == 0 else "Active"}</div>
                    </div>
                </div>
            </div>
            """
            st.markdown(card, unsafe_allow_html=True)

# ====================================
# TAB 9: TRUCK PAYMENTS
# ====================================

with tabs[9]:
    st.subheader("Truck Financing & Equity Tracking")
    st.caption("Track truck purchases and weekly amortization payments.")
    
    col_truck1, col_truck2 = st.columns(2)
    
    with col_truck1:
        with st.form("form_truck", clear_on_submit=True):
            st.markdown("<h5 style='color:#1E293B; margin-bottom:15px;'>New Truck Financing</h5>", unsafe_allow_html=True)
            t_driver = st.text_input("Driver").strip()
            t_truck = st.text_input("Truck ID/VIN").strip()
            t_value = st.number_input("Total Value (USD)", min_value=0.0, step=1000.0)
            t_amort = st.number_input("Weekly Amortization (USD)", min_value=0.0, step=50.0)
            t_date = st.date_input("Start Date", datetime.today())
            
            if st.form_submit_button("Register"):
                if not t_driver or t_value <= 0 or t_amort <= 0:
                    st.error("❌ All fields required.")
                else:
                    try:
                        ws_truck = get_ws("TRUCK_PAYMENTS")
                        new_row = [t_driver, t_truck, t_value, t_amort, 0, t_date.strftime('%Y-%m-%d')]
                        ws_truck.append_row(new_row)
                        st.success(f"✅ Truck {t_truck} registered!")
                        st.cache_data.clear()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
    
    with col_truck2:
        st.markdown("<h5 style='color:#1E293B; margin-bottom:15px;'>Record Amortization</h5>", unsafe_allow_html=True)
        
        if not truck_pay.empty:
            truck_total_col = get_col("TRUCK_PAYMENTS", "total_value")
            truck_paid_col = get_col("TRUCK_PAYMENTS", "total_paid")
            active_trucks = truck_pay[truck_pay[truck_paid_col].astype(float) < truck_pay[truck_total_col].astype(float)]
            
            if not active_trucks.empty:
                with st.form("form_truck_pay", clear_on_submit=True):
                    truck_driver_col = get_col("TRUCK_PAYMENTS", "driver")
                    truck_id_col = get_col("TRUCK_PAYMENTS", "truck_id")
                    
                    opts = active_trucks.apply(lambda r: f"{r[truck_driver_col]} - {r[truck_id_col]}", axis=1).tolist()
                    sel = st.selectbox("Truck", opts)
                    
                    payment = st.number_input("Payment (USD)", min_value=0.0, step=50.0)
                    if st.form_submit_button("Apply"):
                        if payment <= 0:
                            st.error("❌ Amount > 0.")
                        else:
                            try:
                                truck_name = sel.split(" - ")[1]
                                ws_truck = get_ws("TRUCK_PAYMENTS")
                                cell = ws_truck.find(truck_name)
                                current_paid = safe_float(ws_truck.cell(cell.row, 5).value or 0)
                                total = safe_float(ws_truck.cell(cell.row, 3).value or 0)
                                new_paid = min(current_paid + payment, total)
                                ws_truck.update_cell(cell.row, 5, new_paid)
                                st.success(f"✅ ${new_paid:,.2f} of ${total:,.2f}")
                                st.cache_data.clear()
                            except Exception as e:
                                st.error(f"❌ Error: {e}")
            else:
                st.info("ℹ️ All trucks paid.")
        else:
            st.info("ℹ️ No truck records.")
    
    st.divider()
    st.markdown("### Truck Equity Portfolios")
    
    if not truck_pay.empty:
        truck_total_col = get_col("TRUCK_PAYMENTS", "total_value")
        truck_paid_col = get_col("TRUCK_PAYMENTS", "total_paid")
        truck_amort_col = get_col("TRUCK_PAYMENTS", "weekly_amortization")
        truck_driver_col = get_col("TRUCK_PAYMENTS", "driver")
        truck_id_col = get_col("TRUCK_PAYMENTS", "truck_id")
        truck_date_col = get_col("TRUCK_PAYMENTS", "start_date")
        
        for _, row in truck_pay.iterrows():
            t_val = safe_float(row[truck_total_col])
            t_paid = safe_float(row[truck_paid_col])
            t_rem = max(0, t_val - t_paid)
            pct = min(100, (t_paid / t_val * 100)) if t_val > 0 else 0
            
            card = f"""
            <div class="financing-card-container">
                <div class="financing-card-header">
                    <div>
                        <span class="financing-card-driver">{row[truck_driver_col]}</span>
                        <span class="financing-card-meta"> | Purchase</span>
                    </div>
                    <span class="financing-card-id">{row[truck_id_col]}</span>
                </div>
                <div class="financing-grid">
                    <div>
                        <div class="financing-metric-label">Asset Value</div>
                        <div class="financing-metric-value">{money(t_val)}</div>
                        <div class="financing-metric-sub">${safe_float(row[truck_amort_col]):,.2f}/wk</div>
                    </div>
                    <div>
                        <div class="financing-metric-label">Equity Paid</div>
                        <div class="financing-metric-value">{money(t_paid)}</div>
                        <div class="financing-metric-sub">{pct:.1f}%</div>
                    </div>
                    <div>
                        <div class="financing-metric-label">Remaining</div>
                        <div class="financing-metric-value highlighted">{money(t_rem)}</div>
                        <div class="financing-metric-sub">{row[truck_date_col]}</div>
                    </div>
                </div>
            </div>
            """
            st.markdown(card, unsafe_allow_html=True)
            st.progress(min(1.0, pct / 100))

# ====================================
# TAB 10: DISPATCH TRACKER - ✅ CORREGIDO
# ====================================

with tabs[10]:
    st.subheader("Personal Account Ledger")
    st.caption("Track credits and payments for personnel.")
    
    col_p1, col_p2 = st.columns([1, 1])
    
    with col_p1:
        with st.form("form_account", clear_on_submit=True):
            st.markdown("<h5 style='color:#1E293B;'>New Movement</h5>", unsafe_allow_html=True)
            p_name = st.selectbox("Person", ["Ernesto Moran", "Other"])
            p_type = st.radio("Type", ["Credit (Saldo a favor)", "Payment (Débito)"])
            p_concept = st.text_input("Concept").strip()
            p_amount = st.number_input("Amount (USD)", min_value=0.0, step=10.0)
            p_date = st.date_input("Date", datetime.today())
            
            if st.form_submit_button("Post"):
                if not p_concept or p_amount <= 0:
                    st.error("❌ Concept and amount required.")
                else:
                    valor = p_amount if "Credit" in p_type else -p_amount
                    try:
                        ws_disp = get_ws("DISPATCH_TRACKER")
                        disp_date_col = get_col("DISPATCH_TRACKER", "date")
                        disp_month_col = get_col("DISPATCH_TRACKER", "month")
                        disp_concept_col = get_col("DISPATCH_TRACKER", "concept")
                        disp_amount_col = get_col("DISPATCH_TRACKER", "amount")
                        disp_type_col = get_col("DISPATCH_TRACKER", "type")
                        
                        new_row = [
                            p_date.strftime('%Y-%m-%d'),
                            p_date.strftime('%B'),
                            p_concept,
                            valor,
                            "Credit" if valor > 0 else "Debit"
                        ]
                        ws_disp.append_row(new_row)
                        st.success("✅ Movement recorded!")
                        st.cache_data.clear()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
    
    with col_p2:
        if not dispatch_track.empty:
            disp_date_col = get_col("DISPATCH_TRACKER", "date")
            disp_concept_col = get_col("DISPATCH_TRACKER", "concept")
            disp_amount_col = get_col("DISPATCH_TRACKER", "amount")
            
            # ✅ CORREGIDO: Usar nuevos nombres de columna después de renombrar
            df_acc = dispatch_track[[disp_date_col, disp_concept_col, disp_amount_col]].copy()
            df_acc.columns = ["Date", "Concept", "Amount"]
            df_acc["Amount"] = safe_to_numeric(df_acc["Amount"], errors='coerce').fillna(0)
            
            sel_concept = st.selectbox("Select Concept", df_acc["Concept"].unique())
            df_sel = df_acc[df_acc["Concept"] == sel_concept].sort_values("Date")
            df_sel["BALANCE"] = df_sel["Amount"].cumsum()
            
            saldo = safe_float(df_sel["BALANCE"].iloc[-1]) if len(df_sel) > 0 else 0
            color = "#10B981" if saldo >= 0 else "#EF4444"
            
            st.markdown(f"""
            <div style="background-color: #F8FAFC; padding: 15px; border-radius: 10px; border-left: 5px solid {color}; border: 1px solid #E2E8F0;">
                <h5 style="margin:0; color:#64748B;">Balance: {sel_concept}</h5>
                <p style="margin:5px 0 0 0; font-size: 28px; font-weight: bold; color:{color};">{money(saldo)}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("")
            fig = px.line(df_sel, x="Date", y="BALANCE", markers=True, title=f"Account History: {sel_concept}")
            fig.add_hline(y=0, line_dash="dash", line_color="gray")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("ℹ️ No records.")
    
    st.divider()
    st.markdown("### Historical Ledger")
    
    if not dispatch_track.empty:
        disp_date_col = get_col("DISPATCH_TRACKER", "date")
        st.dataframe(dispatch_track.sort_values(disp_date_col, ascending=False), width='stretch')
    else:
        st.info("ℹ️ No history.")


# ====================================
# TAB 11: ACCOUNTS PAYABLE / RECEIVABLE
# ====================================

with tabs[11]:
    st.subheader("Accounts Payable & Receivable Management")
    st.caption("Independent AP/AR module for MJ7 and GCI | Completely separate from Settlements")
    st.divider()
    
    # Company selector
    ap_ar_company = st.radio("Select Company:", ["MJ7 LOGISTICS", "GCI"], horizontal=True)
    st.divider()
    
    # Determine sheet names based on company
    if ap_ar_company == "MJ7 LOGISTICS":
        ap_sheet = "AP_MJ7"
        ar_sheet = "AR_MJ7"
    else:
        ap_sheet = "AP_GCI"
        ar_sheet = "AR_GCI"
    
    # Load AP/AR data with error handling
    try:
        sh = client.open(SHEET_NAME)
        ap_df = pd.DataFrame(sh.worksheet(ap_sheet).get_all_records())
        ar_df = pd.DataFrame(sh.worksheet(ar_sheet).get_all_records())
    except Exception as e:
        st.error(f"❌ Error loading AP/AR data: {e}")
        ap_df = pd.DataFrame()
        ar_df = pd.DataFrame()
    
    def get_column_index_ap_ar(ws, sheet_name, logical_col_name):
        """Obtener índice dinámico de columna en AP/AR sheets."""
        try:
            header_row = ws.row_values(1)
            actual_col_name = get_col(sheet_name, logical_col_name)
            return header_row.index(actual_col_name) + 1
        except (ValueError, IndexError):
            raise ValueError(f"Column '{actual_col_name}' not found in {sheet_name}")
    
    # Create tabs for AP and AR
    ap_tab, ar_tab = st.tabs(["📤 ACCOUNTS PAYABLE", "📥 ACCOUNTS RECEIVABLE"])
    
    # ====================================
    # ACCOUNTS PAYABLE TAB
    # ====================================
    
    with ap_tab:
        st.markdown(render_ap_ar_header(ap_ar_company, is_payable=True), unsafe_allow_html=True)
        
        # Calculate metrics
        if not ap_df.empty:
            ap_df_clean = ap_df.copy()
            ap_df_clean['AMOUNT'] = pd.to_numeric(ap_df_clean['AMOUNT'], errors='coerce').fillna(0)
            ap_df_clean['DUE_DATE'] = pd.to_datetime(ap_df_clean['DUE_DATE'], errors='coerce')
            ap_metrics = calculate_ap_ar_metrics(ap_df_clean, today)
        else:
            ap_metrics = calculate_ap_ar_metrics(pd.DataFrame(), today)
        
        # Display metrics
        st.markdown(render_metrics_grid(ap_metrics), unsafe_allow_html=True)
        
        st.markdown("---")
        
        # New AP Entry Form
        st.markdown("### 📝 Register New Supplier Invoice")
        
        col_ap1, col_ap2 = st.columns(2)
        
        with col_ap1:
            with st.form("ap_entry_form", clear_on_submit=True):
                ap_supplier = st.text_input("Supplier Name").strip()
                ap_invoice = st.text_input("Invoice Number").strip()
                ap_description = st.text_area("Description", height=80).strip()
                
                ap_amount = st.number_input("Invoice Amount ($)", min_value=0.0, step=100.0, key="ap_amount_input")
                ap_date = st.date_input("Invoice Date", today, key="ap_date_input")
                ap_due_date = st.date_input("Due Date", today, key="ap_due_date_input")
                ap_notes = st.text_input("Notes (optional)", key="ap_notes_input")
                
                if st.form_submit_button("Register Invoice", use_container_width=True):
                    if not ap_supplier or not ap_invoice:
                        st.error("❌ Supplier and Invoice Number required.")
                    elif ap_amount <= 0:
                        st.error("❌ Amount must be greater than 0.")
                    else:
                        try:
                            ws_ap = get_ws(ap_sheet)
                            ap_id = f"AP-{int(datetime.now().timestamp())}"
                            new_row = [
                                ap_id,
                                str(ap_date),
                                ap_supplier,
                                ap_invoice,
                                ap_description,
                                safe_float(ap_amount),
                                str(ap_due_date),
                                "PENDING",
                                "",
                                ap_notes
                            ]
                            ws_ap.append_row(new_row)
                            st.success(f"✅ Invoice {ap_invoice} registered successfully!")
                            st.cache_data.clear()
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
        
        st.markdown("---")
        
        # Display AP Data
        st.markdown("### 📊 Payables Registry")
        
        if not ap_df.empty:
            # Create display dataframe
            ap_display = ap_df.copy()
            
            # Format columns
            if 'AMOUNT' in ap_display.columns:
                ap_display['AMOUNT'] = ap_display['AMOUNT'].apply(lambda x: money(safe_float(x)))
            
            # Select columns to display
            display_cols = ['ID', 'DATE', 'SUPPLIER', 'INVOICE_NUMBER', 'DESCRIPTION', 'AMOUNT', 'DUE_DATE', 'STATUS', 'PAYMENT_DATE', 'NOTES']
            available_cols = [col for col in display_cols if col in ap_display.columns]
            
            st.dataframe(
                ap_display[available_cols],
                width='stretch',
                hide_index=True
            )
            
            # Mark as paid section
            st.markdown("---")
            st.markdown("### ✅ Record Payment")
            
            col_pay1, col_pay2 = st.columns([2, 1])
            
            with col_pay1:
                pending_ap = ap_df[ap_df.get('STATUS', '') == 'PENDING']
                if not pending_ap.empty:
                    ap_options = []
                    for _, row in pending_ap.iterrows():
                        inv_num = row.get('INVOICE_NUMBER', 'N/A')
                        supplier = row.get('SUPPLIER', 'N/A')
                        amount = money(safe_float(row.get('AMOUNT', 0)))
                        ap_options.append(f"{inv_num} - {supplier} - {amount}")
                    
                    selected_ap = st.selectbox("Select Invoice to Mark Paid:", ap_options, key="select_ap_payment")
                    
                    with col_pay2:
                        payment_date_ap = st.date_input("Payment Date", today, key="ap_payment_date")
                    
                    if st.button("Mark as PAID", use_container_width=True, key="btn_mark_ap_paid"):
                        try:
                            selected_invoice = selected_ap.split(" - ")[0]
                            ws_ap = get_ws(ap_sheet)
                            
                            # Find row by invoice number
                            cell = ws_ap.find(selected_invoice)
                            if cell:
                                status_col_idx = get_column_index_ap_ar(ws_ap, ap_sheet, "status")
                                payment_date_col_idx = get_column_index_ap_ar(ws_ap, ap_sheet, "payment_date")
                                
                                # Update STATUS to PAID
                                ws_ap.update_cell(cell.row, status_col_idx, "PAID")
                                
                                # Update PAYMENT_DATE
                                ws_ap.update_cell(cell.row, payment_date_col_idx, str(payment_date_ap))
                                
                                st.success("✅ Invoice marked as PAID!")
                                st.cache_data.clear()
                            else:
                                st.error("❌ Invoice not found.")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                else:
                    st.info("ℹ️ All invoices are paid.")
        else:
            st.info("ℹ️ No supplier invoices registered yet.")
        
        # Aged Report
        st.markdown("---")
        st.markdown("### 📈 Aged Payables Report")
        
        if not ap_df.empty and len(ap_df) > 0:
            aged_ap = get_aged_report(ap_df, today)
            
            if not aged_ap.empty and len(aged_ap) > 0:
                aged_summary = aged_ap.groupby('AGING_BUCKET').agg({
                    'AMOUNT': ['sum', 'count']
                }).round(2)
                
                aged_summary.columns = ['Total Amount', 'Count']
                aged_summary['Total Amount'] = aged_summary['Total Amount'].apply(money)
                
                st.dataframe(aged_summary, width='stretch')
            else:
                st.info("ℹ️ No overdue payables.")
        else:
            st.info("ℹ️ No data.")
    
    # ====================================
    # ACCOUNTS RECEIVABLE TAB
    # ====================================
    
    with ar_tab:
        st.markdown(render_ap_ar_header(ap_ar_company, is_payable=False), unsafe_allow_html=True)
        
        # Calculate metrics
        if not ar_df.empty:
            ar_df_clean = ar_df.copy()
            ar_df_clean['AMOUNT'] = pd.to_numeric(ar_df_clean['AMOUNT'], errors='coerce').fillna(0)
            ar_df_clean['DUE_DATE'] = pd.to_datetime(ar_df_clean['DUE_DATE'], errors='coerce')
            ar_metrics = calculate_ap_ar_metrics(ar_df_clean, today)
        else:
            ar_metrics = calculate_ap_ar_metrics(pd.DataFrame(), today)
        
        # Display metrics
        st.markdown(render_metrics_grid(ar_metrics), unsafe_allow_html=True)
        
        st.markdown("---")
        
        # New AR Entry Form
        st.markdown("### 📝 Register New Client Invoice")
        
        col_ar1, col_ar2 = st.columns(2)
        
        with col_ar1:
            with st.form("ar_entry_form", clear_on_submit=True):
                ar_client = st.text_input("Client Name").strip()
                ar_invoice = st.text_input("Invoice Number").strip()
                ar_description = st.text_area("Description", height=80).strip()
                
                ar_amount = st.number_input("Invoice Amount ($)", min_value=0.0, step=100.0, key="ar_amount_input")
                ar_date = st.date_input("Invoice Date", today, key="ar_date_input")
                ar_due_date = st.date_input("Due Date", today, key="ar_due_date_input")
                ar_notes = st.text_input("Notes (optional)", key="ar_notes_input")
                
                if st.form_submit_button("Register Invoice", use_container_width=True):
                    if not ar_client or not ar_invoice:
                        st.error("❌ Client and Invoice Number required.")
                    elif ar_amount <= 0:
                        st.error("❌ Amount must be greater than 0.")
                    else:
                        try:
                            ws_ar = get_ws(ar_sheet)
                            ar_id = f"AR-{int(datetime.now().timestamp())}"
                            new_row = [
                                ar_id,
                                str(ar_date),
                                ar_client,
                                ar_invoice,
                                ar_description,
                                safe_float(ar_amount),
                                str(ar_due_date),
                                "PENDING",
                                "",
                                ar_notes
                            ]
                            ws_ar.append_row(new_row)
                            st.success(f"✅ Invoice {ar_invoice} registered successfully!")
                            st.cache_data.clear()
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
        
        st.markdown("---")
        
        # Display AR Data
        st.markdown("### 📊 Receivables Registry")
        
        if not ar_df.empty:
            # Create display dataframe
            ar_display = ar_df.copy()
            
            # Format columns
            if 'AMOUNT' in ar_display.columns:
                ar_display['AMOUNT'] = ar_display['AMOUNT'].apply(lambda x: money(safe_float(x)))
            
            # Select columns to display
            display_cols = ['ID', 'DATE', 'CLIENT', 'INVOICE_NUMBER', 'DESCRIPTION', 'AMOUNT', 'DUE_DATE', 'STATUS', 'PAYMENT_DATE', 'NOTES']
            available_cols = [col for col in display_cols if col in ar_display.columns]
            
            st.dataframe(
                ar_display[available_cols],
                width='stretch',
                hide_index=True
            )
            
            # Mark as paid section
            st.markdown("---")
            st.markdown("### ✅ Record Payment")
            
            col_pay1, col_pay2 = st.columns([2, 1])
            
            with col_pay1:
                pending_ar = ar_df[ar_df.get('STATUS', '') == 'PENDING']
                if not pending_ar.empty:
                    ar_options = []
                    for _, row in pending_ar.iterrows():
                        inv_num = row.get('INVOICE_NUMBER', 'N/A')
                        client = row.get('CLIENT', 'N/A')
                        amount = money(safe_float(row.get('AMOUNT', 0)))
                        ar_options.append(f"{inv_num} - {client} - {amount}")
                    
                    selected_ar = st.selectbox("Select Invoice to Mark Paid:", ar_options, key="select_ar_payment")
                    
                    with col_pay2:
                        payment_date_ar = st.date_input("Payment Date", today, key="ar_payment_date")
                    
                    if st.button("Mark as PAID", use_container_width=True, key="btn_mark_ar_paid"):
                        try:
                            selected_invoice = selected_ar.split(" - ")[0]
                            ws_ar = get_ws(ar_sheet)
                            
                            # Find row by invoice number
                            cell = ws_ar.find(selected_invoice)
                            if cell:
                                status_col_idx = get_column_index_ap_ar(ws_ar, ar_sheet, "status")
                                payment_date_col_idx = get_column_index_ap_ar(ws_ar, ar_sheet, "payment_date")
                                
                                # Update STATUS to PAID
                                ws_ar.update_cell(cell.row, status_col_idx, "PAID")
                                
                                # Update PAYMENT_DATE
                                ws_ar.update_cell(cell.row, payment_date_col_idx, str(payment_date_ar))
                                
                                st.success("✅ Invoice marked as PAID!")
                                st.cache_data.clear()
                            else:
                                st.error("❌ Invoice not found.")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                else:
                    st.info("ℹ️ All invoices are paid.")
        else:
            st.info("ℹ️ No client invoices registered yet.")
        
        # Aged Report
        st.markdown("---")
        st.markdown("### 📈 Aged Receivables Report")
        
        if not ar_df.empty and len(ar_df) > 0:
            aged_ar = get_aged_report(ar_df, today)
            
            if not aged_ar.empty and len(aged_ar) > 0:
                aged_summary = aged_ar.groupby('AGING_BUCKET').agg({
                    'AMOUNT': ['sum', 'count']
                }).round(2)
                
                aged_summary.columns = ['Total Amount', 'Count']
                aged_summary['Total Amount'] = aged_summary['Total Amount'].apply(money)
                
                st.dataframe(aged_summary, width='stretch')
            else:
                st.info("ℹ️ No overdue receivables.")
        else:
            st.info("ℹ️ No data.")

# ====================================
# FOOTER
# ====================================

st.divider()
st.caption("🚛 MJ7 Logistics Control Center v5.0 | Powered by Streamlit + Google Sheets | Last Updated: 2024")

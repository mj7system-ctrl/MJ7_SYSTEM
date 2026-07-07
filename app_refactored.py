# app_refactored.py
"""
MJ7 LOGISTICS CONTROL CENTER - REFACTORED & MODULAR
====================================================
Versión 5.0: Arquitectura limpia, segura y mantenible
CON MÓDULO AP/AR INTEGRADO
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
    
    # Cargar hojas opcionales con fallback
    try:
        expense_fin = pd.DataFrame(sh.worksheet("EXPENSE_FINANCIAMIENTOS").get_all_records())
    except Exception:
        expense_fin = pd.DataFrame(columns=[get_col("EXPENSE_FINANCIAMIENTOS", k) 
                                            for k in COLUMN_MAPS["EXPENSE_FINANCIAMIENTOS"].values()])
    
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
        for col in ["DATE", "START_DATE", "DELIVERY_DATE"]:
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
# TAB 0: LOADS
# ====================================

with tabs[0]:
    st.subheader("General Loads Registry")
    st.dataframe(loads, use_container_width=True)

# ====================================
# TAB 1: SETTLEMENTS
# ====================================

with tabs[1]:
    st.subheader("Closed Settlements History")
    st.dataframe(settlements, use_container_width=True)

# ====================================
# TAB 2: PERFORMANCE & CARD GENERATOR
# ====================================

with tabs[2]:
    st.subheader("Driver Performance Overview")
    st.dataframe(drivers, use_container_width=True)
    
    if not settlements.empty:
        st.markdown("---")
        st.subheader("Production Metrics Matrix")
        
        # ✅ ARREGLADO: date_col siempre definido
        date_col = get_col("SETTLEMENTS", "date")
        settlements[date_col] = pd.to_datetime(settlements[date_col])
        
        col_date1, col_date2 = st.columns([1, 2])
        with col_date1:
            filter_type = st.radio("Filter views:", ["All Time", "Specific Day"], horizontal=True)
        
        selected_date = None
        settlements_filtered = settlements.copy()
        
        if filter_type == "Specific Day":
            with col_date2:
                selected_date = st.date_input("Select target date:", value=settlements[date_col].max().date())
            settlements_filtered = settlements_filtered[settlements_filtered[date_col].dt.date == selected_date]
        
        if not settlements_filtered.empty:
            load_col = get_col("SETTLEMENTS", "load_id")
            gross_col = get_col("SETTLEMENTS", "gross")
            owner_col = get_col("SETTLEMENTS", "owner_pay")
            mj7_col = get_col("SETTLEMENTS", "mj7_net")
            driver_col = get_col("SETTLEMENTS", "driver_id")
            
            performance_matrix = settlements_filtered.groupby([driver_col, load_col]).agg({
                gross_col: "sum",
                owner_col: "sum",
                mj7_col: "sum"
            }).reset_index()
            
            st.dataframe(
                performance_matrix.style.format({
                    gross_col: "${:,.2f}",
                    owner_col: "${:,.2f}",
                    mj7_col: "${:,.2f}"
                }),
                use_container_width=True
            )
            
            st.markdown("---")
            st.subheader("Generate Performance Cards")
            target_perf_drivers = st.multiselect(
                "Select drivers to generate cards:",
                performance_matrix[driver_col].unique()
            )
            
            if target_perf_drivers:
                try:
                    with open("logo.jpeg", "rb") as image_file:
                        encoded_logo = base64.b64encode(image_file.read()).decode()
                    logo_html_tag = f'<img src="data:image/jpeg;base64,{encoded_logo}" style="height: 36px; border-radius: 4px; border: 1px solid #E2E8F0;">'
                except Exception:
                    logo_html_tag = ''
                
                def generate_reportlab_pdf(title_suffix, driver_id, name_str, date_str, gross, owner_pay, mj7_net):
                    """Generar PDF con ReportLab."""
                    pdf_buffer = io.BytesIO()
                    doc = SimpleDocTemplate(
                        pdf_buffer,
                        pagesize=(600, 260),
                        rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20
                    )
                    
                    styles = getSampleStyleSheet()
                    title_style = ParagraphStyle(
                        'CardTitle', fontName='Helvetica-Bold', fontSize=14, leading=16,
                        textColor=colors.HexColor("#1E293B")
                    )
                    info_style = ParagraphStyle(
                        'DriverInfo', fontName='Helvetica-Bold', fontSize=11, leading=14,
                        textColor=colors.HexColor("#334155")
                    )
                    label_style = ParagraphStyle(
                        'MetricLabel', fontName='Helvetica-Bold', fontSize=9, leading=11,
                        textColor=colors.HexColor("#64748B")
                    )
                    value_style = ParagraphStyle(
                        'MetricValue', fontName='Helvetica-Bold', fontSize=18, leading=22,
                        textColor=colors.HexColor("#1E293B")
                    )
                    net_label_style = ParagraphStyle(
                        'NetLabel', fontName='Helvetica-Bold', fontSize=9, leading=11,
                        textColor=colors.HexColor("#1E40AF")
                    )
                    net_value_style = ParagraphStyle(
                        'NetValue', fontName='Helvetica-Bold', fontSize=18, leading=22,
                        textColor=colors.HexColor("#1D4ED8")
                    )
                    
                    story = []
                    
                    # Header
                    header_text = f"<b>MJ7 LOGISTICS CENTER — {title_suffix}</b><br/><font color='#64748B'>Date: {date_str}</font>"
                    header_p = Paragraph(header_text, title_style)
                    header_data = [[header_p, ""]]
                    
                    if os.path.exists("logo.jpeg"):
                        try:
                            logo_img = RLImage("logo.jpeg", width=70, height=35)
                            header_data = [[header_p, logo_img]]
                        except:
                            pass
                    
                    header_table = Table(header_data, colWidths=[470, 90])
                    header_table.setStyle(TableStyle([
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                        ('LINEBELOW', (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ]))
                    story.append(header_table)
                    story.append(Spacer(1, 12))
                    
                    # Driver info
                    info_p = Paragraph(f"DRIVER ID: {driver_id} &nbsp;&nbsp;|&nbsp;&nbsp; NAME: {name_str}", info_style)
                    info_table = Table([[info_p]], colWidths=[560])
                    info_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                        ('PADDING', (0, 0), (-1, -1), 8),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                    ]))
                    story.append(info_table)
                    story.append(Spacer(1, 15))
                    
                    # Metrics
                    box_gross = [
                        Paragraph("TOTAL GROSS", label_style),
                        Spacer(1, 8),
                        Paragraph(f"${gross:,.2f}", value_style)
                    ]
                    box_owner = [
                        Paragraph("OWNER PAY", label_style),
                        Spacer(1, 8),
                        Paragraph(f"${owner_pay:,.2f}", value_style)
                    ]
                    box_net = [
                        Paragraph("MJ7 NET PROFIT", net_label_style),
                        Spacer(1, 8),
                        Paragraph(f"${mj7_net:,.2f}", net_value_style)
                    ]
                    
                    metrics_table = Table([[box_gross, box_owner, box_net]], colWidths=[180, 180, 200])
                    metrics_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor("#F8FAFC")),
                        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor("#F8FAFC")),
                        ('BACKGROUND', (2, 0), (2, 0), colors.HexColor("#EFF6FF")),
                        ('BOX', (0, 0), (0, 0), 1, colors.HexColor("#E2E8F0")),
                        ('BOX', (1, 0), (1, 0), 1, colors.HexColor("#E2E8F0")),
                        ('BOX', (2, 0), (2, 0), 1, colors.HexColor("#BFDBFE")),
                        ('PADDING', (0, 0), (-1, -1), 12),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ]))
                    story.append(metrics_table)
                    
                    doc.build(story)
                    return pdf_buffer.getvalue()
                
                # Renderizar tarjetas
                for d_id in target_perf_drivers:
                    driver_loads = performance_matrix[performance_matrix[driver_col] == d_id]
                    
                    try:
                        d_name = drivers[drivers[get_col("DRIVERS", "driver_id")].astype(str) == str(d_id)][
                            get_col("DRIVERS", "full_name")
                        ].iloc[0]
                    except Exception:
                        d_name = "Unknown Driver"
                    
                    st.write(f"### Performance Report: {d_name} ({d_id})")
                    
                    # Tarjetas individuales
                    for _, load_row in driver_loads.iterrows():
                        current_load_id = load_row[load_col]
                        card_date_str = selected_date.strftime('%Y-%m-%d') if filter_type == "Specific Day" else datetime.now().strftime('%Y-%m-%d')
                        
                        card_html = render_load_card(
                            load_id=current_load_id,
                            driver_id=d_id,
                            driver_name=d_name,
                            date_str=card_date_str,
                            gross=safe_float(load_row[gross_col]),
                            owner_pay=safe_float(load_row[owner_col]),
                            mj7_net=safe_float(load_row[mj7_col]),
                            logo_html=logo_html_tag
                        )
                        st.markdown(card_html, unsafe_allow_html=True)
                        
                        pdf_data = generate_reportlab_pdf(
                            f"LOAD {current_load_id}", d_id, d_name, card_date_str,
                            safe_float(load_row[gross_col]),
                            safe_float(load_row[owner_col]),
                            safe_float(load_row[mj7_col])
                        )
                        st.download_button(
                            label=f"Export Load Card {current_load_id} (PDF)",
                            data=pdf_data,
                            file_name=f"MJ7_Load_{current_load_id}_{d_id}.pdf",
                            mime="application/pdf",
                            key=f"btn_pdf_{d_id}_{current_load_id}"
                        )
                    
                    # Resumen
                    if len(driver_loads) > 1:
                        total_gross = driver_loads[gross_col].sum()
                        total_owner = driver_loads[owner_col].sum()
                        total_net = driver_loads[mj7_col].sum()
                        
                        title_summary = "DAILY TOTALS" if filter_type == "Specific Day" else "ACCUMULATED TOTALS"
                        subtitle_summary = f"Summary of {len(driver_loads)} loads for {card_date_str}" if filter_type == "Specific Day" else f"Summary of {len(driver_loads)} loads"
                        
                        summary_html = f"""
                        <div style="background-color: #F1F5F9; border: 2px dashed #CBD5E1; border-radius: 12px; padding: 24px; margin-top: 15px; margin-bottom: 8px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #CBD5E1; padding-bottom: 16px; margin-bottom: 16px;">
                                <div>
                                    <h4 style="margin: 0; color: #0F172A; font-size: 14px; letter-spacing: 0.5px; font-weight: 800;">MJ7 LOGISTICS — {title_summary}</h4>
                                    <span style="font-size: 12px; color: #475569;">{subtitle_summary}</span>
                                </div>
                                {logo_html_tag}
                            </div>
                            <div style="background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px; padding: 10px 14px; font-size: 13px; color: #334155; margin-bottom: 20px;">
                                <span style="color: #64748B; font-weight: 600;">DRIVER ID:</span> <span style="font-weight: 700; color: #0F172A;">{d_id}</span> | 
                                <span style="color: #64748B; font-weight: 600;">NAME:</span> <span style="font-weight: 700; color: #0F172A;">{d_name}</span>
                            </div>
                            <table style="width: 100%; border-collapse: separate; border-spacing: 16px 0; margin-left: -16px; margin-right: -16px;">
                                <tr>
                                    <td style="width: 33.33%; background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 8px; padding: 14px; text-align: center;">
                                        <div style="font-size: 11px; text-transform: uppercase; color: #475569; font-weight: 700;">Gross Total</div>
                                        <div style="font-size: 22px; color: #0F172A; font-weight: 800;">{money(total_gross)}</div>
                                    </td>
                                    <td style="width: 33.33%; background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 8px; padding: 14px; text-align: center;">
                                        <div style="font-size: 11px; text-transform: uppercase; color: #475569; font-weight: 700;">Total Owner Pay</div>
                                        <div style="font-size: 22px; color: #0F172A; font-weight: 800;">{money(total_owner)}</div>
                                    </td>
                                    <td style="width: 33.33%; background-color: #2563EB; border: 1px solid #1D4ED8; border-radius: 8px; padding: 14px; text-align: center;">
                                        <div style="font-size: 11px; text-transform: uppercase; color: #FFFFFF; font-weight: 700;">Total Net Profit</div>
                                        <div style="font-size: 22px; color: #FFFFFF; font-weight: 800;">{money(total_net)}</div>
                                    </td>
                                </tr>
                            </table>
                        </div>
                        """
                        st.markdown(summary_html, unsafe_allow_html=True)
                        
                        summary_pdf_data = generate_reportlab_pdf(
                            title_summary, d_id, d_name, card_date_str,
                            total_gross, total_owner, total_net
                        )
                        st.download_button(
                            label=f"Export {title_summary.title()} Summary (PDF)",
                            data=summary_pdf_data,
                            file_name=f"MJ7_{title_summary}_{d_id}.pdf",
                            mime="application/pdf",
                            key=f"btn_pdf_total_{d_id}"
                        )
                    
                    st.markdown("<hr style='border: 1px dashed #E2E8F0;'>", unsafe_allow_html=True)
        else:
            st.warning("No data found for the selected date.")

# ====================================
# TAB 3: DEDUCTIONS
# ====================================

with tabs[3]:
    st.subheader("Expenses & Deductions Log")
    display_deductions = deductions.copy()
    
    qty_col = get_col("DEDUCTIONS", "qty_gallons")
    if qty_col in display_deductions.columns:
        display_deductions[qty_col] = safe_to_numeric(display_deductions[qty_col], errors='coerce')
        display_deductions[qty_col] = display_deductions[qty_col].apply(format_gallons)
    
    st.dataframe(display_deductions, use_container_width=True)

# ====================================
# TAB 4: DATA ENTRY (OPERATIONS)
# ====================================

with tabs[4]:
    st.subheader("Operations Management Module")
    flow = st.radio(
        "Select Action:",
        ["New Load", "Settle Load", "Modify / Re-Settle Load", "Register Deduction", "Add Driver"],
        horizontal=True
    )
    st.divider()
    
    # Helper para conectar a worksheets
    def get_ws(name):
        return client.open(SHEET_NAME).worksheet(name)
    
    # ============ NEW LOAD ============
    if flow == "New Load":
        col_x, col_y = st.columns(2)
        with col_x:
            l_num = st.text_input("Load Reference ID", value=st.session_state.form_load, placeholder="MJ7-XXXX")
            l_comp = st.text_input("Broker / Client Name", value=st.session_state.form_company)
            l_amt = st.number_input("Gross Amount ($)", value=st.session_state.form_amount or 0.0, format="%.2f", step=1.00)
            l_stat = st.selectbox("Status", ["PENDING", "IN TRANSIT", "DELIVERED", "CLOSED / SETTLED"])
        with col_y:
            l_orig = st.text_input("Origin", value=st.session_state.form_origin)
            l_dest = st.text_input("Destination", value=st.session_state.form_destination)
            driver_col_real = get_col("DRIVERS", "driver_id")
            d_options = ["Select Driver"] + sorted_unique_safe(drivers[driver_col_real]) if not drivers.empty else ["No drivers available"]
            l_driver = st.selectbox("Driver", d_options)
            l_sdate = st.date_input("Start Date", today)
            l_edate = st.date_input("Delivery Date", today)
        
        if st.button("Save Load"):
            # ✅ Validar con función
            is_valid, error = validate_load_data(l_num, l_comp, l_amt, l_driver)
            if not is_valid:
                st.error(f"❌ {error}")
            else:
                new_row = [l_num, l_comp, safe_float(l_amt), str(l_sdate), str(l_edate), l_stat, l_orig, l_dest, l_driver]
                get_ws("CARGAS").append_row(new_row)
                st.success("✅ Load registered successfully!")
                st.cache_data.clear()
    
    # ============ SETTLE LOAD ============
    elif flow == "Settle Load":
        load_id_col = get_col("CARGAS", "load_id")
        status_col = get_col("CARGAS", "status")
        amount_col = get_col("CARGAS", "amount")
        driver_col = get_col("CARGAS", "driver_id")
        
        active_loads = loads[loads[status_col] != "CLOSED / SETTLED"][load_id_col].astype(str).unique()
        active_codes = ["Select Load"] + sorted(active_loads.tolist()) if len(active_loads) > 0 else ["No logs open"]
        chosen_load = st.selectbox("Select Load to Settle:", active_codes)
        
        if chosen_load not in ["Select Load", "No logs open"]:
            # ✅ Usar find_row_by_column (SEGURO)
            ops = SheetsOperations(client, SHEET_NAME)
            match = ops.find_row_by_column(loads, "CARGAS", "load_id", chosen_load)
            
            if match is not None:
                op_assigned = match[driver_col]
                gross_revenue = safe_float(match[amount_col])
                
                # Deductions
                load_num_col = get_col("DEDUCTIONS", "load_id")
                ded_type_col = get_col("DEDUCTIONS", "type")
                ded_amt_col = get_col("DEDUCTIONS", "amount")
                
                associated_costs = deductions[deductions[load_num_col].astype(str) == chosen_load]
                fuel_deductions = safe_float(associated_costs[associated_costs[ded_type_col] == "FUEL"][ded_amt_col].sum())
                other_deductions = safe_float(associated_costs[associated_costs[ded_type_col] == "OTHER"][ded_amt_col].sum())
                
                # ✅ Usar calculate_settlement (centralizado)
                aplicar_factoring = st.checkbox("Apply Factoring Fee (2.15%) to this load?", value=True)
                settlement = calculate_settlement(
                    gross_revenue=gross_revenue,
                    fuel_deductions=fuel_deductions,
                    other_deductions=other_deductions,
                    apply_factoring=aplicar_factoring
                )
                
                # ✅ Validar
                error = validate_settlement(settlement)
                if error:
                    st.error(f"❌ Settlement error: {error}")
                else:
                    # ✅ Renderizar preview (reutilizable)
                    st.markdown(render_settlement_preview(settlement), unsafe_allow_html=True)
                    
                    st.write("")
                    if not associated_costs.empty:
                        st.markdown("### Linked Deductions Breakdown")
                        df_view = associated_costs[[ded_type_col, "CONCEPT", ded_amt_col]].copy()
                        df_view.columns = ["Category", "Description", "Amount ($)"]
                        st.dataframe(df_view, use_container_width=True, hide_index=True)
                    else:
                        st.caption("No deductions found for this load.")
                    
                    st.divider()
                    
                    if st.button("Authorize Settlement", use_container_width=True):
                        ws_settlements = get_ws("SETTLEMENTS")
                        settle_load_col = get_col("SETTLEMENTS", "load_id")
                        
                        # Verificar que no esté ya liquidada
                        if chosen_load in ws_settlements.col_values(list(ws_settlements.row_values(1)).index(settle_load_col) + 1):
                            st.error("❌ This load has already been settled.")
                        else:
                            # ✅ Añadir settlement
                            l_date = datetime.now().strftime('%Y-%m-%d')
                            settle_date_col = get_col("SETTLEMENTS", "date")
                            settle_driver_col = get_col("SETTLEMENTS", "driver_id")
                            settle_gross_col = get_col("SETTLEMENTS", "gross")
                            settle_owner_col = get_col("SETTLEMENTS", "owner_pay")
                            settle_dispatch_col = get_col("SETTLEMENTS", "dispatch_fee")
                            settle_factoring_col = get_col("SETTLEMENTS", "factoring_fee")
                            settle_mj7_col = get_col("SETTLEMENTS", "mj7_net")
                            
                            new_settlement = [
                                l_date,
                                chosen_load,
                                str(op_assigned),
                                settlement.gross_revenue,
                                settlement.owner_final,
                                settlement.dispatch_fee,
                                settlement.factoring_fee,
                                settlement.mj7_final
                            ]
                            ws_settlements.append_row(new_settlement)
                            
                            # ✅ Actualizar status (SEGURO)
                            ws_loads = get_ws("CARGAS")
                            ops.update_cell_by_column(
                                ws=ws_loads,
                                df=loads,
                                sheet_name="CARGAS",
                                search_col="load_id",
                                search_value=chosen_load,
                                update_col="status",
                                new_value="CLOSED / SETTLED"
                            )
                            
                            st.success("✅ Settlement locked and saved!")
                            st.cache_data.clear()
            else:
                st.error("❌ Load not found.")
    
    # ============ MODIFY / RE-SETTLE ============
    elif flow == "Modify / Re-Settle Load":
        all_loads = ["Select Load"] + sorted(loads[load_id_col].astype(str).unique().tolist()) if not loads.empty else []
        edit_load_id = st.selectbox("Select load to modify:", all_loads)
        
        if edit_load_id and edit_load_id != "Select Load":
            load_match = ops.find_row_by_column(loads, "CARGAS", "load_id", edit_load_id)
            
            if load_match is not None:
                company_col = get_col("CARGAS", "company")
                e_comp = st.text_input("Broker / Client Name", value=load_match[company_col])
                e_amt = st.number_input("Gross Amount ($)", value=safe_float(load_match[amount_col]), format="%.2f")
                e_stat = st.selectbox("Status", ["PENDING", "IN TRANSIT", "DELIVERED", "CLOSED / SETTLED"],
                                     index=["PENDING", "IN TRANSIT", "DELIVERED", "CLOSED / SETTLED"].index(load_match[status_col]))
                
                driver_options = sorted_unique_safe(drivers[driver_col_real])
                e_driver = st.selectbox("Driver", driver_options, index=driver_options.index(str(load_match[driver_col])) if str(load_match[driver_col]) in driver_options else 0)
                
                if st.button("Update Load"):
                    ws_loads = get_ws("CARGAS")
                    ops.update_cell_by_column(
                        ws=ws_loads,
                        df=loads,
                        sheet_name="CARGAS",
                        search_col="load_id",
                        search_value=edit_load_id,
                        update_col="company",
                        new_value=e_comp
                    )
                    ops.update_cell_by_column(
                        ws=ws_loads,
                        df=loads,
                        sheet_name="CARGAS",
                        search_col="load_id",
                        search_value=edit_load_id,
                        update_col="amount",
                        new_value=safe_float(e_amt)
                    )
                    ops.update_cell_by_column(
                        ws=ws_loads,
                        df=loads,
                        sheet_name="CARGAS",
                        search_col="load_id",
                        search_value=edit_load_id,
                        update_col="status",
                        new_value=e_stat
                    )
                    ops.update_cell_by_column(
                        ws=ws_loads,
                        df=loads,
                        sheet_name="CARGAS",
                        search_col="load_id",
                        search_value=edit_load_id,
                        update_col="driver_id",
                        new_value=e_driver
                    )
                    st.success("✅ Load updated!")
                    st.cache_data.clear()
    
    # ============ REGISTER DEDUCTION ============
    elif flow == "Register Deduction":
        driver_pool = sorted_unique_safe(drivers[driver_col_real]) if not drivers.empty else []
        selected_driver = st.selectbox("Filter by Driver:", ["Select Driver"] + driver_pool)
        
        if selected_driver != "Select Driver":
            carga_driver_col = get_col("CARGAS", "driver_id")
            allowed_loads = loads[loads[carga_driver_col].astype(str) == selected_driver][load_id_col].astype(str).unique()
            
            if len(allowed_loads) > 0:
                with st.form("deductions_entry_form", clear_on_submit=True):
                    g1, g2 = st.columns(2)
                    with g1:
                        d_fdate = st.date_input("Date", today)
                        d_cload = st.selectbox("Link to Load", allowed_loads)
                        d_clog = st.selectbox("Category", ["FUEL", "OTHER"])
                        d_desc = st.text_input("Memo")
                    with g2:
                        d_gal = st.number_input("Gallons", min_value=0.0, step=0.01) if d_clog == "FUEL" else 0.0
                        d_vcost = st.number_input("Total Amount ($)", min_value=0.0, step=1.00, format="%.2f")
                    
                    if st.form_submit_button("Save Deduction"):
                        ded_date_col = get_col("DEDUCTIONS", "date")
                        ded_load_col = get_col("DEDUCTIONS", "load_id")
                        ded_driver_col = get_col("DEDUCTIONS", "driver_id")
                        ded_type_col = get_col("DEDUCTIONS", "type")
                        ded_concept_col = get_col("DEDUCTIONS", "concept")
                        ded_qty_col = get_col("DEDUCTIONS", "qty_gallons")
                        ded_posted_col = get_col("DEDUCTIONS", "posted_date")
                        ded_amount_col = get_col("DEDUCTIONS", "amount")
                        
                        new_ded = [
                            str(d_fdate),
                            d_cload,
                            selected_driver,
                            d_clog,
                            d_desc,
                            safe_float(d_gal),
                            str(today),
                            safe_float(d_vcost)
                        ]
                        get_ws("DEDUCTIONS").append_row(new_ded)
                        st.success("✅ Deduction saved!")
                        st.cache_data.clear()
                
                st.write("")
                st.markdown("### Existing Deductions for This Driver")
                current_driver_deds = deductions[deductions[get_col("DEDUCTIONS", "driver_id")].astype(str) == selected_driver]
                if not current_driver_deds.empty:
                    df_view = current_driver_deds[[
                        get_col("DEDUCTIONS", "date"),
                        get_col("DEDUCTIONS", "load_id"),
                        get_col("DEDUCTIONS", "type"),
                        get_col("DEDUCTIONS", "concept"),
                        get_col("DEDUCTIONS", "amount")
                    ]].copy()
                    df_view.columns = ["Date", "Load ID", "Type", "Concept", "Amount ($)"]
                    st.dataframe(df_view, use_container_width=True, hide_index=True)
                else:
                    st.caption("No deductions yet.")
    
    # ============ ADD DRIVER ============
    elif flow == "Add Driver":
        with st.form("driver_addition_form", clear_on_submit=True):
            f1, f2 = st.columns(2)
            with f1:
                new_id = st.text_input("Driver ID", placeholder="DRV-XX")
                new_name = st.text_input("Full Name")
            with f2:
                new_phone = st.text_input("Phone Number")
                new_ops = st.selectbox("Operational Status", ["ACTIVE", "ON LEAVE", "INACTIVE"])
            
            if st.form_submit_button("Save Driver"):
                if not new_id or not new_name:
                    st.error("❌ Driver ID and Full Name are required.")
                else:
                    new_d = [new_id, new_name, new_phone, new_ops, str(today)]
                    get_ws("DRIVERS").append_row(new_d)
                    st.success("✅ Driver registered!")
                    st.cache_data.clear()

# ====================================
# TAB 5: SEARCH ENGINE
# ====================================

with tabs[5]:
    st.subheader("Dynamic Search Engine")
    st.caption("Search across registries by load or driver.")
    st.markdown("---")
    
    col_search_type, col_search_input = st.columns([1, 2])
    
    with col_search_type:
        search_mode = st.radio("Search By:", ["Load ID", "Driver ID"], horizontal=False)
    
    with col_search_input:
        if search_mode == "Load ID":
            query_string = st.text_input("Enter Load ID:", placeholder="e.g., 4052")
            filtered_results = loads[loads[load_id_col].astype(str).str.contains(query_string, case=False)] if query_string else loads
        else:
            driver_list = ["Select Driver"] + sorted_unique_safe(loads[get_col("CARGAS", "driver_id")])
            selected_driver = st.selectbox("Select Driver:", driver_list)
            filtered_results = loads[loads[get_col("CARGAS", "driver_id")].astype(str) == selected_driver] if selected_driver != "Select Driver" else loads
    
    st.markdown("---")
    st.markdown(f"**Records Found:** `{len(filtered_results)}` entries")
    
    if len(filtered_results) > 0:
        st.dataframe(filtered_results, use_container_width=True)
    else:
        st.warning("⚠️ No results found.")

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
        
        # Merge con drivers si aplica
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
        
        # Tabla
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
        delivery_col = get_col("CARGAS", "delivery_date")
        loads_alerts = loads.copy()
        loads_alerts["DELIVERY_DATE_DT"] = pd.to_datetime(loads_alerts[delivery_col], errors='coerce').dt.date
        
        criticas = []
        atencion = []
        entregadas = []
        en_tiempo = []
        
        for _, row in loads_alerts.iterrows():
            status = str(row[status_col]).strip().upper()
            fecha_entrega = row["DELIVERY_DATE_DT"]
            
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
            st.markdown("<h5 style='color: #0F172A; font-weight: 600; margin-bottom: 15px;'>Critical Loads</h5>", unsafe_allow_html=True)
            for item, motivo in criticas:
                st.markdown(f"""
                <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-left: 5px solid #DC2626; border-radius: 8px; padding: 16px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 600; color: #0F172A;">Load: {item[load_id_col]} | {item[company_col]}</span>
                        <span style="font-size: 12px; color: #DC2626; background-color: #FEF2F2; padding: 4px 8px; border-radius: 4px;">{motivo}</span>
                    </div>
                    <div style="font-size: 13px; color: #475569; margin-top: 10px; border-top: 1px solid #F1F5F9; padding-top: 10px; display: flex; gap: 15px;">
                        <div><span style="color: #94A3B8; font-weight: 500;">Driver:</span> <span style="font-weight: 500;">{item[driver_col]}</span></div>
                        <div><span style="color: #94A3B8; font-weight: 500;">Route:</span> <span style="font-weight: 500;">{item[get_col("CARGAS", "origin")]} → {item[get_col("CARGAS", "destination")]}</span></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            st.write("")
        
        # Attention
        if atencion:
            st.markdown("<h5 style='color: #0F172A; font-weight: 600; margin-bottom: 15px;'>Urgent Loads</h5>", unsafe_allow_html=True)
            for item, motivo in atencion:
                st.markdown(f"""
                <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-left: 5px solid #D97706; border-radius: 8px; padding: 16px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 600; color: #0F172A;">Load: {item[load_id_col]} | {item[company_col]}</span>
                        <span style="font-size: 12px; color: #B45309; background-color: #FEF3C7; padding: 4px 8px; border-radius: 4px;">{motivo}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            st.write("")
        
        # Pending settlement
        if entregadas:
            st.markdown("<h5 style='color: #0F172A; font-weight: 600; margin-bottom: 15px;'>Pending Settlement</h5>", unsafe_allow_html=True)
            for item, motivo in entregadas:
                st.markdown(f"""
                <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-left: 5px solid #2563EB; border-radius: 8px; padding: 16px; margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 600; color: #0F172A;">Load: {item[load_id_col]} | {item[company_col]}</span>
                        <span style="font-size: 12px; color: #1E40AF; background-color: #EFF6FF; padding: 4px 8px; border-radius: 4px;">{motivo}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            st.write("")
        
        if not criticas and not atencion and not entregadas:
            st.success("✅ No delays or pending settlements detected.")
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
                        ws_fin = get_ws("EXPENSE_FINANCIAMIENTOS")
                        new_row = [f"FIN-{int(datetime.now().timestamp())}", f_driver, f_truck, f_concept, total_pay, 0] + fridays
                        ws_fin.append_row(new_row)
                        st.success("✅ Financing agreement created!")
                        st.cache_data.clear()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
    
    with col_fin2:
        st.markdown("<h5 style='color:#1E293B; margin-bottom:15px;'>Record Payment</h5>", unsafe_allow_html=True)
        
        if not expense_fin.empty:
            fin_paid_col = get_col("EXPENSE_FINANCIAMIENTOS", "installments_paid")
            fin_total_col = get_col("EXPENSE_FINANCIAMIENTOS", "total_to_pay")
            active = expense_fin[expense_fin[fin_paid_col].astype(float) < expense_fin[fin_total_col].astype(float)]
            
            if not active.empty:
                with st.form("form_fin_payment", clear_on_submit=True):
                    fin_driver_col = get_col("EXPENSE_FINANCIAMIENTOS", "driver")
                    fin_id_col = get_col("EXPENSE_FINANCIAMIENTOS", "id_fin")
                    fin_concept_col = get_col("EXPENSE_FINANCIAMIENTOS", "concept")
                    
                    opts = active.apply(lambda r: f"{r[fin_driver_col]} ({r[fin_concept_col]}) | {r[fin_id_col]}", axis=1).tolist()
                    sel = st.selectbox("Agreement", opts)
                    sel_id = sel.split(" | ")[1]
                    
                    amount = st.number_input("Payment (USD)", min_value=0.0, step=50.0)
                    if st.form_submit_button("Apply"):
                        if amount <= 0:
                            st.error("❌ Amount > 0 required.")
                        else:
                            try:
                                ws_fin = get_ws("EXPENSE_FINANCIAMIENTOS")
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
        for _, row in expense_fin.iterrows():
            total_val = safe_float(row[fin_total_col])
            paid = safe_float(row[fin_paid_col])
            debt = max(0, total_val - paid)
            pct = min(100, (paid / total_val * 100)) if total_val > 0 else 0
            
            fin_driver_col = get_col("EXPENSE_FINANCIAMIENTOS", "driver")
            fin_truck_col = get_col("EXPENSE_FINANCIAMIENTOS", "truck_id")
            fin_concept_col = get_col("EXPENSE_FINANCIAMIENTOS", "concept")
            fin_id_col = get_col("EXPENSE_FINANCIAMIENTOS", "id_fin")
            
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
        for _, row in truck_pay.iterrows():
            truck_total_col = get_col("TRUCK_PAYMENTS", "total_value")
            truck_paid_col = get_col("TRUCK_PAYMENTS", "total_paid")
            truck_amort_col = get_col("TRUCK_PAYMENTS", "weekly_amortization")
            truck_driver_col = get_col("TRUCK_PAYMENTS", "driver")
            truck_id_col = get_col("TRUCK_PAYMENTS", "truck_id")
            truck_date_col = get_col("TRUCK_PAYMENTS", "start_date")
            
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
# TAB 10: DISPATCH TRACKER
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
                        ws_disp.append_row([p_date.strftime('%Y-%m-%d'), p_name, p_concept, valor])
                        st.success("✅ Movement recorded!")
                        st.cache_data.clear()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
    
    with col_p2:
        if not dispatch_track.empty:
            disp_date_col = get_col("DISPATCH_TRACKER", "date")
            disp_person_col = get_col("DISPATCH_TRACKER", "person")
            disp_concept_col = get_col("DISPATCH_TRACKER", "concept")
            disp_amount_col = get_col("DISPATCH_TRACKER", "amount")
            
            df_acc = dispatch_track[[disp_date_col, disp_person_col, disp_concept_col, disp_amount_col]].copy()
            df_acc[disp_amount_col] = safe_to_numeric(df_acc[disp_amount_col], errors='coerce').fillna(0)
            
            sel_person = st.selectbox("Select Person", df_acc[disp_person_col].unique())
            df_sel = df_acc[df_acc[disp_person_col] == sel_person].sort_values(disp_date_col)
            df_sel["BALANCE"] = df_sel[disp_amount_col].cumsum()
            
            saldo = safe_float(df_sel["BALANCE"].iloc[-1]) if len(df_sel) > 0 else 0
            color = "#10B981" if saldo >= 0 else "#EF4444"
            
            st.markdown(f"""
            <div style="background-color: #F8FAFC; padding: 15px; border-radius: 10px; border-left: 5px solid {color}; border: 1px solid #E2E8F0;">
                <h5 style="margin:0; color:#64748B;">Balance: {sel_person}</h5>
                <p style="margin:5px 0 0 0; font-size: 28px; font-weight: bold; color:{color};">{money(saldo)}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("")
            fig = px.line(df_sel, x=disp_date_col, y="BALANCE", markers=True, title=f"Account History: {sel_person}")
            fig.add_hline(y=0, line_dash="dash", line_color="gray")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("ℹ️ No records.")
    
    st.divider()
    st.markdown("### Historical Ledger")
    
    if not dispatch_track.empty:
        st.dataframe(dispatch_track.sort_values(disp_date_col, ascending=False), use_container_width=True)
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
                use_container_width=True,
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
                                # Update STATUS to PAID
                                status_col_idx = 8  # STATUS is typically column 8
                                ws_ap.update_cell(cell.row, status_col_idx, "PAID")
                                
                                # Update PAYMENT_DATE
                                payment_col_idx = 9  # PAYMENT_DATE is typically column 9
                                ws_ap.update_cell(cell.row, payment_col_idx, str(payment_date_ap))
                                
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
                
                st.dataframe(aged_summary, use_container_width=True)
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
                use_container_width=True,
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
                                # Update STATUS to PAID
                                status_col_idx = 8  # STATUS is typically column 8
                                ws_ar.update_cell(cell.row, status_col_idx, "PAID")
                                
                                # Update PAYMENT_DATE
                                payment_col_idx = 9  # PAYMENT_DATE is typically column 9
                                ws_ar.update_cell(cell.row, payment_col_idx, str(payment_date_ar))
                                
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
                
                st.dataframe(aged_summary, use_container_width=True)
            else:
                st.info("ℹ️ No overdue receivables.")
        else:
            st.info("ℹ️ No data.")

st.divider()
st.caption("MJ7 Logistics Control Center v5.0 | Powered by Streamlit + Google Sheets")

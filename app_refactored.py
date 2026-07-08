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
    try:
        sh = client.open(SHEET_NAME)
        
        # Cargar hojas principales
        try:
            loads = pd.DataFrame(sh.worksheet("CARGAS").get_all_records())
        except Exception as e:
            st.warning(f"⚠️ Error loading CARGAS: {e}")
            loads = pd.DataFrame()
        
        try:
            settlements = pd.DataFrame(sh.worksheet("SETTLEMENTS").get_all_records())
        except Exception as e:
            st.warning(f"⚠️ Error loading SETTLEMENTS: {e}")
            settlements = pd.DataFrame()
        
        try:
            deductions = pd.DataFrame(sh.worksheet("DEDUCTIONS").get_all_records())
        except Exception as e:
            st.warning(f"⚠️ Error loading DEDUCTIONS: {e}")
            deductions = pd.DataFrame()
        
        try:
            drivers = pd.DataFrame(sh.worksheet("DRIVERS").get_all_records())
        except Exception as e:
            st.warning(f"⚠️ Error loading DRIVERS: {e}")
            drivers = pd.DataFrame()
        
        # Cargar hojas opcionales con fallback
        try:
            expense_fin = pd.DataFrame(sh.worksheet("EXPENSE_FINANCING").get_all_records())
        except Exception:
            expense_fin = pd.DataFrame(columns=[get_col("EXPENSE_FINANCING", k) 
                                                for k in COLUMN_MAPS["EXPENSE_FINANCING"].keys()])
        
        try:
            truck_pay = pd.DataFrame(sh.worksheet("TRUCK_PAYMENTS").get_all_records())
        except Exception:
            truck_pay = pd.DataFrame(columns=[get_col("TRUCK_PAYMENTS", k) 
                                              for k in COLUMN_MAPS["TRUCK_PAYMENTS"].keys()])
        
        try:
            dispatch_track = pd.DataFrame(sh.worksheet("DISPATCH_TRACKER").get_all_records())
        except Exception:
            dispatch_track = pd.DataFrame(columns=[get_col("DISPATCH_TRACKER", k) 
                                                   for k in COLUMN_MAPS["DISPATCH_TRACKER"].keys()])
        
        # Convertir fechas - solo si existen las columnas
        for df in [loads, settlements, deductions]:
            if not df.empty:
                date_cols = [get_col("CARGAS", "start_date"), get_col("CARGAS", "delivery_date"), 
                            get_col("SETTLEMENTS", "date"), get_col("DEDUCTIONS", "date")]
                for col in date_cols:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Validar estructuras críticas
        for sheet_name, df in [
            ("CARGAS", loads),
            ("SETTLEMENTS", settlements),
            ("DEDUCTIONS", deductions),
        ]:
            if not df.empty:
                is_valid, errors = validate_dataframe(df, sheet_name)
                if not is_valid:
                    st.warning(f"⚠️ {sheet_name}: {'; '.join(errors)}")
        
        return loads, settlements, deductions, drivers, expense_fin, truck_pay, dispatch_track
    
    except Exception as e:
        st.error(f"❌ Critical error in load_data: {str(e)}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

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
    try:
        date_col = get_col("SETTLEMENTS", "date")
        mj7_net_col = get_col("SETTLEMENTS", "mj7_net")
        
        settlements[date_col] = pd.to_datetime(settlements[date_col])
        
        net_today = settlements[settlements[date_col].dt.date == today.date()][mj7_net_col].sum()
        net_week = settlements[settlements[date_col] >= (today - timedelta(days=7))][mj7_net_col].sum()
        net_month = settlements[settlements[date_col].dt.month == today.month][mj7_net_col].sum()
        net_year = settlements[settlements[date_col].dt.year == today.year][mj7_net_col].sum()
    except Exception as e:
        st.warning(f"⚠️ Error calculating profits: {e}")
        net_today = net_week = net_month = net_year = 0.00
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
    try:
        if not loads.empty:
            st.dataframe(loads, width='stretch')
        else:
            st.info("ℹ️ No data available in CARGAS sheet.")
    except Exception as e:
        st.error(f"❌ Error loading CARGAS: {str(e)}")

# ====================================
# TAB 1: SETTLEMENTS
# ====================================

with tabs[1]:
    st.subheader("Closed Settlements History")
    try:
        if not settlements.empty:
            st.dataframe(settlements, width='stretch')
        else:
            st.info("ℹ️ No data available in SETTLEMENTS sheet.")
    except Exception as e:
        st.error(f"❌ Error loading SETTLEMENTS: {str(e)}")

# ====================================
# TAB 2: PERFORMANCE & CARD GENERATOR
# ====================================

with tabs[2]:
    st.subheader("Driver Performance Overview")
    try:
        if not drivers.empty:
            st.dataframe(drivers, width='stretch')
        else:
            st.info("ℹ️ No drivers available.")
        
        if not settlements.empty:
            st.markdown("---")
            st.subheader("Production Metrics Matrix")
            
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
                
                if not settlements_filtered.empty and driver_col in settlements_filtered.columns and load_col in settlements_filtered.columns:
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
                        width='stretch'
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
                    st.info("ℹ️ No data available for this selection.")
            else:
                st.warning("No data found for the selected date.")
    except Exception as e:
        st.error(f"❌ Error in Performance tab: {str(e)}")

# ====================================
# TAB 3: DEDUCTIONS
# ====================================

with tabs[3]:
    st.subheader("Expenses & Deductions Log")
    try:
        if not deductions.empty:
            display_deductions = deductions.copy()
            
            qty_col = get_col("DEDUCTIONS", "qty_gallons")
            if qty_col in display_deductions.columns:
                display_deductions[qty_col] = safe_to_numeric(display_deductions[qty_col], errors='coerce')
                display_deductions[qty_col] = display_deductions[qty_col].apply(format_gallons)
            
            st.dataframe(display_deductions, width='stretch')
        else:
            st.info("ℹ️ No deductions available.")
    except Exception as e:
        st.error(f"❌ Error loading DEDUCTIONS: {str(e)}")

# ====================================
# ACCOUNTS PAYABLE TAB
# ====================================

with ap_tab:
    try:
        st.markdown(render_ap_ar_header(ap_ar_company, is_payable=True), unsafe_allow_html=True)
        
        # Calculate metrics
        if not ap_df.empty:
            try:
                ap_df_clean = ap_df.copy()
                ap_df_clean['AMOUNT'] = pd.to_numeric(ap_df_clean['AMOUNT'], errors='coerce').fillna(0)
                ap_df_clean['DUE_DATE'] = pd.to_datetime(ap_df_clean['DUE_DATE'], errors='coerce')
                ap_metrics = calculate_ap_ar_metrics(ap_df_clean, today)
            except Exception as e:
                st.warning(f"⚠️ Error calculating AP metrics: {e}")
                ap_metrics = calculate_ap_ar_metrics(pd.DataFrame(), today)
        else:
            ap_metrics = calculate_ap_ar_metrics(pd.DataFrame(), today)
        
        # Display metrics
        try:
            st.markdown(render_metrics_grid(ap_metrics), unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"⚠️ Error displaying metrics: {e}")
        
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
            try:
                # Create display dataframe
                ap_display = ap_df.copy()
                
                # Format columns
                if 'AMOUNT' in ap_display.columns:
                    ap_display['AMOUNT'] = ap_display['AMOUNT'].apply(lambda x: money(safe_float(x)))
                
                # Select columns to display
                display_cols = ['ID', 'DATE', 'SUPPLIER', 'INVOICE_NUMBER', 'DESCRIPTION', 'AMOUNT', 'DUE_DATE', 'STATUS', 'PAYMENT_DATE', 'NOTES']
                available_cols = [col for col in display_cols if col in ap_display.columns]
                
                if available_cols:
                    st.dataframe(
                        ap_display[available_cols],
                        width='stretch',
                        hide_index=True
                    )
                else:
                    st.warning("⚠️ Expected columns not found in AP data.")
            except Exception as e:
                st.error(f"❌ Error displaying AP data: {str(e)}")
            
            # Mark as paid section
            st.markdown("---")
            st.markdown("### ✅ Record Payment")
            
            try:
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
                        
                        if ap_options:
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
                            st.info("ℹ️ No pending invoices.")
                    else:
                        st.info("ℹ️ All invoices are paid.")
            except Exception as e:
                st.error(f"❌ Error in payment recording: {str(e)}")
        else:
            st.info("ℹ️ No supplier invoices registered yet.")
        
        # Aged Report
        st.markdown("---")
        st.markdown("### 📈 Aged Payables Report")
        
        try:
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
        except Exception as e:
            st.error(f"❌ Error generating aged report: {str(e)}")
    
    except Exception as e:
        st.error(f"❌ Error in Accounts Payable tab: {str(e)}")

# ====================================
# ACCOUNTS RECEIVABLE TAB
# ====================================

with ar_tab:
    try:
        st.markdown(render_ap_ar_header(ap_ar_company, is_payable=False), unsafe_allow_html=True)
        
        # Calculate metrics
        if not ar_df.empty:
            try:
                ar_df_clean = ar_df.copy()
                ar_df_clean['AMOUNT'] = pd.to_numeric(ar_df_clean['AMOUNT'], errors='coerce').fillna(0)
                ar_df_clean['DUE_DATE'] = pd.to_datetime(ar_df_clean['DUE_DATE'], errors='coerce')
                ar_metrics = calculate_ap_ar_metrics(ar_df_clean, today)
            except Exception as e:
                st.warning(f"⚠️ Error calculating AR metrics: {e}")
                ar_metrics = calculate_ap_ar_metrics(pd.DataFrame(), today)
        else:
            ar_metrics = calculate_ap_ar_metrics(pd.DataFrame(), today)
        
        # Display metrics
        try:
            st.markdown(render_metrics_grid(ar_metrics), unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"⚠️ Error displaying metrics: {e}")
        
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
            try:
                # Create display dataframe
                ar_display = ar_df.copy()
                
                # Format columns
                if 'AMOUNT' in ar_display.columns:
                    ar_display['AMOUNT'] = ar_display['AMOUNT'].apply(lambda x: money(safe_float(x)))
                
                # Select columns to display
                display_cols = ['ID', 'DATE', 'CLIENT', 'INVOICE_NUMBER', 'DESCRIPTION', 'AMOUNT', 'DUE_DATE', 'STATUS', 'PAYMENT_DATE', 'NOTES']
                available_cols = [col for col in display_cols if col in ar_display.columns]
                
                if available_cols:
                    st.dataframe(
                        ar_display[available_cols],
                        width='stretch',
                        hide_index=True
                    )
                else:
                    st.warning("⚠️ Expected columns not found in AR data.")
            except Exception as e:
                st.error(f"❌ Error displaying AR data: {str(e)}")
            
            # Mark as paid section
            st.markdown("---")
            st.markdown("### ✅ Record Payment")
            
            try:
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
                        
                        if ar_options:
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
                            st.info("ℹ️ No pending invoices.")
                    else:
                        st.info("ℹ️ All invoices are paid.")
            except Exception as e:
                st.error(f"❌ Error in payment recording: {str(e)}")
        else:
            st.info("ℹ️ No client invoices registered yet.")
        
        # Aged Report
        st.markdown("---")
        st.markdown("### 📈 Aged Receivables Report")
        
        try:
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
        except Exception as e:
            st.error(f"❌ Error generating aged report: {str(e)}")
    
    except Exception as e:
        st.error(f"❌ Error in Accounts Receivable tab: {str(e)}")

# ====================================
# FOOTER
# ====================================

st.divider()
st.caption("🚛 MJ7 Logistics Control Center v5.0 | Powered by Streamlit + Google Sheets | Last Updated: 2024")

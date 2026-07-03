#PARTE 1 DE 4 
import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import plotly.express as px
from PIL import Image, ImageDraw, ImageFont
import io
import os

# ReportLab components
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus import Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ==================================================
# CONFIGURACIÓN NUBE
# ==================================================
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

# Cargar desde los Secrets de Streamlit
creds_dict = dict(st.secrets["gcp_service_account"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

client = gspread.authorize(creds)

# Definición del nombre del archivo en Google Sheets
SHEET_NAME = "MJ7_Database"

# State memory management
if "form_load" not in st.session_state: st.session_state.form_load = ""
if "form_company" not in st.session_state: st.session_state.form_company = ""
if "form_amount" not in st.session_state: st.session_state.form_amount = None
if "form_origin" not in st.session_state: st.session_state.form_origin = ""
if "form_destination" not in st.session_state: st.session_state.form_destination = ""

@st.cache_data(ttl=600)
def load_data():
    sh = client.open(SHEET_NAME)
    loads = pd.DataFrame(sh.worksheet("CARGAS").get_all_records())
    settlements = pd.DataFrame(sh.worksheet("SETTLEMENTS").get_all_records())
    deductions = pd.DataFrame(sh.worksheet("DEDUCTIONS").get_all_records())
    drivers = pd.DataFrame(sh.worksheet("DRIVERS").get_all_records())
    
    for df in [loads, settlements, deductions]:
        if "DATE" in df.columns: df["DATE"] = pd.to_datetime(df["DATE"], errors='coerce')
        if "START_DATE" in df.columns: df["START_DATE"] = pd.to_datetime(df["START_DATE"], errors='coerce')
        if "DELIVERY_DATE" in df.columns: df["DELIVERY_DATE"] = pd.to_datetime(df["DELIVERY_DATE"], errors='coerce')
    return loads, settlements, deductions, drivers
# Cargamos datos una sola vez
loads, settlements, deductions, drivers = load_data()

# ==================================================
# CLEAN VISUAL STYLES
# ==================================================
st.markdown(
"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght=400;500;600;700&display=swap');
    html, body, [data-testid="stSidebar"] { font-family: 'Inter', sans-serif; background-color: #F8FAFC; }
    [data-testid="stSidebar"] { background-color: #0F172A !important; color: #F8FAFC !important; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] span, [data-testid="stSidebar"] p { color: #E2E8F0 !important; }
    
    h1 { color: #0047AB; font-weight: 700; letter-spacing: -0.75px; }
    h2, h3 { color: #1E293B; font-weight: 600; letter-spacing: -0.5px; }
    
    [data-testid="metric-container"] { background: #FFFFFF; padding: 20px; border-radius: 8px; border: 1px solid #E2E8F0; }
    [data-testid="stMetricLabel"] { color: #64748B !important; font-weight: 600 !important; font-size: 0.75rem !important; text-transform: uppercase; }
    [data-testid="stMetricValue"] { color: #0F172A !important; font-weight: 700 !important; font-size: 1.5rem !important; }
    
    .stButton button { background: #1E293B !important; color: #FFFFFF !important; border-radius: 6px !important; padding: 10px 20px !important; font-weight: 600 !important; border: none !important; width: 100%; }
    .stButton button:hover { background: #0F172A !important; }
    
    /* Nueva estructura limpia de tarjeta de rendimiento */
    .performance-card-container {
        background-color: #1E293B !important; 
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
        padding: 0px !important;
        margin-bottom: 25px !important;
        overflow: hidden !important;
    }
    .performance-card-header {
        background-color: #0F172A !important;
        border-bottom: 2px solid #38BDF8 !important;
        padding: 15px 20px !important;
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
    }
    .performance-card-header-text h4 {
        color: #38BDF8 !important;
        margin: 0 !important;
        font-size: 1.15rem !important;
        font-family: 'Inter', sans-serif !important;
        letter-spacing: 0.5px !important;
    }
    .performance-card-header-text span {
        color: #94A3B8 !important;
        font-size: 0.8rem !important;
    }
    .performance-card-body {
        padding: 20px !important;
    }
    .driver-meta-info {
        font-size: 1rem !important;
        color: #F8FAFC !important;
        margin-bottom: 15px !important;
    }
    .performance-grid-layout {
        display: grid !important;
        grid-template-columns: repeat(3, 1fr) !important;
        gap: 15px !important;
    }
    .perf-item-box {
        background: #0F172A !important;
        padding: 15px !important;
        border-radius: 8px !important;
        border: 1px solid #334155 !important;
        text-align: center !important;
    }
    .perf-item-box.highlighted {
        border: 1px solid #38BDF8 !important;
    }
    .perf-item-label {
        font-size: 0.75rem !important;
        color: #94A3B8 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    .performance-card-body .perf-item-value {
        font-size: 1.3rem !important;
        font-weight: 700 !important;
        color: #F8FAFC !important;
        margin-top: 5px !important;
    }
</style>
""",
unsafe_allow_html=True
)

today = pd.Timestamp.today().normalize()

st.sidebar.title("MJ7 OPERATIONS")
st.sidebar.caption("Control Panel v4.5")

# Header with Logo Alignment
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

#PARTE 2 DE 4 
# MJ7 PROFITS METRICS
# ==================================================
if not settlements.empty:
    settlements['DATE'] = pd.to_datetime(settlements['DATE'])
    net_today = settlements[settlements['DATE'].dt.date == today.date()]['MJ7_NET'].sum()
    net_week = settlements[settlements['DATE'] >= (today - timedelta(days=7))]['MJ7_NET'].sum()
    net_month = settlements[settlements['DATE'].dt.month == today.month]['MJ7_NET'].sum()
    net_year = settlements[settlements['DATE'].dt.year == today.year]['MJ7_NET'].sum()
else:
    net_today = net_week = net_month = net_year = 0.00

st.markdown("### MJ7 Profits")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Today", f"${net_today:,.2f}")
k2.metric("This Week", f"${net_week:,.2f}")
k3.metric("This Month", f"${net_month:,.2f}")
k4.metric("This Year", f"${net_year:,.2f}")
st.divider()

# Aesthetic Gray Tabs via Streamlit Material Icons Syntax
tabs = st.tabs([
    ":material/insert_chart: Loads", 
    ":material/payments: Settlements", 
    ":material/trending_up: Performance", 
    ":material/money_off: Deductions", 
    ":material/edit_note: Data Entry", 
    ":material/search: Search Engine", 
    ":material/picture_as_pdf: PDF Reports",
    ":material/gavel: Status Verification"
])

# TAB 1: LOADS
with tabs[0]:
    st.subheader("General Loads Registry")
    st.dataframe(loads, use_container_width=True)

# TAB 2: SETTLEMENTS
with tabs[1]:
    st.subheader("Closed Settlements History")
    st.dataframe(settlements, use_container_width=True)

# ==================================================
# TAB 3: PERFORMANCE & CARD GENERATOR
# ==================================================
with tabs[2]:
    st.subheader("Driver Performance Overview")
    st.dataframe(drivers, width="stretch")
    
    if not settlements.empty:
        st.markdown("---")
        st.subheader("Production Metrics Matrix")
        
        # Identificar la columna de fechas y asegurar el tipo datetime
        date_col = "DATE" if "DATE" in settlements.columns else settlements.columns[0] 
        settlements[date_col] = pd.to_datetime(settlements[date_col])
        
        # Filtro de vistas en columnas limpias
        col_date1, col_date2 = st.columns([1, 2])
        with col_date1:
            filter_type = st.radio("Filter views:", ["All Time", "Specific Day"], horizontal=True)
        
        settlements_filtered = settlements.copy()
        
        if filter_type == "Specific Day":
            with col_date2:
                selected_date = st.date_input("Select target date:", value=settlements[date_col].max().date())
            settlements_filtered = settlements_filtered[settlements_filtered[date_col].dt.date == selected_date]
        
        if not settlements_filtered.empty:
            # Detalle por carga: Agrupamos por Chofer y por Carga (LOAD_ID)
            load_col = "LOAD_ID" if "LOAD_ID" in settlements_filtered.columns else (settlements_filtered.columns[1] if len(settlements_filtered.columns) > 1 else settlements_filtered.columns[0])
            
            performance_matrix = settlements_filtered.groupby(["DRIVER_ID", load_col]).agg({"GROSS": "sum", "OWNER_PAY": "sum", "MJ7_NET": "sum"}).reset_index()
            
            st.dataframe(
                performance_matrix.style.format({"GROSS": "${:,.2f}", "OWNER_PAY": "${:,.2f}", "MJ7_NET": "${:,.2f}"}), 
                width="stretch"
            )
            
            st.markdown("---")
            st.subheader("Generate Performance Cards")
            target_perf_drivers = st.multiselect("Select drivers to generate cards:", performance_matrix["DRIVER_ID"].unique())
            
            if target_perf_drivers:
                import base64
                
                try:
                    with open("logo.jpeg", "rb") as image_file:
                        encoded_logo = base64.b64encode(image_file.read()).decode()
                    logo_html_tag = f'<img src="data:image/jpeg;base64,{encoded_logo}" style="height: 36px; border-radius: 4px; border: 1px solid #E2E8F0;">'
                except Exception:
                    logo_html_tag = ''

                # --- FUNCIÓN GENERADORA PDF CON REPORTLAB ---
                def generate_reportlab_pdf(title_suffix, driver_id, name_str, date_str, gross, owner_pay, mj7_net):
                    pdf_buffer = io.BytesIO()
                    
                    # Dimensiones de tarjeta (600 pt x 260 pt)
                    doc = SimpleDocTemplate(
                        pdf_buffer, 
                        pagesize=(600, 260),
                        rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20
                    )
                    
                    styles = getSampleStyleSheet()
                    
                    title_style = ParagraphStyle(
                        'CardTitle', fontName='Helvetica-Bold', fontSize=14, leading=16, textColor=colors.HexColor("#1E293B")
                    )
                    info_style = ParagraphStyle(
                        'DriverInfo', fontName='Helvetica-Bold', fontSize=11, leading=14, textColor=colors.HexColor("#334155")
                    )
                    label_style = ParagraphStyle(
                        'MetricLabel', fontName='Helvetica-Bold', fontSize=9, leading=11, textColor=colors.HexColor("#64748B")
                    )
                    value_style = ParagraphStyle(
                        'MetricValue', fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=colors.HexColor("#1E293B")
                    )
                    net_label_style = ParagraphStyle(
                        'NetLabel', fontName='Helvetica-Bold', fontSize=9, leading=11, textColor=colors.HexColor("#1E40AF")
                    )
                    net_value_style = ParagraphStyle(
                        'NetValue', fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=colors.HexColor("#1D4ED8")
                    )
                    
                    story = []
                    
                    # Header: Título y Logo
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
                        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                        ('ALIGN', (1,0), (1,0), 'RIGHT'),
                        ('LINEBELOW', (0,0), (-1,-1), 1, colors.HexColor("#E2E8F0")),
                        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
                    ]))
                    story.append(header_table)
                    story.append(Spacer(1, 12))
                    
                    # Bloque de Información del Conductor
                    info_p = Paragraph(f"DRIVER ID: {driver_id} &nbsp;&nbsp;|&nbsp;&nbsp; NAME: {name_str}", info_style)
                    info_table = Table([[info_p]], colWidths=[560])
                    info_table.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
                        ('PADDING', (0,0), (-1,-1), 8),
                        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
                    ]))
                    story.append(info_table)
                    story.append(Spacer(1, 15))
                    
                    # Cajas de Métricas Financieras
                    box_gross = [Paragraph("TOTAL GROSS", label_style), Spacer(1, 8), Paragraph(f"${gross:,.2f}", value_style)]
                    box_owner = [Paragraph("OWNER PAY", label_style), Spacer(1, 8), Paragraph(f"${owner_pay:,.2f}", value_style)]
                    box_net = [Paragraph("MJ7 NET PROFIT", net_label_style), Spacer(1, 8), Paragraph(f"${mj7_net:,.2f}", net_value_style)]
                    
                    metrics_table = Table([[box_gross, box_owner, box_net]], colWidths=[180, 180, 200])
                    metrics_table.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (0,0), colors.HexColor("#F8FAFC")),
                        ('BACKGROUND', (1,0), (1,0), colors.HexColor("#F8FAFC")),
                        ('BACKGROUND', (2,0), (2,0), colors.HexColor("#EFF6FF")),
                        ('BOX', (0,0), (0,0), 1, colors.HexColor("#E2E8F0")),
                        ('BOX', (1,0), (1,0), 1, colors.HexColor("#E2E8F0")),
                        ('BOX', (2,0), (2,0), 1, colors.HexColor("#BFDBFE")),
                        ('PADDING', (0,0), (-1,-1), 12),
                        ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ]))
                    story.append(metrics_table)
                    
                    doc.build(story)
                    return pdf_buffer.getvalue()

                # Renderizado por cada conductor seleccionado
                for d_id in target_perf_drivers:
                    driver_loads = performance_matrix[performance_matrix["DRIVER_ID"] == d_id]
                    
                    try:
                        d_name = drivers[drivers["DRIVER_ID"].astype(str) == str(d_id)]["FULL_NAME"].iloc[0]
                    except Exception:
                        d_name = "Unknown Driver Name"
                    
                    st.write(f"### Performance Report: {d_name} ({d_id})")
                    
                    # 1. TARJETAS POR CARGA INDIVIDUAL
                    for _, load_row in driver_loads.iterrows():
                        current_load_id = load_row[load_col]
                        card_date_str = selected_date.strftime('%Y-%m-%d') if filter_type == "Specific Day" else datetime.now().strftime('%Y-%m-%d')
                        
                        card_html = f"""
                        <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 24px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); margin-bottom: 8px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #F1F5F9; padding-bottom: 16px; margin-bottom: 16px;">
                                <div>
                                    <h4 style="margin: 0; color: #1E293B; font-size: 14px; letter-spacing: 0.5px; font-weight: 700;">MJ7 LOGISTICS — LOAD CARD</h4>
                                    <span style="font-size: 12px; color: #64748B;">Load Reference: <b>{current_load_id}</b> | Date: {card_date_str}</span>
                                </div>
                                {logo_html_tag}
                            </div>
                            <div style="background-color: #F8FAFC; border-radius: 6px; padding: 10px 14px; font-size: 13px; color: #334155; margin-bottom: 20px;">
                                <span style="color: #64748B; font-weight: 600;">DRIVER ID:</span> <span style="font-weight: 700; color: #0F172A;">{d_id}</span> | 
                                <span style="color: #64748B; font-weight: 600;">NAME:</span> <span style="font-weight: 700; color: #0F172A;">{d_name}</span>
                            </div>
                            <table style="width: 100%; border-collapse: separate; border-spacing: 16px 0; margin-left: -16px; margin-right: -16px;">
                                <tr>
                                    <td style="width: 33.33%; background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 14px;">
                                        <div style="font-size: 11px; text-transform: uppercase; color: #64748B; font-weight: 600;">Load Gross</div>
                                        <div style="font-size: 20px; color: #1E293B; font-weight: 700;">${load_row['GROSS']:,.2f}</div>
                                    </td>
                                    <td style="width: 33.33%; background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 14px;">
                                        <div style="font-size: 11px; text-transform: uppercase; color: #64748B; font-weight: 600;">Owner Pay</div>
                                        <div style="font-size: 20px; color: #1E293B; font-weight: 700;">${load_row['OWNER_PAY']:,.2f}</div>
                                    </td>
                                    <td style="width: 33.33%; background-color: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 8px; padding: 14px;">
                                        <div style="font-size: 11px; text-transform: uppercase; color: #1E40AF; font-weight: 600;">MJ7 Net Profit</div>
                                        <div style="font-size: 20px; color: #1D4ED8; font-weight: 700;">${load_row['MJ7_NET']:,.2f}</div>
                                    </td>
                                </tr>
                            </table>
                        </div>
                        """
                        st.html(card_html.strip().replace("\n", ""))
                        
                        pdf_data = generate_reportlab_pdf(
                            f"LOAD {current_load_id}", d_id, d_name, card_date_str, 
                            load_row['GROSS'], load_row['OWNER_PAY'], load_row['MJ7_NET']
                        )
                        st.download_button(
                            label=f"Export Load Card {current_load_id} (PDF)",
                            data=pdf_data,
                            file_name=f"MJ7_Load_{current_load_id}_{d_id}.pdf",
                            mime="application/pdf",
                            key=f"btn_pdf_{d_id}_{current_load_id}"
                        )
                    
                    # 2. TARJETA GLOBAL (RESUMEN DIARIO O ACUMULADO)
                    if len(driver_loads) > 1:
                        total_gross = driver_loads['GROSS'].sum()
                        total_owner = driver_loads['OWNER_PAY'].sum()
                        total_net = driver_loads['MJ7_NET'].sum()
                        
                        title_summary = "DAILY TOTALS" if filter_type == "Specific Day" else "ACCUMULATED TOTALS"
                        subtitle_summary = f"Summary of {len(driver_loads)} loads for {card_date_str}" if filter_type == "Specific Day" else f"Summary of {len(driver_loads)} loads | Generated today"
                        
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
                                    <td style="width: 33.33%; background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 8px; padding: 14px;">
                                        <div style="font-size: 11px; text-transform: uppercase; color: #475569; font-weight: 700;">Gross Total</div>
                                        <div style="font-size: 22px; color: #0F172A; font-weight: 800;">${total_gross:,.2f}</div>
                                    </td>
                                    <td style="width: 33.33%; background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 8px; padding: 14px;">
                                        <div style="font-size: 11px; text-transform: uppercase; color: #475569; font-weight: 700;">Total Owner Pay</div>
                                        <div style="font-size: 22px; color: #0F172A; font-weight: 800;">${total_owner:,.2f}</div>
                                    </td>
                                    <td style="width: 33.33%; background-color: #2563EB; border: 1px solid #1D4ED8; border-radius: 8px; padding: 14px;">
                                        <div style="font-size: 11px; text-transform: uppercase; color: #FFFFFF; font-weight: 700;">Total Net Profit</div>
                                        <div style="font-size: 22px; color: #FFFFFF; font-weight: 800;">${total_net:,.2f}</div>
                                    </td>
                                </tr>
                            </table>
                        </div>
                        """
                        st.html(summary_html.strip().replace("\n", ""))
                        
                        summary_pdf_data = generate_reportlab_pdf(
                            title_summary, d_id, d_name, card_date_str, 
                            total_gross, total_owner, total_net
                        )
                        st.download_button(
                            label=f"Export {title_summary.title()} Summary (PDF)",
                            data=summary_pdf_data,
                            file_name=f"MJ7_{title_summary}_{d_id}.pdf",
                            mime="application/pdf",
                            key=f"btn_pdf_total_{d_id}",
                            width="stretch"
                        )
                    
                    st.markdown("<hr style='border: 1px dashed #E2E8F0;'>", unsafe_allow_html=True)
        else:
            st.warning("No data found for the selected date.")
# TAB 4: DEDUCTIONS
with tabs[3]:
    st.subheader("Expenses & Deductions Log")
    display_deductions = deductions.copy()
    if "QTY_GALLONS" in display_deductions.columns:
        display_deductions["QTY_GALLONS"] = pd.to_numeric(display_deductions["QTY_GALLONS"]).apply(lambda x: int(x) if x == int(x) else x)
    st.dataframe(display_deductions, use_container_width=True)

# ==================================================
# TAB 5: OPERATION MODULE (ENTRY & ADJUSTMENTS)
# ==================================================
with tabs[4]:
    st.subheader("Operations Management Module")
    flow = st.radio("Select Action:", ["New Load", "Settle Load", "Modify / Re-Settle Load", "Register Deduction", "Add Driver"], horizontal=True)
    st.divider()

    # Función helper para conectar rápido a las hojas
    def get_ws(name): return client.open(SHEET_NAME).worksheet(name)

    if flow == "New Load":
        col_x, col_y = st.columns(2)
        with col_x:
            l_num = st.text_input("Load Reference ID", value=st.session_state.form_load, placeholder="MJ7-XXXX")
            l_comp = st.text_input("Broker / Client Name", value=st.session_state.form_company)
            l_amt = st.number_input("Gross Amount ($)", value=st.session_state.form_amount, format="%.2f", step=1.00)
            l_stat = st.selectbox("Status", ["PENDING", "IN TRANSIT", "DELIVERED", "CLOSED / SETTLED"])
        with col_y:
            l_orig = st.text_input("Origin", value=st.session_state.form_origin)
            l_dest = st.text_input("Destination", value=st.session_state.form_destination)
            d_options = ["Select Driver"] + list(drivers["DRIVER_ID"].astype(str).unique()) if not drivers.empty else ["No drivers available"]
            l_driver = st.selectbox("Driver", d_options)
            l_sdate = st.date_input("Start Date", today)
            l_edate = st.date_input("Delivery Date", today)
            
        if st.button("Save Load"):
            if not l_num or not l_comp or l_driver == "Select Driver" or l_amt is None:
                st.error("Error: Please complete all required fields.")
            else:
                new_row = [l_num, l_comp, float(l_amt), str(l_sdate), str(l_edate), l_stat, l_orig, l_dest, l_driver]
                get_ws("CARGAS").append_row(new_row)
                st.success("Done: Load registered successfully in the cloud.")
                st.cache_data.clear()

    elif flow == "Settle Load":
        active_codes = ["Select Load"] + list(loads[loads["STATUS"] != "CLOSED / SETTLED"]["LOAD"].astype(str).unique()) if not loads.empty else ["No logs open"]
        chosen_load = st.selectbox("Select Load to Settle:", active_codes)
        
        if chosen_load not in ["Select Load", "No logs open"]:
            match = loads[loads["LOAD"].astype(str) == chosen_load].iloc[0]
            op_assigned = match["DRIVER_ID"]
            gross_revenue = float(match["AMOUNT"])
            
            associated_costs = deductions[deductions["LOAD_NUMBER"].astype(str) == chosen_load]
            fuel_deductions = float(associated_costs[associated_costs["TYPE"] == "FUEL"]["AMOUNT"].sum())
            other_deductions = float(associated_costs[associated_costs["TYPE"] == "OTHER"]["AMOUNT"].sum())
            
            # 1. Distribución comercial estricta sobre el 100% de la carga
            m_base = gross_revenue * 0.15
            o_base = gross_revenue * 0.85
            disp_fee = gross_revenue * 0.05
            
            # ==================================================
            # INTERRUPTOR DE FACTORING CONTROLADO (Gasto del Chofer)
            # ==================================================
            aplicar_factoring = st.checkbox("Apply Factoring Fee (2.15%) to this load?", value=True)
            
            if aplicar_factoring:
                fact_fee = gross_revenue * 0.0215
            else:
                fact_fee = 0.0
                
            # Restas exactas según tu regla de negocio:
            # A MJ7 solo se le quita dispatch
            mj7_final = m_base - disp_fee
            # Al driver se le quita fuel, deducciones y factoring
            owner_final = o_base - fuel_deductions - other_deductions - fact_fee
            
            # ==================================================
            # PREVISUALIZACIÓN VISUAL ANTES DE AUTORIZAR
            # ==================================================
            st.markdown("""
            <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 6px; padding: 15px; margin: 15px 0 15px 0;">
                <h4 style="color: #1E3A8A; margin-top: 0; margin-bottom: 5px; font-weight: 600;">Financial Preview</h4>
                <p style="font-size: 13px; color: #475569; margin-bottom: 0;">Verify the calculated amounts before closing and authorizing settlement.</p>
            </div>
            """, unsafe_allow_html=True)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Gross Revenue", f"${gross_revenue:,.2f}")
            c2.metric("Dispatch Fee (MJ7)", f"${disp_fee:,.2f}", delta="-5.00%", delta_color="inverse")
            c3.metric("Factoring Fee", f"${fact_fee:,.2f}", delta="-2.15%" if aplicar_factoring else "$0.00", delta_color="inverse")
            c4.metric("Total Deductions", f"${(fuel_deductions + other_deductions):,.2f}")

            st.write("") 

            c5, c6 = st.columns(2)
            with c5:
                st.markdown(f"""
                <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 15px; border-radius: 6px; text-align: center;">
                    <span style="font-size: 12px; color: #64748B; font-weight: 600; text-transform: uppercase;">Owner Net Pay</span>
                    <h2 style="color: #0F172A; margin: 5px 0 0 0; font-weight: 700;">${owner_final:,.2f}</h2>
                </div>
                """, unsafe_allow_html=True)
            with c6:
                st.markdown(f"""
                <div style="background-color: #F0F9FF; border: 1px solid #B9E6FE; padding: 15px; border-radius: 6px; text-align: center;">
                    <span style="font-size: 12px; color: #0369A1; font-weight: 600; text-transform: uppercase;">MJ7 Net Yield</span>
                    <h2 style="color: #0369A1; margin: 5px 0 0 0; font-weight: 700;">${mj7_final:,.2f}</h2>
                </div>
                """, unsafe_allow_html=True)
                
            st.divider()

            if st.button("Authorize Settlement", use_container_width=True):
                ws_settlements = get_ws("SETTLEMENTS")
                if chosen_load in ws_settlements.col_values(2):
                    st.error("Error: This load has already been settled.")
                else:
                    from datetime import date
                    l_date = date.today() 
                    
                    new_settlement = [
                        str(l_date), 
                        str(chosen_load), 
                        str(op_assigned), 
                        float(gross_revenue), 
                        float(owner_final), 
                        float(disp_fee), 
                        float(fact_fee), 
                        float(mj7_final)
                    ]
                    ws_settlements.append_row(new_settlement)
                    
                    ws_loads = get_ws("CARGAS")
                    cell = ws_loads.find(chosen_load)
                    ws_loads.update_cell(cell.row, 6, "CLOSED / SETTLED")
                    
                    st.success("Done: Settlement locked and saved in Cloud.")
                    st.cache_data.clear()

    elif flow == "Modify / Re-Settle Load":
        all_loads = ["Select Load"] + list(loads["LOAD"].astype(str).unique()) if not loads.empty else []
        edit_load_id = st.selectbox("Select the load you wish to modify or re-settle:", all_loads)
        if edit_load_id and edit_load_id != "Select Load":
            load_filtered_df = loads[loads["LOAD"].astype(str).str.strip() == str(edit_load_id).strip()]
            if not load_filtered_df.empty:
                load_match = load_filtered_df.iloc[0]
                e_comp = st.text_input("Broker / Client Name", value=load_match["COMPANY"])
                e_amt = st.number_input("Gross Amount ($)", value=float(load_match["AMOUNT"]), format="%.2f")
                e_stat = st.selectbox("Status", ["PENDING", "IN TRANSIT", "DELIVERED", "CLOSED / SETTLED"], index=["PENDING", "IN TRANSIT", "DELIVERED", "CLOSED / SETTLED"].index(load_match["STATUS"]))
                e_driver = st.selectbox("Driver Assigned", list(drivers["DRIVER_ID"].astype(str).unique()), index=list(drivers["DRIVER_ID"].astype(str).unique()).index(str(load_match["DRIVER_ID"])))
                if st.button("Update and Re-Settle"):
                    ws_loads = get_ws("CARGAS")
                    cell = ws_loads.find(str(edit_load_id))
                    if cell:
                        ws_loads.update_cell(cell.row, 2, e_comp)
                        ws_loads.update_cell(cell.row, 3, float(e_amt))
                        ws_loads.update_cell(cell.row, 6, e_stat)
                        ws_loads.update_cell(cell.row, 9, e_driver)
                        st.success("Done: Load modified in Cloud.")
                        st.cache_data.clear()
            else:
                st.error("Error: Could not retrieve load data.")

    elif flow == "Register Deduction":
        driver_pool = list(drivers["DRIVER_ID"].astype(str).unique()) if not drivers.empty else []
        selected_driver_context = st.selectbox("Filter by Driver:", ["Select Driver"] + driver_pool)
        if selected_driver_context != "Select Driver":
            allowed_cargas = loads[loads["DRIVER_ID"].astype(str) == selected_driver_context]["LOAD"].astype(str).unique()
            if len(allowed_cargas) > 0:
                with st.form("deductions_entry_form", clear_on_submit=True):
                    g1, g2 = st.columns(2)
                    with g1:
                        d_fdate = st.date_input("Date", today)
                        d_cload = st.selectbox("Link to Load", allowed_cargas)
                        d_clog = st.selectbox("Category", ["FUEL", "OTHER"])
                        d_desc = st.text_input("Memo")
                    with g2:
                        d_gal = st.number_input("Gallons", min_value=0.0, step=0.01) if d_clog == "FUEL" else 0.0
                        d_vcost = st.number_input("Total Amount ($)", min_value=0.0, step=1.00, format="%.2f")
                    if st.form_submit_button("Save Deduction"):
                        new_ded = [str(d_fdate), d_cload, selected_driver_context, d_clog, d_desc, float(d_gal), str(today), float(d_vcost)]
                        get_ws("DEDUCTIONS").append_row(new_ded)
                        st.success("Done: Deduction saved in Cloud.")
                        st.cache_data.clear()

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
                new_d = [new_id, new_name, new_phone, new_ops, str(today)]
                get_ws("DRIVERS").append_row(new_d)
                st.success("Done: Driver registered in Cloud.")
                st.cache_data.clear()

# ==================================================
# TAB 6: SEARCH ENGINE
# ==================================================
with tabs[5]:
    st.subheader("Dynamic Search Engine")
    st.caption("Search across active database registries by specific load numbers or driver profiles.")
    st.markdown("---")
    
    col_search_type, col_search_input = st.columns([1, 2])
    
    with col_search_type:
        search_mode = st.radio(
            "Search Category:",
            ["By Load ID", "By Driver ID"],
            horizontal=False
        )
        
    with col_search_input:
        if search_mode == "By Load ID":
            query_string = st.text_input("Enter Load ID digits or characters:", placeholder="e.g., 4052")
            if query_string:
                filtered_results = loads[loads["LOAD"].astype(str).str.contains(query_string, case=False)]
            else:
                filtered_results = loads.copy()
                
        else:
            driver_list = ["Select a Driver..."] + sorted(loads["DRIVER_ID"].dropna().unique().tolist())
            selected_driver = st.selectbox("Select Driver Profile:", driver_list)
            
            if selected_driver != "Select a Driver...":
                filtered_results = loads[loads["DRIVER_ID"] == selected_driver]
            else:
                filtered_results = loads.copy()

    st.markdown("---")
    
    st.markdown(f"**Records Found:** `{len(filtered_results)}` entries matching criteria.")
    
    if len(filtered_results) > 0:
        st.dataframe(filtered_results, width="stretch")
    else:
        st.warning("No records match your search criteria. Please adjust filters.")

# ==================================================
# TAB 7: EXECUTIVE PDF REPORT ENGINE
# ==================================================
with tabs[6]:
    st.subheader("MJ7 Executive Report Engine")
    selected_scope = st.selectbox("Select Report Type Scope:", ["Complete General Financial Overview", "Isolated Driver Analytical View", "Audit Log: Fuel / Diesel Ledger Only"])
    
    def compile_pdf_document(dataframe_source, document_heading, show_totals=False, sum_mj7=0.0, sum_owner=0.0):
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
        header_style = ParagraphStyle('DocHead', parent=text_styles['Heading1'], fontSize=16, leading=20, textColor=colors.HexColor('#0F172A'), spaceAfter=8)
        meta_style = ParagraphStyle('DocMeta', parent=text_styles['Normal'], fontSize=9, textColor=colors.HexColor('#475569'), spaceAfter=14)
        total_style = ParagraphStyle('DocTotals', parent=text_styles['Normal'], fontSize=11, fontName="Helvetica-Bold", textColor=colors.HexColor('#0F172A'), spaceAfter=10)
        cell_style = ParagraphStyle('DataCell', parent=text_styles['Normal'], fontSize=8, alignment=1)
        
        # --- CRUCE PARA EL NOMBRE DEL DRIVER ---
        df_display = dataframe_source.copy()
        if "DRIVER_ID" in df_display.columns:
            drivers_copy = drivers[['DRIVER_ID', 'FULL_NAME']].copy()
            drivers_copy["DRIVER_ID"] = drivers_copy["DRIVER_ID"].astype(str)
            df_display["DRIVER_ID"] = df_display["DRIVER_ID"].astype(str)
            df_display = df_display.merge(drivers_copy, on="DRIVER_ID", how="left")
            df_display.drop(columns=["DRIVER_ID"], inplace=True)
            df_display.rename(columns={"FULL_NAME": "DRIVER"}, inplace=True)

        elements_list.append(Paragraph("MJ7 LOGISTICS CENTER MANAGEMENT REPORT", header_style))
        elements_list.append(Paragraph(f"Scope: {document_heading} | Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", meta_style))
        
        if show_totals:
            elements_list.append(Paragraph(f"TOTAL MJ7 NET PROFIT: ${sum_mj7:,.2f} | TOTAL OPERATOR PAYMENTS: ${sum_owner:,.2f}", total_style))
            elements_list.append(Spacer(1, 10))
            
        # Generar tabla con formato limpio
        cols = df_display.columns.to_list()
        formatted_table_data = [[Paragraph(f"<b>{str(c).replace('_', ' ')}</b>", text_styles['Normal']) for c in cols]]
        
        for _, row in df_display.iterrows():
            row_items = []
            for col in cols:
                val = row[col]
                if col in ["GROSS", "OWNER_PAY", "DISPATCH", "FACTORING", "MJ7_NET", "AMOUNT"]:
                    item_text = f"${float(val):,.2f}" if pd.notnull(val) else "$0.00"
                elif isinstance(val, (datetime, pd.Timestamp)):
                    item_text = val.strftime('%Y-%m-%d')
                else:
                    item_text = str(val) if pd.notnull(val) else ""
                row_items.append(Paragraph(item_text, cell_style))
            formatted_table_data.append(row_items)
            
        report_table = Table(formatted_table_data, repeatRows=1)
        report_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#475569')), # Azul-Gris más claro
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),                # Fuente blanca para contraste
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')])
        ]))
        elements_list.append(report_table)
        pdf_canvas.build(elements_list)
        return byte_stream.getvalue()

    # Lógica de botones
    if selected_scope == "Complete General Financial Overview":
        if st.button("Compile Financial Report"):
            if not settlements.empty:
                pdf_binary = compile_pdf_document(settlements, "General Ledger Executive View", True, settlements['MJ7_NET'].sum(), settlements['OWNER_PAY'].sum())
                st.download_button("📥 Save General Report PDF", pdf_binary, f"MJ7_General_Report_{datetime.now().strftime('%Y%m%d')}.pdf", "application/pdf")
            else:
                st.warning("No records found in settlements database.")

    elif selected_scope == "Isolated Driver Analytical View":
        driver_uid_pick = st.selectbox("Select Target Driver Unique ID:", drivers["DRIVER_ID"].unique() if not drivers.empty else [])
        if st.button("Compile Driver Report") and driver_uid_pick:
            subset = settlements[settlements["DRIVER_ID"].astype(str) == str(driver_uid_pick)]
            if not subset.empty:
                pdf_binary = compile_pdf_document(subset, f"Driver Analytical Ledger ({driver_uid_pick})", True, subset['MJ7_NET'].sum(), subset['OWNER_PAY'].sum())
                st.download_button(f"📥 Save Operator {driver_uid_pick} PDF", pdf_binary, f"MJ7_Driver_{driver_uid_pick}_Report_{datetime.now().strftime('%Y%m%d')}.pdf", "application/pdf")
            else:
                st.warning("This specific driver registry holds no settled entries.")

    elif selected_scope == "Audit Log: Fuel / Diesel Ledger Only":
        if st.button("Compile Deductions Audit"):
            fuel_records = deductions[deductions["TYPE"] == "FUEL"]
            if not fuel_records.empty:
                pdf_binary = compile_pdf_document(fuel_records, "Fuel Audit Ledger Log", False)
                st.download_button("📥 Save Fuel Ledger PDF", pdf_binary, f"MJ7_Fuel_Audit_{datetime.now().strftime('%Y%m%d')}.pdf", "application/pdf")
            else:
                st.warning("No diesel or fuel records logged yet.")
                
# ==================================================
# NUEVA TAB 8: STATUS VERIFICATION MODULE
# ==================================================
with tabs[7]:
    st.subheader("Panel de Verificación de Estatus")
    st.caption("Filtro automático y control de cargas según su fecha de entrega y estado de tránsito.")
    st.divider()

    if not loads.empty:
        loads_alerts = loads.copy()
        loads_alerts["DELIVERY_DATE_DT"] = pd.to_datetime(loads_alerts["DELIVERY_DATE"], errors='coerce').dt.date
        
        criticas = []
        atencion = []
        en_tiempo = []
        entregadas_por_cerrar = []

        for _, row in loads_alerts.iterrows():
            status = str(row["STATUS"]).strip().upper()
            fecha_entrega = row["DELIVERY_DATE_DT"]
            
            if status == "CLOSED / SETTLED" or pd.isna(fecha_entrega):
                continue
                
            try:
                f_entrega_pura = pd.to_datetime(fecha_entrega).date()
                f_hoy_pura = pd.to_datetime(today).date()
                dias_restantes = (f_entrega_pura - f_hoy_pura).days
            except Exception:
                dias_restantes = 999 

            if status == "DELIVERED":
                entregadas_por_cerrar.append((row, "Entrega confirmada. Pendiente de liquidación."))
            elif dias_restantes <= 0 and dias_restantes != 999:
                if dias_restantes == 0:
                    msj = "Entrega programada para el día de hoy."
                else:
                    msj = f"Estatus demorado por {abs(dias_restantes)} días."
                criticas.append((row, msj))
            elif dias_restantes == 1:
                atencion.append((row, "Próxima a finalizar (Mañana)."))
            elif dias_restantes != 999:
                en_tiempo.append((row, f"En tiempo (Faltan {dias_restantes} días)."))

        # Métricas de resumen de alta dirección (Estilo Performance Cards)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Críticas / Vencidas", len(criticas))
        m2.metric("Urgentes (Mañana)", len(atencion))
        m3.metric("Por Liquidar", len(entregadas_por_cerrar))
        m4.metric("En Ruta Segura", len(en_tiempo))
        st.write("")

        # 1. SECCIÓN CRÍTICA (Estilo Performance Card - Alerta Fina)
        if criticas:
            st.markdown("<h5 style='color: #0F172A; font-weight: 600; margin-bottom: 15px;'>Cargas Críticas e Incidencias de Tiempo</h5>", unsafe_allow_html=True)
            for item, motivo in criticas:
                st.markdown(f"""
                <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-left: 5px solid #DC2626; border-radius: 8px; padding: 16px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 600; color: #0F172A; font-size: 14px; text-transform: uppercase; tracking-content: 0.5px;">Carga: {item['LOAD']} &middot; {item['COMPANY']}</span>
                        <span style="font-size: 12px; font-weight: 600; color: #DC2626; background-color: #FEF2F2; padding: 4px 8px; border-radius: 4px;">{motivo}</span>
                    </div>
                    <div style="font-size: 13px; color: #475569; margin-top: 10px; border-top: 1px solid #F1F5F9; padding-top: 10px; display: flex; gap: 15px;">
                        <div><span style="color: #94A3B8; font-weight: 500;">Operador:</span> <span style="font-weight: 500; color: #334155;">{item['DRIVER_ID']}</span></div>
                        <div><span style="color: #94A3B8; font-weight: 500;">Ruta:</span> <span style="font-weight: 500; color: #334155;">{item['ORIGIN']} &rarr; {item['DESTINATION']}</span></div>
                        <div><span style="color: #94A3B8; font-weight: 500;">Estatus:</span> <span style="font-weight: 500; color: #334155;">{item['STATUS']}</span></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            st.write("")

        # 2. SECCIÓN URGENTE (Estilo Performance Card - Precaución Fina)
        if atencion:
            st.markdown("<h5 style='color: #0F172A; font-weight: 600; margin-bottom: 15px;'>Cargas Próximas a Vencer</h5>", unsafe_allow_html=True)
            for item, motivo in atencion:
                st.markdown(f"""
                <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-left: 5px solid #D97706; border-radius: 8px; padding: 16px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 600; color: #0F172A; font-size: 14px; text-transform: uppercase; tracking-content: 0.5px;">Carga: {item['LOAD']} &middot; {item['COMPANY']}</span>
                        <span style="font-size: 12px; font-weight: 600; color: #B45309; background-color: #FEF3C7; padding: 4px 8px; border-radius: 4px;">{motivo}</span>
                    </div>
                    <div style="font-size: 13px; color: #475569; margin-top: 10px; border-top: 1px solid #F1F5F9; padding-top: 10px; display: flex; gap: 15px;">
                        <div><span style="color: #94A3B8; font-weight: 500;">Operador:</span> <span style="font-weight: 500; color: #334155;">{item['DRIVER_ID']}</span></div>
                        <div><span style="color: #94A3B8; font-weight: 500;">Ruta:</span> <span style="font-weight: 500; color: #334155;">{item['ORIGIN']} &rarr; {item['DESTINATION']}</span></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            st.write("")

        # 3. SECCIÓN POR LIQUIDAR (Estilo Performance Card - Concluido Fino)
        if entregadas_por_cerrar:
            st.markdown("<h5 style='color: #0F172A; font-weight: 600; margin-bottom: 15px;'>Servicios Concluidos por Procesar</h5>", unsafe_allow_html=True)
            for item, motivo in entregadas_por_cerrar:
                st.markdown(f"""
                <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-left: 5px solid #2563EB; border-radius: 8px; padding: 16px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.02);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 600; color: #0F172A; font-size: 14px; text-transform: uppercase; tracking-content: 0.5px;">Carga: {item['LOAD']} &middot; {item['COMPANY']}</span>
                        <span style="font-size: 12px; font-weight: 600; color: #1E40AF; background-color: #EFF6FF; padding: 4px 8px; border-radius: 4px;">{motivo}</span>
                    </div>
                    <div style="font-size: 13px; color: #475569; margin-top: 10px; border-top: 1px solid #F1F5F9; padding-top: 10px; display: flex; gap: 15px;">
                        <div><span style="color: #94A3B8; font-weight: 500;">Operador:</span> <span style="font-weight: 500; color: #334155;">{item['DRIVER_ID']}</span></div>
                        <div><span style="color: #94A3B8; font-weight: 500;">Importe Bruto:</span> <span style="font-weight: 600; color: #0F172A;">${float(item['AMOUNT']):,.2f}</span></div>
                        <div><span style="color: #94A3B8; font-weight: 500;">Destino final:</span> <span style="font-weight: 500; color: #334155;">{item['DESTINATION']}</span></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            st.write("")

        if not criticas and not atencion and not entregadas_por_cerrar:
            st.success("El sistema no detecta demoras ni servicios pendientes de liquidación para el día de hoy.")
    else:
        st.info("No se encontraron registros de operaciones activos para el análisis de estatus.")

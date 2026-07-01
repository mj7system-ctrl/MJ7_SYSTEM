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
    st.dataframe(drivers, use_container_width=True)
    
    if not settlements.empty:
        st.markdown("---")
        st.subheader("Production Metrics Matrix")
        
        # Detalle por carga: Agrupamos por Chofer y por Carga (asumiendo LOAD_ID)
        load_col = "LOAD_ID" if "LOAD_ID" in settlements.columns else (settlements.columns[1] if len(settlements.columns) > 1 else settlements.columns[0])
        
        performance_matrix = settlements.groupby(["DRIVER_ID", load_col]).agg({"GROSS": "sum", "OWNER_PAY": "sum", "MJ7_NET": "sum"}).reset_index()
        st.dataframe(
            performance_matrix.style.format({"GROSS": "${:,.2f}", "OWNER_PAY": "${:,.2f}", "MJ7_NET": "${:,.2f}"}), 
            use_container_width=True
        )
        
        # Multiple Driver Selector and Image Generator
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

            # LÓGICA DE REUTILIZACIÓN PARA PILLOW
            def generate_single_card_image(title_suffix, driver_id, name_str, gross, owner_pay, mj7_net):
                img_w, img_h = 600, 260
                img = Image.new("RGB", (img_w, img_h), "#FFFFFF")
                draw = ImageDraw.Draw(img)
                
                draw.rectangle([0, 0, img_w-1, img_h-1], outline="#E2E8F0", width=1)
                draw.text((25, 20), f"MJ7 LOGISTICS CENTER — {title_suffix}", fill="#1E293B")
                draw.text((25, 45), f"Date: {datetime.now().strftime('%Y-%m-%d')}", fill="#64748B")
                
                try:
                    logo_img = Image.open("logo.jpeg").convert("RGB")
                    logo_img = logo_img.resize((70, 35))
                    img.paste(logo_img, (505, 20))
                except Exception:
                    pass
                    
                draw.line([(25, 75), (575, 75)], fill="#E2E8F0", width=1)
                
                draw.rectangle([25, 90, 575, 125], fill="#F8FAFC")
                draw.text((35, 100), f"DRIVER ID: {driver_id}   |   NAME: {name_str}", fill="#334155")
                
                # Caja 1: Gross
                draw.rectangle([25, 145, 195, 230], fill="#F8FAFC", outline="#E2E8F0")
                draw.text((35, 155), "TOTAL GROSS", fill="#64748B")
                draw.text((35, 185), f"${gross:,.2f}", fill="#1E293B")
                
                # Caja 2: Owner Pay
                draw.rectangle([210, 145, 385, 230], fill="#F8FAFC", outline="#E2E8F0")
                draw.text((220, 155), "OWNER PAY", fill="#64748B")
                draw.text((220, 185), f"${owner_pay:,.2f}", fill="#1E293B")
                
                # Caja 3: Net Profit
                draw.rectangle([400, 145, 575, 230], fill="#EFF6FF", outline="#BFDBFE")
                draw.text((410, 155), "MJ7 NET PROFIT", fill="#1E40AF")
                draw.text((410, 185), f"${mj7_net:,.2f}", fill="#1D4ED8")
                
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                return buf.getvalue()

            # Bucle por cada chofer seleccionado
            for d_id in target_perf_drivers:
                # Filtrar todas las cargas de este chofer específico
                driver_loads = performance_matrix[performance_matrix["DRIVER_ID"] == d_id]
                
                try:
                    d_name = drivers[drivers["DRIVER_ID"].astype(str) == str(d_id)]["FULL_NAME"].iloc[0]
                except Exception:
                    d_name = "Unknown Driver Name"
                
                # Línea corregida sin el error de sintaxis del comentario
                st.write(f"### 📋 Performance for: {d_name} ({d_id})")
                
                # 1. GENERAR TARJETA POR CADA CARGA INDIVIDUAL
                for _, load_row in driver_loads.iterrows():
                    current_load_id = load_row[load_col]
                    
                    card_html = f"""
                    <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 24px; font-family: -apple-system, sans-serif; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); margin-bottom: 8px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #F1F5F9; padding-bottom: 16px; margin-bottom: 16px;">
                            <div>
                                <h4 style="margin: 0; color: #1E293B; font-size: 14px; letter-spacing: 0.5px; font-weight: 700;">MJ7 LOGISTICS — LOAD CARD</h4>
                                <span style="font-size: 12px; color: #64748B;">Load Reference: <b>{current_load_id}</b> | Date: {datetime.now().strftime('%Y-%m-%d')}</span>
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
                    
                    # Botón descarga de la carga específica
                    load_img_data = generate_single_card_image(f"LOAD {current_load_id}", d_id, d_name, load_row['GROSS'], load_row['OWNER_PAY'], load_row['MJ7_NET'])
                    st.download_button(
                        label=f"📥 Download Card - Load {current_load_id}",
                        data=load_img_data,
                        file_name=f"MJ7_Load_{current_load_id}_{d_id}.png",
                        mime="image/png",
                        key=f"btn_dl_{d_id}_{current_load_id}"
                    )
                
                # 2. GENERAR TARJETA DE SUMATORIA TOTAL (Solo si tiene más de 1 carga para no repetir)
                if len(driver_loads) > 1:
                    total_gross = driver_loads['GROSS'].sum()
                    total_owner = driver_loads['OWNER_PAY'].sum()
                    total_net = driver_loads['MJ7_NET'].sum()
                    
                    summary_html = f"""
                    <div style="background-color: #F1F5F9; border: 2px dashed #CBD5E1; border-radius: 12px; padding: 24px; font-family: -apple-system, sans-serif; margin-top: 15px; margin-bottom: 8px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #CBD5E1; padding-bottom: 16px; margin-bottom: 16px;">
                            <div>
                                <h4 style="margin: 0; color: #0F172A; font-size: 14px; letter-spacing: 0.5px; font-weight: 800;">MJ7 LOGISTICS — ACCUMULATED TOTALS</h4>
                                <span style="font-size: 12px; color: #475569;">Summary of {len(driver_loads)} loads | Generated today</span>
                            </div>
                            {logo_html_tag}
                        </div>
                        <table style="width: 100%; border-collapse: separate; border-spacing: 16px 0; margin-left: -16px; margin-right: -16px;">
                            <tr>
                                <td style="width: 33.33%; background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 8px; padding: 14px;">
                                    <div style="font-size: 11px; text-transform: uppercase; color: #475569; font-weight: 700;">Accumulated Gross</div>
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
                    
                    # Botón descarga del Gran Total
                    total_img_data = generate_single_card_image("ACCUMULATED TOTALS", d_id, d_name, total_gross, total_owner, total_net)
                    st.download_button(
                        label=f"📊 Download Cumulative Summary Card",
                        data=total_img_data,
                        file_name=f"MJ7_TOTAL_SUMMARY_{d_id}.png",
                        mime="image/png",
                        key=f"btn_dl_total_{d_id}"
                    )
                
                st.markdown("<hr style='border: 1px dashed #E2E8F0;'>", unsafe_allow_html=True)
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
            
            m_base = gross_revenue * 0.15
            o_base = gross_revenue * 0.85
            disp_fee = gross_revenue * 0.05
            
            # ==================================================
            # INTERRUPTOR DE FACTORING OPCIONAL
            # ==================================================
            aplicar_factoring = st.checkbox("¿Aplicar cobro de Factoring (2.15%) a esta carga?", value=True)
            
            if aplicar_factoring:
                fact_fee = gross_revenue * 0.0215
            else:
                fact_fee = 0.00 
            
            mj7_final = m_base - disp_fee - fact_fee
            owner_final = o_base - fuel_deductions - other_deductions
            
            # ==================================================
            # PREVISUALIZACIÓN VISUAL ANTES DE AUTORIZAR
            # ==================================================
            st.markdown("""
            <div style="background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 15px; margin: 15px 0 15px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <h4 style="color: #0047AB; margin-top: 0; margin-bottom: 5px;">📋 Previsualización Financiera</h4>
                <p style="font-size: 13px; color: #475569; margin-bottom: 0;">Verifica los montos calculados antes de bloquear y autorizar el pago.</p>
            </div>
            """, unsafe_allow_html=True)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Gross Revenue", f"${gross_revenue:,.2f}")
            c2.metric("Factoring Fee", f"${fact_fee:,.2f}", delta="-2.15%" if aplicar_factoring else "Sin Factoring", delta_color="inverse" if aplicar_factoring else "normal")
            c3.metric("Fuel Deductions", f"${fuel_deductions:,.2f}")
            c4.metric("Other Deductions", f"${other_deductions:,.2f}")

            st.write("") 

            c5, c6 = st.columns(2)
            with c5:
                st.markdown(f"""
                <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 15px; border-radius: 8px; text-align: center;">
                    <span style="font-size: 12px; color: #64748B; font-weight: 600; text-transform: uppercase;">Pago Neto Chofer (Owner Pay)</span>
                    <h2 style="color: #0F172A; margin: 5px 0 0 0;">${owner_final:,.2f}</h2>
                </div>
                """, unsafe_allow_html=True)
            with c6:
                st.markdown(f"""
                <div style="background-color: #E0F2FE; border: 1px solid #BAE6FD; padding: 15px; border-radius: 8px; text-align: center;">
                    <span style="font-size: 12px; color: #0369A1; font-weight: 600; text-transform: uppercase;">Rendimiento Neto MJ7</span>
                    <h2 style="color: #0369A1; margin: 5px 0 0 0;">${mj7_final:,.2f}</h2>
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
                e_stat = st.selectbox("Status", ["PENDING", "IN TRANSIT", "DELIMITED", "CLOSED / SETTLED"], index=["PENDING", "IN TRANSIT", "DELIVERED", "CLOSED / SETTLED"].index(load_match["STATUS"]))
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

    

# TAB 6: SEARCH ENGINE (Se queda igual, ya lee de memoria)
with tabs[5]:
    st.subheader("Dynamic Load Search Engine")
    query_string = st.text_input("Enter load ID digits or characters:")
    if query_string:
        filtered_results = loads[loads["LOAD"].astype(str).str.contains(query_string, case=False)]
        st.dataframe(filtered_results, use_container_width=True)

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
    st.subheader("🚦 Panel de Alertas y Verificación de Estatus")
    st.caption("Filtro automático de cargas críticas según su fecha de entrega y estado de tránsito.")
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
                
            # ==================================================
            # PROTECCIÓN DE TIPOS DE FECHA (CORRECCIÓN DE ERROR)
            # ==================================================
            from datetime import date
            f_entrega_pura = fecha_entrega if isinstance(fecha_entrega, date) else pd.to_datetime(fecha_entrega).date()
            f_hoy_pura = today if isinstance(today, date) else pd.to_datetime(today).date()
            
            dias_restantes = (f_entrega_pura - f_hoy_pura).days

            if status == "DELIVERED":
                entregadas_por_cerrar.append((row, f"✅ ¡Entregada! Lista para el módulo de liquidaciones."))
            elif dias_restantes <= 0:
                if dias_restantes == 0:
                    msj = "🚨 ¡SE ENTREGA HOY! Monitorear ubicación urgente."
                else:
                    msj = f"⚠️ RETRASADA: Debió entregarse hace {abs(dias_restantes)} días."
                criticas.append((row, msj))
            elif dias_restantes == 1:
                atencion.append((row, "⏳ Próxima a finalizar: Se entrega mañana."))
            else:
                en_tiempo.append((row, f"🟢 En tiempo (Faltan {dias_restantes} días)."))

        # Métricas de resumen ejecutivo
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🔴 Críticas / Vencidas", len(criticas))
        m2.metric("🟡 Urgentes (Mañana)", len(atencion))
        m3.metric("🔵 Por Liquidar", len(entregadas_por_cerrar))
        m4.metric("🟢 En ruta segura", len(en_tiempo))
        st.write("")

        # 1. CARGAS CRÍTICAS (ROJO)
        if criticas:
            st.markdown("<h4 style='color: #DC2626;'>🚨 Cargas Críticas / Vencidas</h4>", unsafe_allow_html=True)
            for item, motivo in criticas:
                st.markdown(f"""
                <div style="background-color: #FEF2F2; border-left: 5px solid #DC2626; border-top: 1px solid #FCA5A5; border-right: 1px solid #FCA5A5; border-bottom: 1px solid #FCA5A5; border-radius: 4px; padding: 12px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="font-weight: bold; color: #991B1B;">📦 Carga: {item['LOAD']} ({item['COMPANY']})</span>
                        <span style="font-weight: bold; color: #DC2626;">{motivo}</span>
                    </div>
                    <div style="font-size: 13px; color: #7F1D1D; margin-top: 5px;">
                        <b>Chofer ID:</b> {item['DRIVER_ID']} | <b>Ruta:</b> {item['ORIGIN']} ➡️ {item['DESTINATION']} | <b>Estatus:</b> {item['STATUS']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            st.write("")

        # 2. CARGAS URGENTES (AMARILLO)
        if atencion:
            st.markdown("<h4 style='color: #D97706;'>⏳ Próximas a Vencer (Mañana)</h4>", unsafe_allow_html=True)
            for item, motivo in atencion:
                st.markdown(f"""
                <div style="background-color: #FEF3C7; border-left: 5px solid #D97706; border-top: 1px solid #FDE68A; border-right: 1px solid #FDE68A; border-bottom: 1px solid #FDE68A; border-radius: 4px; padding: 12px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="font-weight: bold; color: #92400E;">📦 Carga: {item['LOAD']} ({item['COMPANY']})</span>
                        <span style="font-weight: bold; color: #B45309;">{motivo}</span>
                    </div>
                    <div style="font-size: 13px; color: #78350F; margin-top: 5px;">
                        <b>Chofer ID:</b> {item['DRIVER_ID']} | <b>Ruta:</b> {item['ORIGIN']} ➡️ {item['DESTINATION']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            st.write("")

        # 3. ENTREGADAS POR LIQUIDAR (AZUL)
        if entregadas_por_cerrar:
            st.markdown("<h4 style='color: #2563EB;'>💵 Entregadas listas para Liquidar</h4>", unsafe_allow_html=True)
            for item, motivo in entregadas_por_cerrar:
                st.markdown(f"""
                <div style="background-color: #EFF6FF; border-left: 5px solid #2563EB; border-top: 1px solid #BFDBFE; border-right: 1px solid #BFDBFE; border-bottom: 1px solid #BFDBFE; border-radius: 4px; padding: 12px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="font-weight: bold; color: #1E40AF;">📦 Carga: {item['LOAD']} ({item['COMPANY']})</span>
                        <span style="font-weight: bold; color: #2563EB;">{motivo}</span>
                    </div>
                    <div style="font-size: 13px; color: #1E3A8A; margin-top: 5px;">
                        <b>Chofer ID:</b> {item['DRIVER_ID']} | <b>Monto Gross:</b> ${float(item['AMOUNT']):,.2f} | <b>Destino:</b> {item['DESTINATION']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            st.write("")

        if not criticas and not atencion and not entregadas_por_cerrar:
            st.success("🎉 ¡Excelente! No tienes ninguna carga retrasada, urgente ni entregas pendientes por liquidar el día de hoy.")
    else:
        st.info("No hay registros de cargas activos en el sistema para evaluar estatus.")

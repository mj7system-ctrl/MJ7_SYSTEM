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
    ":material/picture_as_pdf: PDF Reports"
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
        performance_matrix = settlements.groupby("DRIVER_ID").agg({"GROSS": "sum", "OWNER_PAY": "sum", "MJ7_NET": "sum"}).reset_index()
        st.dataframe(
            performance_matrix.style.format({"GROSS": "${:,.2f}", "OWNER_PAY": "${:,.2f}", "MJ7_NET": "${:,.2f}"}), 
            use_container_width=True
        )
        
        # Multiple Driver Selector and Image Generator
        st.markdown("---")
        st.subheader("Generate Performance Cards")
        target_perf_drivers = st.multiselect("Select drivers to generate cards:", performance_matrix["DRIVER_ID"].unique())
        
        if target_perf_drivers:
            # Importación de Base64 para inyectar el logo directo en la barra azul del HTML
            import base64
            try:
                with open("logo.jpeg", "rb") as image_file:
                    encoded_logo = base64.b64encode(image_file.read()).decode()
                logo_html_tag = f'<img src="data:image/jpeg;base64,{encoded_logo}" style="height: 40px; border-radius: 4px; border: 1px solid #334155;">'
            except Exception:
                logo_html_tag = ''

            # Bucle Limpio: Genera una tarjeta única e independiente por cada chofer seleccionado
            for d_id in target_perf_drivers:
                drv_data = performance_matrix[performance_matrix["DRIVER_ID"] == d_id].iloc[0]
                
                try:
                    d_name = drivers[drivers["DRIVER_ID"].astype(str) == str(d_id)]["FULL_NAME"].iloc[0]
                except Exception:
                    d_name = "Unknown Driver Name"
                
                # Renderizado HTML limpio en pantalla en tonos grises oscuros y azul marino
                card_html = f"""
                <div class="performance-card-container">
                    <div class="performance-card-header">
                        <div class="performance-card-header-text">
                            <h4>MJ7 LOGISTICS CENTER — PERFORMANCE CARD</h4>
                            <span>Generated on: {datetime.now().strftime('%Y-%m-%d')}</span>
                        </div>
                        {logo_html_tag}
                    </div>
                    <div class="performance-card-body">
                        <div class="driver-meta-info">
                            <strong style="color: #38BDF8;">DRIVER ID:</strong> {d_id} &nbsp;|&nbsp; <strong style="color: #38BDF8;">NAME:</strong> {d_name}
                        </div>
                        <div class="performance-grid-layout">
                            <div class="perf-item-box">
                                <div class="perf-item-label">Total Gross</div>
                                <div class="perf-item-value">${drv_data['GROSS']:,.2f}</div>
                            </div>
                            <div class="perf-item-box">
                                <div class="perf-item-label">Owner Pay</div>
                                <div class="perf-item-value">${drv_data['OWNER_PAY']:,.2f}</div>
                            </div>
                            <div class="perf-item-box highlighted">
                                <div class="perf-item-label" style="color: #38BDF8;">MJ7 Net Profit</div>
                                <div class="perf-item-value" style="color: #38BDF8;">${drv_data['MJ7_NET']:,.2f}</div>
                            </div>
                        </div>
                    </div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
                
                # Lógica Nativa para Generar y Descargar la Imagen PNG de este Chofer Específico
                def generate_single_card_image(driver_id, name_str, row_data):
                    img_w, img_h = 600, 260
                    img = Image.new("RGB", (img_w, img_h), "#1E293B")
                    draw = ImageDraw.Draw(img)
                    
                    # Header Azul/Negro de la Tarjeta Imagen
                    draw.rectangle([0, 0, img_w, 75], fill="#1B2631")
                    draw.text((25, 18), "MJ7 LOGISTICS CENTER — PERFORMANCE CARD", fill="#38BDF8")
                    draw.text((25, 45), f"Date: {datetime.now().strftime('%Y-%m-%d')}", fill="#94A3B8")
                    
                    # Intentar pegar el logo físico en la esquina derecha del header de la imagen
                    try:
                        logo_img = Image.open("logo.jpeg").convert("RGB")
                        logo_img = logo_img.resize((70, 35))
                        img.paste(logo_img, (505, 20))
                    except Exception:
                        pass
                        
                    # Línea divisoria azul brillante
                    draw.line([(0, 75), (img_w, 75)], fill="#38BDF8", width=2)
                    
                    # Metadatos del Chofer en el bloque Gris
                    draw.text((25, 95), f"DRIVER ID: {driver_id}   |   NAME: {name_str}", fill="#FFFFFF")
                    
                    # Grid de Indicadores Financieros
                    # Caja 1: Gross
                    draw.rectangle([25, 135, 195, 225], fill="#0F172A", outline="#334155")
                    draw.text((40, 148), "TOTAL GROSS", fill="#94A3B8")
                    draw.text((40, 180), f"${row_data['GROSS']:,.2f}", fill="#F8FAFC")
                    
                    # Caja 2: Owner Pay
                    draw.rectangle([210, 135, 385, 225], fill="#0F172A", outline="#334155")
                    draw.text((225, 148), "OWNER PAY", fill="#94A3B8")
                    draw.text((225, 180), f"${row_data['OWNER_PAY']:,.2f}", fill="#F8FAFC")
                    
                    # Caja 3: MJ7 Net (Resaltada)
                    draw.rectangle([400, 135, 575, 225], fill="#0F172A", outline="#38BDF8")
                    draw.text((415, 148), "MJ7 NET PROFIT", fill="#38BDF8")
                    draw.text((415, 180), f"${row_data['MJ7_NET']:,.2f}", fill="#38BDF8")
                    
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    return buf.getvalue()
                
                single_img_data = generate_single_card_image(d_id, d_name, drv_data)
                st.download_button(
                    label=f"📥 Download Card Image ({d_id})",
                    data=single_img_data,
                    file_name=f"MJ7_Performance_{d_id}_{datetime.now().strftime('%Y%m%d')}.png",
                    mime="image/png",
                    key=f"btn_dl_{d_id}"
                )
                st.markdown("<br>", unsafe_allow_html=True)

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
            fact_fee = gross_revenue * 0.0215
            
            mj7_final = m_base - disp_fee - fact_fee
            owner_final = o_base - fuel_deductions - other_deductions
            
            if st.button("Authorize Settlement"):
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

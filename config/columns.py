# config/columns.py
"""
MAPEO CENTRALIZADO DE COLUMNAS
Una sola fuente de verdad para nombres de columnas
"""

COLUMN_MAPS = {
    "CARGAS": {
        "load_id": "LOAD",
        "company": "COMPANY",
        "amount": "AMOUNT",
        "start_date": "START_DATE",
        "delivery_date": "DELIVERY_DATE",
        "status": "STATUS",
        "origin": "ORIGIN",
        "destination": "DESTINATION",
        "driver_id": "DRIVER_ID",
    },
    "SETTLEMENTS": {
        "date": "DATE",
        "load_id": "LOAD_ID",
        "driver_id": "DRIVER_ID",
        "gross": "GROSS",
        "owner_pay": "OWNER_PAY",
        "dispatch_fee": "DISPATCH",
        "factoring_fee": "FACTORING",
        "mj7_net": "MJ7_NET",
    },
    "DEDUCTIONS": {
        "date": "DATE",
        "load_id": "LOAD_NUMBER",
        "driver_id": "DRIVER_ID",
        "type": "TYPE",
        "concept": "CONCEPT",
        "qty_gallons": "QTY_GALLONS",
        "posted_date": "POSTED_DATE",
        "amount": "AMOUNT",
    },
    "DRIVERS": {
        "driver_id": "DRIVER_ID",
        "full_name": "FULL_NAME",
        "phone": "PHONE_NUMBER",
        "status": "OPERATIONAL_STATUS",
        "date_joined": "DATE_JOINED",
    },
    "EXPENSE_FINANCIAMIENTOS": {
        "id_fin": "ID_FIN",
        "driver": "DRIVER",
        "truck_id": "TRUCK_ID",
        "concept": "CONCEPT",
        "total_to_pay": "TOTAL_TO_PAY",
        "installments_paid": "INSTALLMENTS_PAID",
        "friday_1": "FRIDAY_1",
        "friday_2": "FRIDAY_2",
        "friday_3": "FRIDAY_3",
        "friday_4": "FRIDAY_4",
    },
    "TRUCK_PAYMENTS": {
        "driver": "DRIVER",
        "truck_id": "TRUCK_ID",
        "total_value": "TOTAL_VALUE",
        "weekly_amortization": "WEEKLY_AMORTIZATION",
        "total_paid": "TOTAL_PAID",
        "start_date": "START_DATE",
    },
    "DISPATCH_TRACKER": {
        "date": "DATE",
        "person": "PERSON",
        "concept": "CONCEPT",
        "amount": "AMOUNT",
    },
    "AP_MJ7": {
        "ap_id": "AP_ID",
        "company_name": "COMPANY_NAME",
        "date_created": "DATE_CREATED",
        "vendor_name": "VENDOR_NAME",
        "invoice_number": "INVOICE_NUMBER",
        "description": "DESCRIPTION",
        "amount_due": "AMOUNT_DUE",
        "amount_paid": "AMOUNT_PAID",
        "due_date": "DUE_DATE",
        "status": "STATUS",
        "category": "CATEGORY",
        "notes": "NOTES",
    },
    "AR_MJ7": {
        "ar_id": "AR_ID",
        "date_created": "DATE_CREATED",
        "customer_name": "CUSTOMER_NAME",
        "invoice_number": "INVOICE_NUMBER",
        "description": "DESCRIPTION",
        "amount_due": "AMOUNT_DUE",
        "amount_received": "AMOUNT_RECEIVED",
        "due_date": "DUE_DATE",
        "status": "STATUS",
        "load_reference": "LOAD_REFERENCE",
        "notes": "NOTES",
    },
    "AP_GCI": {
        "ap_id": "AP_ID",
        "company_name": "COMPANY_NAME",
        "date_created": "DATE_CREATED",
        "vendor_name": "VENDOR_NAME",
        "invoice_number": "INVOICE_NUMBER",
        "description": "DESCRIPTION",
        "amount_due": "AMOUNT_DUE",
        "amount_paid": "AMOUNT_PAID",
        "due_date": "DUE_DATE",
        "status": "STATUS",
        "category": "CATEGORY",
        "notes": "NOTES",
    },
    "AR_GCI": {
        "ar_id": "AR_ID",
        "company_name": "COMPANY_NAME",
        "date_created": "DATE_CREATED",
        "customer_name": "CUSTOMER_NAME",
        "invoice_number": "INVOICE_NUMBER",
        "description": "DESCRIPTION",
        "amount_due": "AMOUNT_DUE",
        "amount_received": "AMOUNT_RECEIVED",
        "due_date": "DUE_DATE",
        "status": "STATUS",
        "load_reference": "LOAD_REFERENCE",
        "notes": "NOTES",
    },
}

REQUIRED_COLUMNS = {
    "CARGAS": ["load_id", "company", "amount", "driver_id", "status"],
    "SETTLEMENTS": ["date", "load_id", "driver_id", "gross", "mj7_net"],
    "DEDUCTIONS": ["date", "load_id", "amount", "type"],
    "DRIVERS": ["driver_id", "full_name"],
    "DISPATCH_TRACKER": ["date", "person", "amount"],
    "AP_MJ7": ["ap_id", "vendor_name", "amount_due", "due_date", "status"],
    "AR_MJ7": ["ar_id", "customer_name", "amount_due", "due_date", "status"],
    "AP_GCI": ["ap_id", "vendor_name", "amount_due", "due_date", "status"],
    "AR_GCI": ["ar_id", "customer_name", "amount_due", "due_date", "status"],
}

COMPANY_SHEETS = {
    "MJ7": {"ap": "AP_MJ7", "ar": "AR_MJ7"},
    "GCI": {"ap": "AP_GCI", "ar": "AR_GCI"},
}


def get_col(sheet_name: str, canonical_name: str) -> str:
    """Obtener nombre REAL de columna desde nombre CANONICAL."""
    if sheet_name not in COLUMN_MAPS:
        raise KeyError(f"❌ Hoja desconocida: {sheet_name}")
    if canonical_name not in COLUMN_MAPS[sheet_name]:
        raise KeyError(f"❌ Columna '{canonical_name}' no existe en {sheet_name}")
    return COLUMN_MAPS[sheet_name][canonical_name]


def get_company_sheets(company: str) -> dict:
    """Obtener hojas de AP/AR para una empresa específica."""
    if company not in COMPANY_SHEETS:
        raise KeyError(f"❌ Empresa desconocida: {company}")
    return COMPANY_SHEETS[company]


def validate_sheet_columns(df, sheet_name: str) -> list:
    """Validar que DataFrame tiene todas las columnas requeridas."""
    required = REQUIRED_COLUMNS.get(sheet_name, [])
    canonical_cols = [get_col(sheet_name, c) for c in required]
    missing = [c for c in canonical_cols if c not in df.columns]
    return missing

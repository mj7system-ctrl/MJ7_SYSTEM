"""
Column mapping configuration for all sheets.
Maps logical names to actual column headers.
"""

COLUMN_MAPS = {
    "CARGAS": {
        "load_id": "LOAD_ID",
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
        "gross": "GROSS_AMOUNT",
        "owner_pay": "OWNER_PAY",
        "dispatch_fee": "DISPATCH_FEE",
        "factoring_fee": "FACTORING_FEE",
        "mj7_net": "MJ7_NET",
    },
    "DEDUCTIONS": {
        "date": "DATE",
        "load_id": "LOAD_ID",
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
        "phone": "PHONE",
        "status": "STATUS",
        "hire_date": "HIRE_DATE",
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
    # AP/AR MAPPINGS - MJ7
    "AP_MJ7": {
        "id": "ID",
        "date": "DATE",
        "supplier": "SUPPLIER",
        "invoice_number": "INVOICE_NUMBER",
        "description": "DESCRIPTION",
        "amount": "AMOUNT",
        "due_date": "DUE_DATE",
        "status": "STATUS",
        "payment_date": "PAYMENT_DATE",
        "notes": "NOTES",
    },
    "AR_MJ7": {
        "id": "ID",
        "date": "DATE",
        "client": "CLIENT",
        "invoice_number": "INVOICE_NUMBER",
        "description": "DESCRIPTION",
        "amount": "AMOUNT",
        "due_date": "DUE_DATE",
        "status": "STATUS",
        "payment_date": "PAYMENT_DATE",
        "notes": "NOTES",
    },
    "AP_GCI": {
        "id": "ID",
        "date": "DATE",
        "supplier": "SUPPLIER",
        "invoice_number": "INVOICE_NUMBER",
        "description": "DESCRIPTION",
        "amount": "AMOUNT",
        "due_date": "DUE_DATE",
        "status": "STATUS",
        "payment_date": "PAYMENT_DATE",
        "notes": "NOTES",
    },
    "AR_GCI": {
        "id": "ID",
        "date": "DATE",
        "client": "CLIENT",
        "invoice_number": "INVOICE_NUMBER",
        "description": "DESCRIPTION",
        "amount": "AMOUNT",
        "due_date": "DUE_DATE",
        "status": "STATUS",
        "payment_date": "PAYMENT_DATE",
        "notes": "NOTES",
    },
}

def get_col(sheet_name, logical_name):
    """
    Get the actual column name from logical name.
    Returns the column header string.
    """
    if sheet_name not in COLUMN_MAPS:
        raise ValueError(f"Sheet '{sheet_name}' not found in COLUMN_MAPS")
    
    if logical_name not in COLUMN_MAPS[sheet_name]:
        raise ValueError(f"Column '{logical_name}' not found in sheet '{sheet_name}'")
    
    return COLUMN_MAPS[sheet_name][logical_name]

def validate_sheet_columns(df, sheet_name):
    """
    Validate that a dataframe has all required columns for a sheet.
    Returns (is_valid, error_message)
    """
    if df.empty:
        return True, None
    
    required_cols = list(COLUMN_MAPS[sheet_name].values())
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        return False, f"Missing columns: {', '.join(missing_cols)}"
    
    return True, None

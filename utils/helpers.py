# utils/helpers.py
"""
FUNCIONES AUXILIARES REUTILIZABLES
Conversiones seguras, formateo, validación
"""

import pandas as pd
from typing import Any, Union
from datetime import datetime


# =================== CONVERSIONES SEGURAS ===================

def safe_float(value: Any, default: float = 0.0) -> float:
    """Convertir a FLOAT de forma segura."""
    try:
        return float(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """Convertir a INT de forma segura."""
    try:
        result = float(value) if value is not None else default
        return int(result) if result == int(result) else int(result)
    except (TypeError, ValueError):
        return default


# =================== FORMATEO ===================

def money(value: Union[float, int], decimals: int = 2) -> str:
    """Formatear como MONEDA USD con separadores de miles."""
    amount = safe_float(value)
    return f"${amount:,.{decimals}f}"


def format_gallons(value: Any) -> Union[int, float]:
    """Formatear galones: INT si es entero, FLOAT si decimal."""
    num = safe_float(value)
    return int(num) if num == int(num) else num


def safe_date_str(value: Any, fmt: str = '%Y-%m-%d') -> str:
    """Convertir a STRING de fecha de forma segura."""
    try:
        if isinstance(value, str):
            dt = pd.to_datetime(value)
        else:
            dt = value
        return dt.strftime(fmt)
    except Exception:
        return ""


# =================== PARSING ===================

def parse_date(value: Any) -> Union[pd.Timestamp, None]:
    """Parsear fecha de forma segura."""
    try:
        dt = pd.to_datetime(value, errors='coerce')
        return dt if pd.notnull(dt) else None
    except Exception:
        return None


def safe_to_numeric(series: pd.Series, errors: str = 'coerce') -> pd.Series:
    """Convertir SERIE a numérica de forma segura."""
    return pd.to_numeric(series, errors=errors)


def sorted_unique_safe(series: pd.Series) -> list:
    """Retornar valores ÚNICOS y ORDENADOS, manejando tipos mixtos."""
    try:
        unique_vals = series.dropna().unique()
        str_vals = [str(v) for v in unique_vals]
        return sorted(str_vals)
    except Exception:
        return []


# =================== VALIDACIÓN ===================

def validate_dataframe(df, sheet_name: str) -> tuple:
    """Validar que DataFrame tiene estructura correcta."""
    from config.columns import validate_sheet_columns
    
    errors = []
    missing = validate_sheet_columns(df, sheet_name)
    if missing:
        errors.append(f"Faltan columnas en {sheet_name}: {', '.join(missing)}")
    if df.empty:
        errors.append(f"{sheet_name} está vacío")
    
    return len(errors) == 0, errors

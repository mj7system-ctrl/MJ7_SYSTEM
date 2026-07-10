"""
Google Sheets operations module.
Handles all interactions with Google Sheets API safely and efficiently.
"""

import pandas as pd
from config.columns import get_col

class SheetsOperations:
    """Class to handle Google Sheets operations safely."""
    
    def __init__(self, client, sheet_name):
        """
        Initialize SheetsOperations.
        """
        self.client = client
        self.sheet_name = sheet_name
    
    def find_row_by_column(self, df, sheet_name, search_col_name, search_value):
        """
        Find a row in dataframe by column value.
        """
        try:
            col = get_col(sheet_name, search_col_name)
            matches = df[df[col].astype(str) == str(search_value)]
            
            if matches.empty:
                return None
            return matches.iloc[0]
        except Exception as e:
            print(f"❌ Error finding row: {e}")
            return None
    
    def update_cell_by_column(self, ws, df, sheet_name, search_col, search_value, update_col, new_value):
        """
        Update a cell using local DataFrame index to minimize API calls.
        """
        try:
            # 1. Obtener nombres reales de columnas
            search_col_actual = get_col(sheet_name, search_col)
            update_col_actual = get_col(sheet_name, update_col)
            
            # 2. Localizar la fila usando el DataFrame (Sin llamadas API)
            df_filtered = df[df[search_col_actual].astype(str) == str(search_value)]
            if df_filtered.empty:
                raise ValueError(f"❌ Valor '{search_value}' no encontrado en el DataFrame.")
            
            # La fila en Sheets = índice del DF + 2 (1 por encabezado, 1 por base 0 del DF)
            row_idx = df_filtered.index[0] + 2
            
            # 3. Localizar la columna usando el DataFrame (Sin llamadas API)
            col_idx = df.columns.get_loc(update_col_actual) + 1
            
            # 4. Una sola llamada a la API para actualizar
            ws.update_cell(row_idx, col_idx, new_value)
            
            print(f"✅ Updated {update_col_actual} to '{new_value}' at ({row_idx}, {col_idx})")
            
        except Exception as e:
            print(f"❌ Error updating cell: {e}")
            raise

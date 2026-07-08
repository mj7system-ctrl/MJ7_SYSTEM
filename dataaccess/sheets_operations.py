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
        
        Args:
            client: gspread authorized client
            sheet_name: Name of the Google Sheet
        """
        self.client = client
        self.sheet_name = sheet_name
    
    def find_row_by_column(self, df, sheet_name, search_col_name, search_value):
        """
        Find a row in dataframe by column value.
        Uses the COLUMN_MAPS to resolve logical names to actual column names.
        
        Args:
            df: DataFrame to search
            sheet_name: Name of the sheet (for column mapping)
            search_col_name: Logical column name to search in (e.g., "load_id")
            search_value: Value to search for
        
        Returns:
            Row as dict-like object or None if not found
        """
        try:
            # Get actual column name from mapping
            col = get_col(sheet_name, search_col_name)
            
            # Convert both to string for comparison
            matches = df[df[col].astype(str) == str(search_value)]
            
            if matches.empty:
                return None
            
            return matches.iloc[0]
        except Exception as e:
            print(f"❌ Error finding row: {e}")
            return None
    
    def update_cell_by_column(self, ws, df, sheet_name, search_col, search_value, update_col, new_value):
        """
        Update a cell in worksheet by finding row and column.
        
        Args:
            ws: Worksheet object
            df: DataFrame to reference
            sheet_name: Name of the sheet
            search_col: Logical column name to search (e.g., "load_id")
            search_value: Value to search for
            update_col: Logical column name to update (e.g., "status")
            new_value: New value to set
        
        Raises:
            ValueError: If row or column not found
        """
        try:
            # Get actual column names from mapping
            search_col_actual = get_col(sheet_name, search_col)
            update_col_actual = get_col(sheet_name, update_col)
            
            # Find row in dataframe
            row_match = self.find_row_by_column(df, sheet_name, search_col, search_value)
            if row_match is None:
                raise ValueError(f"❌ Value '{search_value}' not found in column '{search_col_actual}'")
            
            # Find cell in worksheet by search value
            cell = ws.find(str(search_value))
            if cell is None:
                raise ValueError(f"❌ Cell with value '{search_value}' not found in worksheet")
            
            # Get column index of update_col from header row
            header_row = ws.row_values(1)
            try:
                col_idx = header_row.index(update_col_actual) + 1
            except ValueError:
                raise ValueError(f"❌ Column '{update_col_actual}' not found in worksheet header")
            
            # Update cell at found row with new column index
            ws.update_cell(cell.row, col_idx, new_value)
            print(f"✅ Updated {update_col_actual} to '{new_value}' for {search_col_actual} '{search_value}'")
            
        except Exception as e:
            print(f"❌ Error updating cell: {e}")
            raise

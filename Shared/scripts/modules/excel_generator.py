import pandas as pd
import sqlite3
import os
from datetime import datetime

class ExcelGenerator:
    """
    Generates Excel sheets based on SQL queries for user updates.
    """
    def __init__(self, db_path):
        self.db_path = db_path

    def get_conn(self):
        return sqlite3.connect(self.db_path)

    def generate_update_sheet(self, sql_query, update_type, output_dir):
        """
        Generates an Excel sheet with data from sql_query.
        Adds instruction columns based on update_type.
        """
        conn = self.get_conn()
        try:
            df = pd.read_sql_query(sql_query, conn)
        except Exception as e:
            return {"error": f"SQL Error: {e}"}
        finally:
            conn.close()

        # Add metadata sheet or columns to track what this is for
        # We'll use a hidden sheet or just filename convention. 
        # Let's use filename convention + a 'Instructions' sheet.
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"Update_{update_type}_{timestamp}.xlsx"
        output_path = os.path.join(output_dir, filename)
        
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Data Sheet
            df.to_excel(writer, sheet_name='Data', index=False)
            
            # Instructions Sheet
            instructions = pd.DataFrame({
                'Field': ['Update Type', 'Generated At', 'Instructions'],
                'Value': [update_type, timestamp, 'Modify the columns in the Data sheet. Do NOT change ID columns.']
            })
            instructions.to_excel(writer, sheet_name='Info', index=False)
            
        return {"success": True, "path": output_path, "rows": len(df)}

    def process_update_sheet(self, file_path):
        """
        Reads the update sheet and applies changes to the DB.
        This is a generic updater that assumes the user modified the 'Data' sheet.
        """
        try:
            # Read Info to know what to do
            info_df = pd.read_excel(file_path, sheet_name='Info')
            update_type = info_df[info_df['Field'] == 'Update Type']['Value'].values[0]
            
            # Read Data
            df = pd.read_excel(file_path, sheet_name='Data')
            
            conn = self.get_conn()
            cursor = conn.cursor()
            updated_count = 0
            
            if update_type == 'update_house_details':
                # Expects 'id' or 'object_id' and fields like 'aantal_sk', 'aantal_pers', 'kluis_code_1'
                for _, row in df.iterrows():
                    # Identify row
                    if 'id' in row:
                        pk = row['id']
                        pk_col = 'id'
                    elif 'object_id' in row:
                        pk = row['object_id']
                        pk_col = 'object_id'
                    else:
                        continue
                        
                    # Build Update Query dynamically based on columns present
                    # We only update columns that exist in the table and are not the PK
                    # For safety, we should whitelist columns or check schema.
                    # For now, let's assume columns in DF match DB columns.
                    
                    # Fetch current schema to verify columns
                    cursor.execute(f"PRAGMA table_info(huizen)")
                    valid_cols = [r[1] for r in cursor.fetchall()]
                    
                    fields = []
                    vals = []
                    
                    for col in df.columns:
                        if col in valid_cols and col != pk_col:
                            val = row[col]
                            # Handle NaN
                            if pd.isna(val): val = None
                            
                            fields.append(f"{col} = ?")
                            vals.append(val)
                            
                    if fields:
                        query = f"UPDATE huizen SET {', '.join(fields)} WHERE {pk_col} = ?"
                        vals.append(pk)
                        cursor.execute(query, vals)
                        updated_count += 1
                        
            elif update_type == 'update_contract':
                # Similar logic for contracts
                pass # Implement as needed
                
            conn.commit()
            conn.close()
            return {"success": True, "updated": updated_count}
            
        except Exception as e:
            return {"error": str(e)}

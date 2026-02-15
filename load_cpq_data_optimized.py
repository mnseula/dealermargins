# Save the current optimized function as a reference
# I'll create helper functions for CSV bulk loading that can be reused

import csv
import tempfile
import os
from typing import List, Dict

def bulk_load_to_temp_table(cursor, csv_data: List[tuple], temp_table_name: str, columns: List[str]):
    """
    Generic function to bulk load data via CSV into a temporary table
    
    Args:
        cursor: MySQL cursor
        csv_data: List of tuples containing row data
        temp_table_name: Name of temporary table
        columns: List of column names
    """
    # Create temp CSV file
    temp_csv = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='')
    
    try:
        # Write data to CSV
        writer = csv.writer(temp_csv)
        for row in csv_data:
            # Convert None to \N for MySQL NULL
            converted_row = ['\\N' if val is None else str(val) for val in row]
            writer.writerow(converted_row)
        temp_csv.close()
        
        # Bulk load into temp table
        column_list = ', '.join(columns)
        cursor.execute(f"""
            LOAD DATA LOCAL INFILE '{temp_csv.name}'
            INTO TABLE {temp_table_name}
            FIELDS TERMINATED BY ',' 
            OPTIONALLY ENCLOSED BY '"'
            LINES TERMINATED BY '\\n'
            ({column_list})
        """)
        
        return cursor.rowcount
        
    finally:
        # Clean up temp file
        if os.path.exists(temp_csv.name):
            os.unlink(temp_csv.name)


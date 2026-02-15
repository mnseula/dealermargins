"""
Helper functions for CSV bulk loading into MySQL

These functions provide fast bulk loading using temporary tables and LOAD DATA LOCAL INFILE.
"""

import csv
import tempfile
import os
from typing import List, Tuple

def bulk_insert_with_temp_table(cursor, csv_data: List[Tuple],
                                 temp_table_schema: str,
                                 target_table: str,
                                 columns: List[str],
                                 update_clause: str = None):
    """
    Generic CSV bulk loading with temp table approach

    Args:
        cursor: MySQL cursor
        csv_data: List of tuples containing row data
        temp_table_schema: CREATE TEMPORARY TABLE statement
        target_table: Name of final target table
        columns: List of column names for INSERT
        update_clause: ON DUPLICATE KEY UPDATE clause (optional)

    Returns:
        Number of rows loaded
    """
    # Create temp CSV
    temp_csv = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='')

    try:
        # Write CSV
        writer = csv.writer(temp_csv)
        for row in csv_data:
            writer.writerow(row)
        temp_csv.close()

        # Create temp table
        cursor.execute(temp_table_schema)

        # Bulk load into temp table
        column_list = ', '.join(columns)
        cursor.execute(f"""
            LOAD DATA LOCAL INFILE '{temp_csv.name}'
            INTO TABLE temp_{target_table}
            FIELDS TERMINATED BY ','
            LINES TERMINATED BY '\\n'
            ({column_list})
        """)

        # Insert from temp to final table
        if update_clause:
            insert_sql = f"""
                INSERT INTO {target_table} ({column_list})
                SELECT {column_list} FROM temp_{target_table}
                {update_clause}
            """
        else:
            insert_sql = f"""
                INSERT INTO {target_table} ({column_list})
                SELECT {column_list} FROM temp_{target_table}
            """

        cursor.execute(insert_sql)
        rows_loaded = cursor.rowcount

        # Drop temp table
        cursor.execute(f"DROP TEMPORARY TABLE temp_{target_table}")

        return rows_loaded

    finally:
        if os.path.exists(temp_csv.name):
            os.unlink(temp_csv.name)

#!/usr/bin/env python3
"""
Check BoatOptions Table Schemas (15-26)

Verifies that all BoatOptions year tables have consistent schemas
and identifies any missing columns that need to be added.

Usage:
    python3 check_boatoptions_schema.py

Author: Claude Code
Date: 2026-02-09
"""

import mysql.connector
from mysql.connector import Error

# Database configuration
DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'warrantyparts',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD'
}

# Expected columns (31 total) from import script
EXPECTED_COLUMNS = [
    'ERP_OrderNo', 'BoatSerialNo', 'BoatModelNo', 'LineNo', 'ItemNo', 'ItemDesc1',
    'ExtSalesAmount', 'QuantitySold', 'Series', 'WebOrderNo', 'Orig_Ord_Type',
    'ApplyToNo', 'InvoiceNo', 'InvoiceDate', 'ItemMasterProdCat', 'ItemMasterProdCatDesc',
    'ItemMasterMCT', 'MCTDesc', 'LineSeqNo', 'ConfigID', 'ValueText',
    'OptionSerialNo', 'C_Series', 'order_date', 'external_confirmation_ref',
    'MSRP', 'CfgName', 'CfgPage', 'CfgScreen', 'CfgValue', 'CfgAttrType'
]

def get_table_columns(cursor, table_name):
    """Get list of columns for a table"""
    query = """
        SELECT COLUMN_NAME, DATA_TYPE, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'warrantyparts'
          AND TABLE_NAME = %s
        ORDER BY ORDINAL_POSITION
    """
    cursor.execute(query, (table_name,))
    return cursor.fetchall()

def main():
    print("="*80)
    print("BOATOPTIONS SCHEMA CHECKER (2015-2026)")
    print("="*80)
    print()

    try:
        # Connect to database
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("✅ Connected to database")
        print()

        # Check each table from BoatOptions15 to BoatOptions26
        tables_to_check = [f'BoatOptions{i:02d}' for i in range(15, 27)]

        all_schemas = {}
        missing_columns = {}

        for table_name in tables_to_check:
            # Check if table exists
            cursor.execute("""
                SELECT COUNT(*)
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = 'warrantyparts'
                  AND TABLE_NAME = %s
            """, (table_name,))

            exists = cursor.fetchone()[0] > 0

            if not exists:
                print(f"❌ {table_name}: TABLE DOES NOT EXIST")
                all_schemas[table_name] = None
                continue

            # Get columns
            columns = get_table_columns(cursor, table_name)
            column_names = [col[0] for col in columns]
            all_schemas[table_name] = column_names

            # Find missing columns
            missing = [col for col in EXPECTED_COLUMNS if col not in column_names]

            if missing:
                missing_columns[table_name] = missing
                print(f"⚠️  {table_name}: {len(column_names)} columns, MISSING {len(missing)} columns")
                for col in missing:
                    print(f"       - {col}")
            else:
                print(f"✅ {table_name}: {len(column_names)} columns, all expected columns present")

        print()
        print("="*80)
        print("SUMMARY")
        print("="*80)

        if not missing_columns:
            print("✅ All tables have consistent schemas with all required columns!")
        else:
            print(f"⚠️  {len(missing_columns)} table(s) need schema updates:")
            print()

            # Group tables by missing columns
            from collections import defaultdict
            by_missing = defaultdict(list)
            for table, cols in missing_columns.items():
                key = tuple(sorted(cols))
                by_missing[key].append(table)

            for cols, tables in by_missing.items():
                print(f"Tables missing: {', '.join(cols)}")
                print(f"  Affected tables: {', '.join(tables)}")
                print()

            print("="*80)
            print("RECOMMENDED ACTIONS")
            print("="*80)
            print()

            # Generate ALTER TABLE statements
            print("Run these ALTER TABLE statements to add missing columns:")
            print()

            for table, cols in missing_columns.items():
                print(f"-- {table}")
                for col in cols:
                    # Determine column type based on column name
                    if col in ['MSRP', 'ExtSalesAmount']:
                        col_def = f"{col} DECIMAL(10,2) DEFAULT NULL"
                    elif col in ['order_date']:
                        col_def = f"{col} DATE DEFAULT NULL"
                    elif col in ['CfgName', 'CfgValue', 'ValueText']:
                        col_def = f"{col} VARCHAR(100) DEFAULT NULL"
                    elif col in ['CfgPage', 'CfgScreen']:
                        col_def = f"{col} VARCHAR(50) DEFAULT NULL"
                    elif col in ['CfgAttrType']:
                        col_def = f"{col} VARCHAR(20) DEFAULT NULL"
                    elif col in ['external_confirmation_ref', 'ConfigID']:
                        col_def = f"{col} VARCHAR(30) DEFAULT NULL"
                    else:
                        col_def = f"{col} VARCHAR(50) DEFAULT NULL"

                    print(f"ALTER TABLE {table} ADD COLUMN {col_def};")
                print()

        print("="*80)

        cursor.close()
        conn.close()

    except Error as e:
        print(f"❌ Database error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == '__main__':
    exit(main())

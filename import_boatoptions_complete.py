#!/usr/bin/env python3
"""
Complete BoatOptions Import Script - Python Version of C# SqlServerToMySqlImporter

Imports boat builds from MSSQL (CSI/ERP) to MySQL with automatic model year detection.
Includes ALL 21 fields including MCTDesc and ItemMasterMCT from prodcode_mst table.

Features:
- Model year detection from serial number suffix (routes to correct table)
- Two-part UNION query (regular items + configured CPQ items)
- All critical fields for window stickers
- CSV-based bulk import for performance
- Progress reporting and error handling

Usage:
    # Import all recent data (last 90 days)
    python3 import_boatoptions_complete.py

    # Import specific year only
    python3 import_boatoptions_complete.py --year 24
    python3 import_boatoptions_complete.py --year 25
    python3 import_boatoptions_complete.py --year 26

    # Clear table before import
    python3 import_boatoptions_complete.py --year 25 --clear

Author: Converted from C# by Claude Code
Date: 2026-02-03
"""

import sys
import argparse
import csv
import tempfile
import os
from datetime import datetime
from typing import List, Dict, Tuple
import pymssql
import mysql.connector
from mysql.connector import Error as MySQLError

# ============================================================================
# DATABASE CONFIGURATIONS
# ============================================================================

# MSSQL (Source - CSI/ERP)
MSSQL_CONFIG = {
    'server': 'MPL1STGSQL086.POLARISSTAGE.COM',
    'database': 'CSISTG',
    'user': 'svccsimarine',
    'password': 'CNKmoFxEsXs0D9egZQXH',
    'timeout': 300,
    'login_timeout': 60
}

# MySQL (Destination)
MYSQL_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'warrantyparts_test',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD'
}

# ============================================================================
# TABLE MAPPING BY YEAR
# ============================================================================

TABLE_MAP = {
    '24': 'BoatOptions24',
    '25': 'BoatOptions25_test',
    '26': 'BoatOptions26_test'
}

# ============================================================================
# COMPLETE SQL QUERY (From C# Code)
# ============================================================================

# This is the exact query from the C# SqlServerToMySqlImporter
# It includes the critical prodcode_mst join for MCTDesc and ItemMasterMCT
MSSQL_QUERY = """
-- Part 1: Regular order line items (boat, engines, accessories)
SELECT
    LEFT(coi.co_num, 30) AS ERP_OrderNo,
    LEFT(coi.Uf_BENN_BoatSerialNumber, 15) AS BoatSerialNo,
    LEFT(coi.Uf_BENN_BoatModel, 14) AS BoatModelNo,
    coi.co_line AS LineNo,
    LEFT(coi.item, 30) AS ItemNo,
    LEFT(im.description, 50) AS ItemDesc1,
    CAST((coi.price * coi.qty_ordered) AS DECIMAL(10,2)) AS ExtSalesAmount,
    coi.qty_invoiced AS QuantitySold,
    LEFT(im.Uf_BENN_Series, 5) AS Series,
    LEFT(coi.Uf_BENN_BoatWebOrderNumber, 30) AS WebOrderNo,
    LEFT(co.type, 1) AS Orig_Ord_Type,
    ah.apply_to_inv_num AS ApplyToNo,
    LEFT(iim.inv_num, 30) AS InvoiceNo,
    CASE
        WHEN ah.inv_date IS NOT NULL
        THEN CONVERT(INT, CONVERT(VARCHAR(8), ah.inv_date, 112))
        ELSE NULL
    END AS InvoiceDate,
    LEFT(im.Uf_BENN_ProductCategory, 3) AS ItemMasterProdCat,
    LEFT(pcm.description, 100) AS ItemMasterProdCatDesc,
    LEFT(im.Uf_BENN_MaterialCostType, 10) AS ItemMasterMCT,
    LEFT(pcm.description, 50) AS MCTDesc,
    coi.co_line AS LineSeqNo,
    '' AS ConfigID,
    '' AS ValueText
FROM [CSISTG].[dbo].[coitem_mst] coi
LEFT JOIN [CSISTG].[dbo].[inv_item_mst] iim
    ON coi.co_num = iim.co_num
    AND coi.co_line = iim.co_line
    AND coi.co_release = iim.co_release
    AND coi.site_ref = iim.site_ref
LEFT JOIN [CSISTG].[dbo].[arinv_mst] ah
    ON iim.inv_num = ah.inv_num
    AND iim.site_ref = ah.site_ref
LEFT JOIN [CSISTG].[dbo].[co_mst] co
    ON coi.co_num = co.co_num
    AND coi.site_ref = co.site_ref
LEFT JOIN [CSISTG].[dbo].[item_mst] im
    ON coi.item = im.item
    AND coi.site_ref = im.site_ref
LEFT JOIN [CSISTG].[dbo].[prodcode_mst] pcm
    ON im.Uf_BENN_MaterialCostType = pcm.product_code
    AND im.site_ref = pcm.site_ref
WHERE coi.site_ref = 'BENN'
    AND coi.Uf_BENN_BoatSerialNumber IS NOT NULL
    AND coi.Uf_BENN_BoatSerialNumber != ''
    AND coi.RecordDate >= DATEADD(day, -90, GETDATE())

UNION ALL

-- Part 2: Component attributes for configured items (CPQ boats)
SELECT
    LEFT(coi.co_num, 30) AS ERP_OrderNo,
    LEFT(coi.Uf_BENN_BoatSerialNumber, 15) AS BoatSerialNo,
    LEFT(coi.Uf_BENN_BoatModel, 14) AS BoatModelNo,
    coi.co_line AS LineNo,
    '' AS ItemNo,
    LEFT(att.Uf_BENN_AttributeValue, 50) AS ItemDesc1,
    CAST(0 AS DECIMAL(10,2)) AS ExtSalesAmount,
    0 AS QuantitySold,
    LEFT(im.Uf_BENN_Series, 5) AS Series,
    LEFT(coi.Uf_BENN_BoatWebOrderNumber, 30) AS WebOrderNo,
    LEFT(co.type, 1) AS Orig_Ord_Type,
    ah.apply_to_inv_num AS ApplyToNo,
    LEFT(iim.inv_num, 30) AS InvoiceNo,
    CASE
        WHEN ah.inv_date IS NOT NULL
        THEN CONVERT(INT, CONVERT(VARCHAR(8), ah.inv_date, 112))
        ELSE NULL
    END AS InvoiceDate,
    'ACY' AS ItemMasterProdCat,
    'ACCESSORIES' AS ItemMasterProdCatDesc,
    'ACY' AS ItemMasterMCT,
    'ACCESSORIES' AS MCTDesc,
    (coi.co_line * 1000 + att.Uf_BENN_SequenceNo) AS LineSeqNo,
    LEFT(coi.config_id, 30) AS ConfigID,
    LEFT(att.Uf_BENN_AttributeValue, 100) AS ValueText
FROM [CSISTG].[dbo].[coitem_mst] coi
LEFT JOIN [CSISTG].[dbo].[inv_item_mst] iim
    ON coi.co_num = iim.co_num
    AND coi.co_line = iim.co_line
    AND coi.co_release = iim.co_release
    AND coi.site_ref = iim.site_ref
LEFT JOIN [CSISTG].[dbo].[arinv_mst] ah
    ON iim.inv_num = ah.inv_num
    AND iim.site_ref = ah.site_ref
LEFT JOIN [CSISTG].[dbo].[co_mst] co
    ON coi.co_num = co.co_num
    AND coi.site_ref = co.site_ref
LEFT JOIN [CSISTG].[dbo].[item_mst] im
    ON coi.item = im.item
    AND coi.site_ref = im.site_ref
LEFT JOIN [CSISTG].[dbo].[Uf_BENN_ComponentAttributesJL] att
    ON coi.co_num = att.RefRowPointer
    AND coi.site_ref = att.site_ref
WHERE coi.site_ref = 'BENN'
    AND coi.config_id IS NOT NULL
    AND coi.Uf_BENN_BoatSerialNumber IS NOT NULL
    AND coi.Uf_BENN_BoatSerialNumber != ''
    AND att.Uf_BENN_AttributeValue IS NOT NULL
    AND coi.RecordDate >= DATEADD(day, -90, GETDATE())

ORDER BY ERP_OrderNo, LineSeqNo
"""

# ============================================================================
# FUNCTIONS
# ============================================================================

def log(message: str, level: str = "INFO"):
    """Print timestamped log message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    symbols = {
        "INFO": "ℹ️",
        "SUCCESS": "✅",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "PROGRESS": "⏳"
    }
    symbol = symbols.get(level, "•")
    print(f"[{timestamp}] {symbol} {message}")

def detect_model_year(serial_number: str) -> str:
    """
    Detect model year from serial number suffix.

    Serial format: ETWC4149F425 (ends with year suffix)
    Examples: ...F425 = 2025, ...H324 = 2024, ...J426 = 2026

    Returns: '24', '25', or '26'
    """
    if not serial_number or len(serial_number) < 3:
        return '25'  # Default to 2025

    # Get last 3 characters
    suffix = serial_number[-3:]

    # Extract year digits (last 2 chars)
    try:
        year_digits = suffix[-2:]
        if year_digits in ['24', '25', '26']:
            return year_digits
    except:
        pass

    # Default to 2025
    return '25'

def get_target_table(year: str) -> str:
    """Get MySQL table name for given year"""
    return TABLE_MAP.get(year, 'BoatOptions25_test')

def extract_from_mssql() -> List[Tuple]:
    """Extract boat option line items from MSSQL database"""
    log("Connecting to MSSQL (CSI/ERP database)...")

    try:
        conn = pymssql.connect(**MSSQL_CONFIG)
        cursor = conn.cursor()

        log("Extracting data with complete field set (21 fields including MCTDesc)...")
        log("This includes both regular items and configured CPQ items...")

        cursor.execute(MSSQL_QUERY)
        rows = cursor.fetchall()

        log(f"Extracted {len(rows):,} rows from MSSQL", "SUCCESS")

        cursor.close()
        conn.close()

        return rows

    except pymssql.Error as e:
        log(f"MSSQL error: {e}", "ERROR")
        raise
    except Exception as e:
        log(f"Unexpected error: {e}", "ERROR")
        raise

def group_by_year(rows: List[Tuple]) -> Dict[str, List[Tuple]]:
    """Group rows by model year detected from serial number"""
    log("Grouping rows by model year...")

    groups = {
        '24': [],
        '25': [],
        '26': []
    }

    for row in rows:
        serial_no = row[1]  # BoatSerialNo is column 2
        year = detect_model_year(serial_no)
        groups[year].append(row)

    log(f"Year 2024: {len(groups['24']):,} rows")
    log(f"Year 2025: {len(groups['25']):,} rows")
    log(f"Year 2026: {len(groups['26']):,} rows")

    return groups

def clear_table(mysql_conn, table_name: str):
    """Clear the target BoatOptions table"""
    cursor = mysql_conn.cursor()
    try:
        log(f"Clearing {table_name} table...", "WARNING")
        cursor.execute(f"DELETE FROM {table_name}")
        deleted = cursor.rowcount
        mysql_conn.commit()
        log(f"Deleted {deleted:,} existing rows", "SUCCESS")
    except MySQLError as e:
        log(f"Error clearing table: {e}", "ERROR")
        raise
    finally:
        cursor.close()

def load_to_mysql_via_csv(rows: List[Tuple], table_name: str, clear: bool = False):
    """Load data to MySQL using CSV bulk import"""

    if len(rows) == 0:
        log(f"No rows to import for {table_name}", "WARNING")
        return

    log(f"Loading {len(rows):,} rows to {table_name}...")

    try:
        # Create temporary CSV file
        temp_csv = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='')
        csv_path = temp_csv.name

        log(f"Writing data to temporary CSV: {csv_path}", "PROGRESS")

        # Write CSV
        csv_writer = csv.writer(temp_csv)
        for row in rows:
            csv_writer.writerow(row)
        temp_csv.close()

        log(f"CSV file created with {len(rows):,} rows", "SUCCESS")

        # Connect to MySQL
        log("Connecting to MySQL...", "PROGRESS")
        conn = mysql.connector.connect(**MYSQL_CONFIG)

        # Clear table if requested
        if clear:
            clear_table(conn, table_name)

        cursor = conn.cursor()

        # Load CSV into MySQL using LOAD DATA LOCAL INFILE
        log("Importing CSV to MySQL...", "PROGRESS")

        load_query = f"""
        LOAD DATA LOCAL INFILE '{csv_path}'
        INTO TABLE {table_name}
        FIELDS TERMINATED BY ','
        OPTIONALLY ENCLOSED BY '"'
        LINES TERMINATED BY '\\n'
        (ERP_OrderNo, BoatSerialNo, BoatModelNo, LineNo, ItemNo, ItemDesc1,
         ExtSalesAmount, QuantitySold, Series, WebOrderNo, Orig_Ord_Type,
         ApplyToNo, InvoiceNo, InvoiceDate, ItemMasterProdCat, ItemMasterProdCatDesc,
         ItemMasterMCT, MCTDesc, LineSeqNo, ConfigID, ValueText)
        """

        cursor.execute(load_query)
        conn.commit()

        imported = cursor.rowcount
        log(f"Successfully imported {imported:,} rows to {table_name}", "SUCCESS")

        cursor.close()
        conn.close()

        # Clean up CSV file
        os.unlink(csv_path)

        return imported

    except MySQLError as e:
        log(f"MySQL error: {e}", "ERROR")
        if 'conn' in locals():
            conn.rollback()
        raise
    except Exception as e:
        log(f"Unexpected error: {e}", "ERROR")
        raise
    finally:
        # Make sure temp file is cleaned up
        if 'csv_path' in locals() and os.path.exists(csv_path):
            os.unlink(csv_path)

def load_to_mysql_batch(rows: List[Tuple], table_name: str, clear: bool = False):
    """Load data to MySQL using batch inserts (fallback if CSV fails)"""

    if len(rows) == 0:
        log(f"No rows to import for {table_name}", "WARNING")
        return

    log(f"Loading {len(rows):,} rows to {table_name} using batch inserts...")

    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)

        # Clear table if requested
        if clear:
            clear_table(conn, table_name)

        cursor = conn.cursor()

        insert_query = f"""
        INSERT INTO {table_name} (
            ERP_OrderNo, BoatSerialNo, BoatModelNo, LineNo, ItemNo, ItemDesc1,
            ExtSalesAmount, QuantitySold, Series, WebOrderNo, Orig_Ord_Type,
            ApplyToNo, InvoiceNo, InvoiceDate, ItemMasterProdCat, ItemMasterProdCatDesc,
            ItemMasterMCT, MCTDesc, LineSeqNo, ConfigID, ValueText
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """

        batch_size = 1000
        inserted = 0

        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            cursor.executemany(insert_query, batch)
            conn.commit()
            inserted += len(batch)

            if inserted % 5000 == 0:
                log(f"Progress: {inserted:,} / {len(rows):,} rows...", "PROGRESS")

        log(f"Successfully inserted {inserted:,} rows to {table_name}", "SUCCESS")

        cursor.close()
        conn.close()

        return inserted

    except MySQLError as e:
        log(f"MySQL error: {e}", "ERROR")
        if 'conn' in locals():
            conn.rollback()
        raise
    except Exception as e:
        log(f"Unexpected error: {e}", "ERROR")
        raise

def print_summary(year_groups: Dict[str, List[Tuple]]):
    """Print summary statistics"""
    print("\n" + "="*70)
    print("IMPORT SUMMARY")
    print("="*70)

    total = sum(len(rows) for rows in year_groups.values())
    print(f"\nTotal rows imported: {total:,}")
    print(f"\nBreakdown by year:")

    for year in ['24', '25', '26']:
        count = len(year_groups[year])
        table = TABLE_MAP[year]
        if count > 0:
            print(f"  20{year}: {count:,} rows → {table}")
        else:
            print(f"  20{year}: {count:,} rows (skipped)")

    print("\n" + "="*70)

def main():
    parser = argparse.ArgumentParser(
        description='Import boat options from MSSQL to BoatOptions tables',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Import all recent data (last 90 days) to all tables
  python3 import_boatoptions_complete.py

  # Import specific year only
  python3 import_boatoptions_complete.py --year 25

  # Clear table before import
  python3 import_boatoptions_complete.py --year 25 --clear
        """
    )

    parser.add_argument('--year', choices=['24', '25', '26'],
                       help='Import specific year only (default: all years)')
    parser.add_argument('--clear', action='store_true',
                       help='Clear existing data before import')
    parser.add_argument('--batch', action='store_true',
                       help='Use batch inserts instead of CSV (slower but more compatible)')

    args = parser.parse_args()

    print("="*70)
    print("BOATOPTIONS COMPLETE IMPORT SCRIPT")
    print("="*70)
    print(f"Mode: Import {'year 20' + args.year if args.year else 'all years'}")
    print(f"Clear existing: {'Yes' if args.clear else 'No'}")
    print(f"Import method: {'Batch inserts' if args.batch else 'CSV bulk load'}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    print()

    try:
        # Step 1: Extract from MSSQL
        rows = extract_from_mssql()

        if len(rows) == 0:
            log("No data extracted from MSSQL!", "ERROR")
            sys.exit(1)

        # Step 2: Group by year
        year_groups = group_by_year(rows)

        # Step 3: Load to MySQL tables
        years_to_import = [args.year] if args.year else ['24', '25', '26']

        for year in years_to_import:
            year_rows = year_groups[year]

            if len(year_rows) == 0:
                log(f"No data for year 20{year}, skipping...", "WARNING")
                continue

            table_name = get_target_table(year)

            if args.batch:
                load_to_mysql_batch(year_rows, table_name, clear=args.clear)
            else:
                try:
                    load_to_mysql_via_csv(year_rows, table_name, clear=args.clear)
                except Exception as e:
                    log(f"CSV import failed, falling back to batch inserts: {e}", "WARNING")
                    load_to_mysql_batch(year_rows, table_name, clear=args.clear)

        # Step 4: Print summary
        print_summary(year_groups)

        log("Import completed successfully!", "SUCCESS")

    except KeyboardInterrupt:
        log("Import cancelled by user", "WARNING")
        sys.exit(1)
    except Exception as e:
        log(f"Import failed: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

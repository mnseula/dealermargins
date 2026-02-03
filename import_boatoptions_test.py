#!/usr/bin/env python3
"""
BoatOptions Import Script - TEST VERSION

Imports INVOICED boat orders from 12/14/2025 onwards to TEST database.
This is for validating the scraping logic before running on production.

Features:
- Only invoiced orders (has invoice number and qty_invoiced > 0)
- Only orders from 2025-12-14 onwards (CPQ go-live date)
- CPQ order detection (routes to BoatOptions26_test)
- Non-CPQ order detection (routes by serial number year)
- Complete field set including MCTDesc from prodcode_mst
- CFG table scraping for configured CPQ items

Usage:
    python3 import_boatoptions_test.py

Author: Claude Code
Date: 2026-02-03
"""

import sys
import csv
import tempfile
import os
from datetime import datetime, date
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

# MySQL (Destination - TEST DATABASE)
MYSQL_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'warrantyparts_boatoptions_test',  # TEST DATABASE
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD'
}

# CPQ Go-Live Date
CPQ_GO_LIVE_DATE = date(2024, 12, 14)

# ============================================================================
# TABLE MAPPING BY YEAR
# ============================================================================

TABLE_MAP = {
    '24': 'BoatOptions24',
    '25': 'BoatOptions25_test',
    '26': 'BoatOptions26_test'
}

# ============================================================================
# COMPLETE SQL QUERY - INVOICED ORDERS ONLY, FROM 12/14/2025 ONWARDS
# ============================================================================

MSSQL_QUERY = """
-- Part 1: Main order lines (e.g., boat itself, engine, accessories)
SELECT
    LEFT(coi.Uf_BENN_BoatWebOrderNumber, 30) AS [WebOrderNo],
    LEFT(im.Uf_BENN_Series, 5) AS [C_Series],
    coi.qty_invoiced AS [QuantitySold],
    LEFT(co.type, 1) AS [Orig_Ord_Type],
    LEFT(ser.ser_num, 12) AS [OptionSerialNo],
    pcm.description AS [MCTDesc],
    coi.co_line AS [LineSeqNo],
    coi.co_line AS [LineNo],
    LEFT(coi.item, 15) AS [ItemNo],
    NULL AS [ItemMasterProdCatDesc],
    LEFT(im.Uf_BENN_ProductCategory, 3) AS [ItemMasterProdCat],
    LEFT(im.Uf_BENN_MaterialCostType, 10) AS [ItemMasterMCT],
    LEFT(coi.description, 30) AS [ItemDesc1],
    LEFT(iim.inv_num, 30) AS [InvoiceNo],
    CASE
        WHEN ah.inv_date IS NOT NULL
        THEN CONVERT(INT, CONVERT(VARCHAR(8), ah.inv_date, 112))
        ELSE NULL
    END AS [InvoiceDate],
    CAST((coi.price * coi.qty_invoiced) AS DECIMAL(10,2)) AS [ExtSalesAmount],
    LEFT(coi.co_num, 30) AS [ERP_OrderNo],
    LEFT(coi.Uf_BENN_BoatSerialNumber, 15) AS [BoatSerialNo],
    LEFT(coi.Uf_BENN_BoatModel, 14) AS [BoatModelNo],
    ah.apply_to_inv_num AS [ApplyToNo],
    '' AS [ConfigID],
    '' AS [ValueText],
    co.order_date AS [order_date],
    co.external_confirmation_ref AS [external_confirmation_ref]
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
LEFT JOIN [CSISTG].[dbo].[serial_mst] ser
    ON coi.co_num = ser.ref_num
    AND coi.co_line = ser.ref_line
    AND coi.co_release = ser.ref_release
    AND coi.item = ser.item
    AND coi.site_ref = ser.site_ref
    AND ser.ref_type = 'O'
WHERE coi.site_ref = 'BENN'
    AND coi.Uf_BENN_BoatSerialNumber IS NOT NULL
    AND coi.Uf_BENN_BoatSerialNumber != ''
    AND iim.inv_num IS NOT NULL
    AND coi.qty_invoiced > 0
    AND co.order_date >= '2024-12-14'

UNION ALL

-- Part 2: Component "Description" attributes for invoiced, configured items (CPQ boats)
SELECT
    LEFT(coi.Uf_BENN_BoatWebOrderNumber, 30) AS [WebOrderNo],
    LEFT(im.Uf_BENN_Series, 5) AS [C_Series],
    coi.qty_invoiced AS [QuantitySold],
    LEFT(co.type, 1) AS [Orig_Ord_Type],
    LEFT(ser.ser_num, 12) AS [BoatModelNo],
    pcm.description AS [MCTDesc],
    coi.co_line AS [LineSeqNo],
    coi.co_line AS [LineNo],
    LEFT(ISNULL(ccm.comp_name, attr_detail.comp_id), 15) AS [ItemNo],
    NULL AS [ItemMasterProdCatDesc],
    LEFT(im.Uf_BENN_ProductCategory, 3) AS [ItemMasterProdCat],
    LEFT(im.Uf_BENN_MaterialCostType, 10) AS [ItemMasterMCT],
    LEFT(attr_detail.attr_value, 30) AS [ItemDesc1],
    LEFT(iim.inv_num, 30) AS [InvoiceNo],
    CASE
        WHEN ah.inv_date IS NOT NULL
        THEN CONVERT(INT, CONVERT(VARCHAR(8), ah.inv_date, 112))
        ELSE NULL
    END AS [InvoiceDate],
    CAST((coi.price * coi.qty_invoiced) AS DECIMAL(10,2)) AS [ExtSalesAmount],
    LEFT(coi.co_num, 30) AS [ERP_OrderNo],
    LEFT(coi.Uf_BENN_BoatSerialNumber, 15) AS [BoatSerialNo],
    LEFT(coi.Uf_BENN_BoatModel, 14) AS [OptionSerialNo],
    ah.apply_to_inv_num AS [ApplyToNo],
    LEFT(coi.config_id, 30) AS [ConfigID],
    LEFT(attr_detail.attr_value, 100) AS [ValueText],
    co.order_date AS [order_date],
    co.external_confirmation_ref AS [external_confirmation_ref]
FROM [CSISTG].[dbo].[coitem_mst] coi
INNER JOIN [CSISTG].[dbo].[cfg_attr_mst] attr_detail
    ON coi.config_id = attr_detail.config_id
    AND coi.site_ref = attr_detail.site_ref
    AND attr_detail.attr_name = 'Description'
    AND attr_detail.sl_field = 'jobmatl.description'
    AND attr_detail.attr_type = 'Schema'
    AND attr_detail.attr_value IS NOT NULL
LEFT JOIN [CSISTG].[dbo].[cfg_comp_mst] ccm
    ON attr_detail.config_id = ccm.config_id
    AND attr_detail.comp_id = ccm.comp_id
    AND attr_detail.site_ref = ccm.site_ref
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
LEFT JOIN [CSISTG].[dbo].[serial_mst] ser
    ON coi.co_num = ser.ref_num
    AND coi.co_line = ser.ref_line
    AND coi.co_release = ser.ref_release
    AND coi.item = ser.item
    AND coi.site_ref = ser.site_ref
    AND ser.ref_type = 'O'
WHERE coi.config_id IS NOT NULL
    AND coi.qty_invoiced = coi.qty_ordered
    AND coi.qty_invoiced > 0
    AND ser.site_ref = 'BENN'
    AND co.order_date >= '2024-12-14'

ORDER BY [ERP_OrderNo], [LineSeqNo]
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

def is_cpq_order(order_date, external_confirmation_ref, co_num):
    """
    Detect if order is a CPQ/EQ order.
    CPQ orders always go to BoatOptions26_test.

    Criteria:
    - order_date >= 2024-12-14 (CPQ Go Live)
    - co_num starts with 'SO'
    - external_confirmation_ref starts with 'SO'
    """
    if not order_date or not external_confirmation_ref or not co_num:
        return False

    # Handle both datetime and date objects
    if isinstance(order_date, datetime):
        order_date = order_date.date()

    return (
        order_date >= CPQ_GO_LIVE_DATE and
        str(co_num).startswith('SO') and
        str(external_confirmation_ref).startswith('SO')
    )

def detect_model_year_from_serial(serial_number: str) -> str:
    """
    Detect model year from serial number suffix.

    Serial format: ETWC4149F425 (ends with year suffix)
    Examples: ...F425 = 2025, ...H324 = 2024, ...J426 = 2026

    Returns: '24', '25', or '26'
    """
    if not serial_number or len(serial_number) < 3:
        return '25'  # Default to 2025

    # Get last 2 characters (year digits)
    try:
        year_digits = serial_number[-2:]
        if year_digits in ['24', '25', '26']:
            return year_digits
    except:
        pass

    # Default to 2025
    return '25'

def get_target_year(row: Dict) -> str:
    """
    Determine which BoatOptions table this row should go to.

    Logic:
    1. If CPQ order → Always '26' (BoatOptions26_test)
    2. Otherwise → Detect from serial number suffix
    """
    order_date = row.get('order_date')
    external_confirmation_ref = row.get('external_confirmation_ref')
    co_num = row.get('ERP_OrderNo')
    serial_no = row.get('BoatSerialNo')

    # Check if CPQ order first
    if is_cpq_order(order_date, external_confirmation_ref, co_num):
        return '26'  # All CPQ orders → BoatOptions26_test

    # Non-CPQ order - detect year from serial number suffix
    return detect_model_year_from_serial(serial_no)

def extract_from_mssql() -> List[Dict]:
    """Extract invoiced boat orders from MSSQL database (from 12/14/2025 onwards)"""
    log("Connecting to MSSQL (CSI/ERP database)...")

    try:
        conn = pymssql.connect(**MSSQL_CONFIG)
        cursor = conn.cursor(as_dict=True)
        log("✅ Connected to MSSQL", "SUCCESS")

        log("Extracting INVOICED orders from 12/14/2024 onwards...")
        log("This includes both regular items and CPQ configured items...")

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

def group_by_year(rows: List[Dict]) -> Dict[str, List[Dict]]:
    """Group rows by target year (CPQ orders → 26, others by serial)"""
    log("Grouping rows by target year...")

    groups = {
        '24': [],
        '25': [],
        '26': []
    }

    cpq_count = 0
    non_cpq_count = 0

    for row in rows:
        year = get_target_year(row)
        groups[year].append(row)

        # Track CPQ vs non-CPQ
        if is_cpq_order(row.get('order_date'), row.get('external_confirmation_ref'), row.get('ERP_OrderNo')):
            cpq_count += 1
        else:
            non_cpq_count += 1

    log(f"Year 2024: {len(groups['24']):,} rows")
    log(f"Year 2025: {len(groups['25']):,} rows")
    log(f"Year 2026: {len(groups['26']):,} rows (CPQ orders)")
    log(f"\nCPQ orders: {cpq_count:,}")
    log(f"Non-CPQ orders: {non_cpq_count:,}")

    return groups

def load_to_mysql_batch(rows: List[Dict], table_name: str):
    """Load data to MySQL using batch inserts"""

    if len(rows) == 0:
        log(f"No rows to import for {table_name}", "WARNING")
        return 0

    log(f"Loading {len(rows):,} rows to {table_name}...")

    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()

        # Prepare insert query with all 23 fields
        insert_query = f"""
        INSERT INTO {table_name} (
            ERP_OrderNo, BoatSerialNo, BoatModelNo, LineNo, ItemNo, ItemDesc1,
            ExtSalesAmount, QuantitySold, Series, WebOrderNo, Orig_Ord_Type,
            ApplyToNo, InvoiceNo, InvoiceDate, ItemMasterProdCat, ItemMasterProdCatDesc,
            ItemMasterMCT, MCTDesc, LineSeqNo, ConfigID, ValueText,
            OptionSerialNo, C_Series
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s
        )
        """

        batch_size = 1000
        inserted = 0

        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]

            # Prepare batch data (map dict fields to tuple)
            batch_data = []
            for row in batch:
                row_tuple = (
                    row.get('ERP_OrderNo'),
                    row.get('BoatSerialNo'),
                    row.get('BoatModelNo'),
                    row.get('LineNo'),
                    row.get('ItemNo'),
                    row.get('ItemDesc1'),
                    row.get('ExtSalesAmount'),
                    row.get('QuantitySold'),
                    row.get('Series') or row.get('C_Series'),  # Use C_Series if Series is None
                    row.get('WebOrderNo'),
                    row.get('Orig_Ord_Type'),
                    row.get('ApplyToNo'),
                    row.get('InvoiceNo'),
                    row.get('InvoiceDate'),
                    row.get('ItemMasterProdCat'),
                    row.get('ItemMasterProdCatDesc'),
                    row.get('ItemMasterMCT'),
                    row.get('MCTDesc'),
                    row.get('LineSeqNo'),
                    row.get('ConfigID'),
                    row.get('ValueText'),
                    row.get('OptionSerialNo'),
                    row.get('C_Series')
                )
                batch_data.append(row_tuple)

            cursor.executemany(insert_query, batch_data)
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

def print_summary(year_groups: Dict[str, List[Dict]], results: Dict[str, int]):
    """Print summary statistics"""
    print("\n" + "="*80)
    print("IMPORT SUMMARY - TEST DATABASE")
    print("="*80)

    total_extracted = sum(len(rows) for rows in year_groups.values())
    total_imported = sum(results.values())

    print(f"\nExtracted: {total_extracted:,} rows from MSSQL")
    print(f"Imported:  {total_imported:,} rows to MySQL")

    print(f"\nBreakdown by table:")
    for year in ['24', '25', '26']:
        count = results.get(year, 0)
        table = TABLE_MAP[year]
        if count > 0:
            print(f"  {table:25s}: {count:8,d} rows")

    print("\n" + "="*80)
    print("✅ TEST IMPORT COMPLETE")
    print("="*80)
    print("\nNext Steps:")
    print("1. Verify data in warrantyparts_boatoptions_test database")
    print("2. Check CPQ orders are in BoatOptions26_test")
    print("3. Run test queries to validate data integrity")
    print("4. If successful, run import to PRODUCTION database")
    print("="*80)

def main():
    print("="*80)
    print("BOATOPTIONS IMPORT - TEST VERSION")
    print("="*80)
    print(f"Target: warrantyparts_boatoptions_test (TEST DATABASE)")
    print(f"Filter: Invoiced orders from 12/14/2024 onwards")
    print(f"CPQ Detection: ON (routes to BoatOptions26_test)")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print()

    try:
        # Step 1: Extract from MSSQL
        rows = extract_from_mssql()

        if len(rows) == 0:
            log("No data extracted from MSSQL!", "ERROR")
            log("This could mean no orders have been invoiced since 12/14/2024", "WARNING")
            sys.exit(1)

        # Step 2: Group by year
        year_groups = group_by_year(rows)

        # Step 3: Load to MySQL tables
        results = {}
        for year in ['24', '25', '26']:
            year_rows = year_groups[year]

            if len(year_rows) == 0:
                log(f"No data for year 20{year}, skipping...", "WARNING")
                results[year] = 0
                continue

            table_name = TABLE_MAP[year]
            imported = load_to_mysql_batch(year_rows, table_name)
            results[year] = imported

        # Step 4: Print summary
        print_summary(year_groups, results)

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

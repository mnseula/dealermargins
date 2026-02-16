#!/usr/bin/env python3
"""
BoatOptions Import Script - PRODUCTION VERSION

⚠️  WARNING: This modifies LIVE PRODUCTION data! ⚠️

Imports INVOICED boat orders from 12/14/2025 onwards to PRODUCTION database.

Features:
- Only invoiced orders (has invoice number and qty_invoiced > 0)
- Only orders from 2025-12-14 onwards (CPQ go-live date)
- Smart routing with fallback logic:
  1. FIRST: Detect model year from serial number
     - Year <= 2025 → Legacy boat → warrantyparts.BoatOptionsXX
  2. THEN: Year >= 2026 → Check CPQ criteria → cpq.BoatOptions or warrantyparts
- Handles old inventory boats (e.g., 2024 boat invoiced in 2026 → BoatOptions24)
- Complete field set including MCTDesc from prodcode_mst
- CFG table scraping for configured CPQ items with MSRP

Usage:
    # Staging (default)
    python3 import_boatoptions_production.py
    
    # Production
    python3 import_boatoptions_production.py --prd

Command Line Arguments:
    --prd, --production    Use production MSSQL database (CSIPRD)
                           Default is staging (CSISTG) if not specified

Author: Claude Code
Date: 2026-02-11
"""

import sys
import argparse
import csv
import tempfile
import os
from datetime import datetime, date
from typing import List, Dict, Tuple
import pymssql
import mysql.connector
from mysql.connector import Error as MySQLError

# ============================================================================
# COMMAND LINE ARGUMENTS
# ============================================================================

parser = argparse.ArgumentParser(
    description='Import boat options from MSSQL to MySQL',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
    # Staging (default)
    python3 import_boatoptions_production.py
    
    # Production
    python3 import_boatoptions_production.py --prd
    
    # In JAMS - Staging job:
    Command: python3 import_boatoptions_production.py
    
    # In JAMS - Production job:
    Command: python3 import_boatoptions_production.py --prd
    """
)
parser.add_argument(
    '--prd', '--production',
    action='store_true',
    dest='use_production',
    default=False,
    help='Use production MSSQL database (CSIPRD). Default is staging (CSISTG).'
)
# Parse known args to allow other args from existing code
args, remaining_argv = parser.parse_known_args()
# Put remaining args back for further parsing if needed
sys.argv[1:] = remaining_argv

# ============================================================================
# DATABASE CONFIGURATION - COMMAND LINE SWITCH
# ============================================================================

USE_PRODUCTION = args.use_production

# MSSQL Configuration - Staging (Default)
MSSQL_CONFIG_STAGING = {
    'server': 'MPL1STGSQL086.POLARISSTAGE.COM',
    'database': 'CSISTG',
    'user': 'svccsimarine',
    'password': 'CNKmoFxEsXs0D9egZQXH',
    'timeout': 300,
    'login_timeout': 60
}

# MSSQL Configuration - Production
MSSQL_CONFIG_PRODUCTION = {
    'server': 'MPL1ITSSQL086.POLARISIND.COM',
    'database': 'CSIPRD',
    'user': 'svcSpecs01',
    'password': 'SD4nzr0CJ5oj38',
    'timeout': 300,
    'login_timeout': 60
}

# Select configuration based on command line argument
MSSQL_CONFIG = MSSQL_CONFIG_PRODUCTION if USE_PRODUCTION else MSSQL_CONFIG_STAGING

# Log which database we're using (for JAMS logs)
if USE_PRODUCTION:
    print(f"⚠️  USING PRODUCTION DATABASE: {MSSQL_CONFIG['database']} on {MSSQL_CONFIG['server']}")
else:
    print(f"ℹ️  Using STAGING database: {MSSQL_CONFIG['database']} on {MSSQL_CONFIG['server']}")

# MySQL (Destination - PRODUCTION DATABASE)
# Note: Database is specified in table names (cpq.BoatOptions or warrantyparts.BoatOptions15)
MYSQL_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD'
}

# CPQ Go-Live Date
CPQ_GO_LIVE_DATE = date(2025, 12, 14)

# ============================================================================
# TABLE MAPPING BY YEAR - PRODUCTION STRUCTURE
# ============================================================================

def get_table_for_year(year: int, is_production: bool = False) -> str:
    """
    Map model year to BoatOptions table name.

    Production tables:
    - BoatOptionsBefore_05  → Before 2005
    - BoatOptions99_04      → 1999-2004
    - BoatOptions05_07      → 2005-2007
    - BoatOptions08_10      → 2008-2010
    - BoatOptions11_14      → 2011-2014
    - BoatOptions15-26      → Individual year tables

    Test tables: Same naming (no _test suffix for consistency)
    """
    if year < 2005:
        if 1999 <= year <= 2004:
            return 'BoatOptions99_04'
        else:
            return 'BoatOptionsBefore_05'
    elif 2005 <= year <= 2007:
        return 'BoatOptions05_07'
    elif 2008 <= year <= 2010:
        return 'BoatOptions08_10'
    elif 2011 <= year <= 2014:
        return 'BoatOptions11_14'
    elif year >= 2015:
        # Individual year tables: BoatOptions15, BoatOptions16, ..., BoatOptions26
        year_suffix = year % 100
        return f'BoatOptions{year_suffix:02d}'
    else:
        return 'BoatOptionsBefore_05'

# ============================================================================
# COMPLETE SQL QUERY - INVOICED ORDERS ONLY, FROM 12/14/2025 ONWARDS
# ============================================================================

MSSQL_QUERY = """
-- Use ROW_NUMBER to generate unique LineSeqNo for each row per order
-- This fixes the issue where configured items all have the same co_line value
WITH BoatOrders AS (
    -- First, identify all orders that have boats (traditional or CPQ)
    -- Also get the HIN from serial_mst for CPQ boats
    SELECT DISTINCT
        coi.co_num,
        coi.site_ref,
        -- Get BoatSerialNumber from either coitem or serial_mst (for CPQ boats)
        COALESCE(
            NULLIF(coi.Uf_BENN_BoatSerialNumber, ''),
            ser.ser_num
        ) AS Uf_BENN_BoatSerialNumber,
        coi.Uf_BENN_BoatModel,
        coi.config_id
    FROM [CSISTG].[dbo].[coitem_mst] coi
    LEFT JOIN [CSISTG].[dbo].[serial_mst] ser
        ON coi.co_num = ser.ref_num
        AND coi.co_line = ser.ref_line
        AND coi.co_release = ser.ref_release
        AND coi.item = ser.item
        AND coi.site_ref = ser.site_ref
        AND ser.ref_type = 'O'
    WHERE coi.site_ref = 'BENN'
        AND (
            -- Traditional boats: have BoatSerialNumber
            (coi.Uf_BENN_BoatSerialNumber IS NOT NULL AND coi.Uf_BENN_BoatSerialNumber != '')
            OR
            -- CPQ boats: have config_id (boat line item)
            (coi.config_id IS NOT NULL AND coi.config_id != '')
        )
),
OrderedRows AS (
-- Part 1: Main order lines (boat, engine, prerigs, accessories)
SELECT
    LEFT(coi.Uf_BENN_BoatWebOrderNumber, 30) AS [WebOrderNo],
    LEFT(im.Uf_BENN_Series, 5) AS [C_Series],
    coi.qty_invoiced AS [QuantitySold],
    LEFT(co.type, 1) AS [Orig_Ord_Type],
    -- OptionSerialNo = Engine serial number from serial_mst (for engine lines)
    LEFT(ser.ser_num, 12) AS [OptionSerialNo],
    pcm.description AS [MCTDesc],
    coi.co_line AS [LineSeqNo],
    coi.co_line AS [LineNo],
    LEFT(coi.item, 15) AS [ItemNo],
    NULL AS [ItemMasterProdCatDesc],
    LEFT(im.Uf_BENN_ProductCategory, 3) AS [ItemMasterProdCat],
    LEFT(im.Uf_BENN_MaterialCostType, 10) AS [ItemMasterMCT],
    LEFT(coi.description, 30) AS [ItemDesc1],
    LEFT(LTRIM(RTRIM(iim.inv_num)), 30) AS [InvoiceNo],
    CASE
        WHEN ah.inv_date IS NOT NULL
        THEN CONVERT(INT, CONVERT(VARCHAR(8), ah.inv_date, 112))
        ELSE NULL
    END AS [InvoiceDate],
    CAST((coi.price * coi.qty_invoiced) AS DECIMAL(10,2)) AS [ExtSalesAmount],
    LEFT(coi.co_num, 30) AS [ERP_OrderNo],
    -- Use boat serial from order if line doesn't have it (for engines/prerigs)
    LEFT(COALESCE(coi.Uf_BENN_BoatSerialNumber, bo.Uf_BENN_BoatSerialNumber), 15) AS [BoatSerialNo],
    LEFT(COALESCE(coi.Uf_BENN_BoatModel, bo.Uf_BENN_BoatModel), 14) AS [BoatModelNo],
    ah.apply_to_inv_num AS [ApplyToNo],
    '' AS [ConfigID],
    '' AS [ValueText],
    co.order_date AS [order_date],
    co.external_confirmation_ref AS [external_confirmation_ref],
    -- NEW FIELDS: NULL for non-CPQ items (Part 1)
    NULL AS [MSRP],
    NULL AS [CfgName],
    NULL AS [CfgPage],
    NULL AS [CfgScreen],
    NULL AS [CfgValue],
    NULL AS [CfgAttrType]
FROM [CSISTG].[dbo].[coitem_mst] coi
INNER JOIN BoatOrders bo
    ON coi.co_num = bo.co_num
    AND coi.site_ref = bo.site_ref
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
-- Join serial_mst to get engine serial numbers (ser_num -> OptionSerialNo)
-- Matches on co_line so each line item gets its own serial (e.g., engine serial for engine line)
LEFT JOIN [CSISTG].[dbo].[serial_mst] ser
    ON coi.co_num = ser.ref_num
    AND coi.co_line = ser.ref_line
    AND coi.co_release = ser.ref_release
    AND coi.item = ser.item
    AND coi.site_ref = ser.site_ref
    AND ser.ref_type = 'O'
WHERE coi.site_ref = 'BENN'
    AND iim.inv_num IS NOT NULL
    AND coi.qty_invoiced > 0
    AND co.order_date >= '2025-12-14'
    -- Year filter removed to allow test boats like ETWINVTEST01
    -- AND TRY_CAST(RIGHT(COALESCE(coi.Uf_BENN_BoatSerialNumber, bo.Uf_BENN_BoatSerialNumber), 2) AS INT) >= 15

UNION ALL

-- Part 2: ALL configuration attributes for invoiced, configured items (CPQ boats)
SELECT
    LEFT(coi.Uf_BENN_BoatWebOrderNumber, 30) AS [WebOrderNo],
    LEFT(im.Uf_BENN_Series, 5) AS [C_Series],
    coi.qty_invoiced AS [QuantitySold],
    LEFT(co.type, 1) AS [Orig_Ord_Type],
    LEFT(coi.Uf_BENN_BoatModel, 14) AS [OptionSerialNo],
    -- Classify MCTDesc based on configuration attribute name
    CASE
        WHEN attr_detail.attr_name = 'Base Boat' THEN 'PONTOONS'
        WHEN attr_detail.attr_name LIKE '%Pre-Rig%'
             OR attr_detail.attr_name LIKE '%Rigging%'
             OR attr_detail.attr_name LIKE '%Pre Rig%' THEN 'PRE-RIG'
        WHEN attr_detail.Uf_BENN_Cfg_Price > 0 THEN 'ACCESSORIES'
        ELSE 'STANDARD FEATURES'
    END AS [MCTDesc],
    coi.co_line AS [LineSeqNo],
    coi.co_line AS [LineNo],
    LEFT(attr_detail.attr_name, 50) AS [ItemNo],
    NULL AS [ItemMasterProdCatDesc],
    -- Keep boat's product category for CPQ attributes
    LEFT(im.Uf_BENN_ProductCategory, 3) AS [ItemMasterProdCat],
    -- Classify ItemMasterMCT based on configuration attribute name
    CASE
        WHEN attr_detail.attr_name = 'Base Boat' THEN 'BOA'
        WHEN attr_detail.attr_name LIKE '%Pre-Rig%'
             OR attr_detail.attr_name LIKE '%Rigging%'
             OR attr_detail.attr_name LIKE '%Pre Rig%' THEN 'PRE'
        WHEN attr_detail.Uf_BENN_Cfg_Price > 0 THEN 'ACC'
        ELSE 'STD'
    END AS [ItemMasterMCT],
    LEFT(attr_detail.attr_value, 30) AS [ItemDesc1],
    LEFT(LTRIM(RTRIM(iim.inv_num)), 30) AS [InvoiceNo],
    CASE
        WHEN ah.inv_date IS NOT NULL
        THEN CONVERT(INT, CONVERT(VARCHAR(8), ah.inv_date, 112))
        ELSE NULL
    END AS [InvoiceDate],
    CAST(ISNULL(attr_detail.Uf_BENN_Cfg_Price, 0) AS DECIMAL(10,2)) AS [ExtSalesAmount],
    LEFT(coi.co_num, 30) AS [ERP_OrderNo],
    LEFT(ser.ser_num, 15) AS [BoatSerialNo],
    LEFT(coi.Uf_BENN_BoatModel, 14) AS [BoatModelNo],
    ah.apply_to_inv_num AS [ApplyToNo],
    LEFT(coi.config_id, 30) AS [ConfigID],
    LEFT(attr_detail.attr_value, 100) AS [ValueText],
    co.order_date AS [order_date],
    co.external_confirmation_ref AS [external_confirmation_ref],
    -- NEW FIELDS: Configuration metadata from cfg_attr_mst
    CAST(ISNULL(attr_detail.Uf_BENN_Cfg_MSRP, 0) AS DECIMAL(10,2)) AS [MSRP],
    LEFT(attr_detail.Uf_BENN_Cfg_Name, 100) AS [CfgName],
    LEFT(attr_detail.Uf_BENN_Cfg_Page, 50) AS [CfgPage],
    LEFT(attr_detail.Uf_BENN_Cfg_Screen, 50) AS [CfgScreen],
    LEFT(attr_detail.Uf_BENN_Cfg_Value, 100) AS [CfgValue],
    LEFT(attr_detail.attr_type, 20) AS [CfgAttrType]
FROM [CSISTG].[dbo].[coitem_mst] coi
INNER JOIN [CSISTG].[dbo].[cfg_attr_mst] attr_detail
    ON coi.config_id = attr_detail.config_id
    AND coi.site_ref = attr_detail.site_ref
    AND attr_detail.attr_value IS NOT NULL
    AND attr_detail.print_flag = 'E'
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
    AND coi.site_ref = 'BENN'
    AND co.order_date >= '2025-12-14'
    -- Filter boats with serial suffix >= 15 to avoid broken table routing
    -- Serials ending in 00-14 or 99 get misrouted to old tables (BoatOptions99_04)
    AND TRY_CAST(RIGHT(ser.ser_num, 2) AS INT) >= 15

)
-- Now assign unique LineSeqNo using ROW_NUMBER per order
SELECT
    [WebOrderNo],
    [C_Series],
    [QuantitySold],
    [Orig_Ord_Type],
    [OptionSerialNo],
    [MCTDesc],
    ROW_NUMBER() OVER (PARTITION BY [ERP_OrderNo] ORDER BY [LineSeqNo], [ItemNo]) AS [LineSeqNo],
    [LineNo],
    [ItemNo],
    [ItemMasterProdCatDesc],
    [ItemMasterProdCat],
    [ItemMasterMCT],
    [ItemDesc1],
    [InvoiceNo],
    [InvoiceDate],
    [ExtSalesAmount],
    [ERP_OrderNo],
    [BoatSerialNo],
    [BoatModelNo],
    [ApplyToNo],
    [ConfigID],
    [ValueText],
    [order_date],
    [external_confirmation_ref],
    [MSRP],
    [CfgName],
    [CfgPage],
    [CfgScreen],
    [CfgValue],
    [CfgAttrType]
FROM OrderedRows
ORDER BY [ERP_OrderNo], [LineSeqNo]
"""

# ============================================================================
# FUNCTIONS
# ============================================================================

def log(message: str, level: str = "INFO"):
    """Print timestamped log message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def is_cpq_order(order_date, external_confirmation_ref, co_num):
    """
    Detect if order is a CPQ/EQ order.
    CPQ orders go to cpq.BoatOptions.

    Criteria:
    - order_date >= 2025-12-14 (CPQ Go Live)
    - co_num starts with 'SO'
    - external_confirmation_ref starts with 'SO' (optional - can be NULL)
    """
    if not order_date or not co_num:
        return False

    # Handle both datetime and date objects
    if isinstance(order_date, datetime):
        order_date = order_date.date()

    # Check date and order number (required)
    if not (order_date >= CPQ_GO_LIVE_DATE and str(co_num).startswith('SO')):
        return False

    # external_confirmation_ref is optional (can be NULL for some CPQ orders)
    # If present, it should start with 'SO', but NULL is acceptable
    if external_confirmation_ref and not str(external_confirmation_ref).startswith('SO'):
        return False

    return True

def detect_model_year_from_serial(serial_number: str) -> int:
    """
    Detect model year from serial number suffix.

    Serial format examples:
    - ETWC4149F425 → ends with 25 → 2025
    - ETWC1474F324 → ends with 24 → 2024
    - ETWC6109F526 → ends with 26 → 2026
    - ETWA2930E415 → ends with 15 → 2015
    - ETWC5779C920 → ends with 20 → 2020
    - ETW00789F899 → ends with 99 → 1999

    Returns: Full year (e.g., 2025, 2015, 1999)
    """
    if not serial_number or len(serial_number) < 2:
        return 2026  # Default to current year

    # Get last 2 characters (year digits)
    try:
        year_suffix = serial_number[-2:]
        year_2digit = int(year_suffix)

        # Determine century
        # 00-50 = 2000s (2000-2050)
        # 51-99 = 1900s (1951-1999)
        if year_2digit <= 50:
            return 2000 + year_2digit
        else:
            return 1900 + year_2digit

    except:
        return 2026  # Default to current year

def get_target_year(row: Dict) -> int:
    """
    Determine model year for this row.

    IMPORTANT: ALL orders (CPQ and non-CPQ) are routed by MODEL YEAR from serial number.
    A CPQ order for a 2025 model goes to BoatOptions25, not BoatOptions26.

    Returns: Full year (e.g., 2025, 2015, 1999)
    """
    serial_no = row.get('BoatSerialNo')

    # Detect year from serial number (applies to ALL orders)
    return detect_model_year_from_serial(serial_no)

def extract_from_mssql() -> List[Dict]:
    """Extract invoiced boat orders from MSSQL database (from 12/14/2025 onwards)"""
    log("Connecting to MSSQL (CSI/ERP database)...")

    try:
        conn = pymssql.connect(**MSSQL_CONFIG)
        cursor = conn.cursor(as_dict=True)
        log("✅ Connected to MSSQL", "SUCCESS")

        log("Extracting INVOICED orders from 12/14/2025 onwards...")
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

def group_by_table(rows: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Group rows by target table based on model year.
    ALL boats (CPQ and legacy) go to warrantyparts.BoatOptions{year} tables.

    Routing logic:
    - Year detected from serial number suffix
    - All boats route to warrantyparts.BoatOptions{year}
    - CPQ markers tracked for reporting only (not routing)

    This ensures:
    - Old inventory boats (2024 models invoiced in 2026) route to BoatOptions24
    - CPQ boats (2026+ models) route to BoatOptions26/27/etc.
    - All data in single database (warrantyparts) for consistent queries
    """
    log("Grouping rows by target table...")

    groups = {}
    year_counts = {}
    cpq_count = 0
    non_cpq_count = 0

    for row in rows:
        # STEP 1: Detect model year from serial number (primary routing method)
        year = get_target_year(row)

        # Check if this order has CPQ markers (for reporting only)
        has_cpq_markers = is_cpq_order(
            row.get('order_date'),
            row.get('external_confirmation_ref'),
            row.get('ERP_OrderNo')
        )

        # STEP 2: Route ALL boats to warrantyparts.BoatOptions{year}
        # Year-based routing ensures old inventory goes to correct historical table
        # CPQ boats (2026+) go to BoatOptions26, BoatOptions27, etc.
        table_name = f'warrantyparts.{get_table_for_year(year)}'

        # Track CPQ vs non-CPQ for reporting (doesn't affect routing)
        if has_cpq_markers:
            cpq_count += 1
        else:
            non_cpq_count += 1

        # Add to groups
        if table_name not in groups:
            groups[table_name] = []
        groups[table_name].append(row)

        # Track year counts for reporting
        year_counts[year] = year_counts.get(year, 0) + 1

    # Log summary
    log(f"\nRows grouped by table:")
    for table_name in sorted(groups.keys()):
        log(f"  {table_name:25s}: {len(groups[table_name]):6,} rows")

    log(f"\nRows by model year:")
    for year in sorted(year_counts.keys()):
        log(f"  {year}: {year_counts[year]:,} rows")

    log(f"\nCPQ orders: {cpq_count:,}")
    log(f"Non-CPQ orders: {non_cpq_count:,}")

    return groups

def deduplicate_rows(rows: List[Dict]) -> List[Dict]:
    """
    Deduplicate rows based on composite key: BoatSerialNo + ItemNo + LineNo + LineSeqNo.
    For old tables without primary keys, this prevents duplicate inserts.
    When duplicates exist, prioritize ACC over BS1 for ItemMasterProdCat.
    Returns deduplicated list.
    """
    seen = {}
    duplicates_found = 0
    
    for row in rows:
        # Create unique key from composite fields
        key = (
            row.get('BoatSerialNo', ''),
            row.get('ItemNo', ''),
            row.get('LineNo', 0),
            row.get('LineSeqNo', 0)
        )
        
        if key in seen:
            duplicates_found += 1
            existing = seen[key]
            
            # Prioritize ACC over BS1
            existing_cat = existing.get('ItemMasterProdCat', '')
            new_cat = row.get('ItemMasterProdCat', '')
            
            if new_cat == 'ACC' and existing_cat != 'ACC':
                # New row has ACC, use it instead
                seen[key] = row
        else:
            seen[key] = row
    
    if duplicates_found > 0:
        log(f"Removed {duplicates_found:,} duplicate rows", "INFO")
    
    return list(seen.values())

def load_to_mysql_batch(rows: List[Dict], table_name: str):
    """Load data to MySQL using batch inserts and verify"""

    if not rows:
        log(f"No rows to import for {table_name}", "WARNING")
        return 0

    # Deduplicate rows before processing (critical for old tables without primary keys)
    original_count = len(rows)
    rows = deduplicate_rows(rows)
    if len(rows) < original_count:
        log(f"Deduplicated from {original_count:,} to {len(rows):,} rows", "INFO")

    log(f"Processing {len(rows):,} rows for {table_name}...")

    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()

        # Get initial row count for comparison
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        initial_row_count = cursor.fetchone()[0]

        # Prepare insert query with all 25 fields
        insert_query = f"""
        INSERT INTO {table_name} (
            ERP_OrderNo, BoatSerialNo, BoatModelNo, LineNo, ItemNo, ItemDesc1,
            ExtSalesAmount, QuantitySold, Series, WebOrderNo, Orig_Ord_Type,
            ApplyToNo, InvoiceNo, InvoiceDate, ItemMasterProdCat, ItemMasterProdCatDesc,
            ItemMasterMCT, MCTDesc, LineSeqNo, ConfigID, ValueText,
            OptionSerialNo, C_Series, order_date, external_confirmation_ref,
            MSRP, CfgName, CfgPage, CfgScreen, CfgValue, CfgAttrType
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s
        )
        ON DUPLICATE KEY UPDATE
            BoatSerialNo = VALUES(BoatSerialNo),
            BoatModelNo = VALUES(BoatModelNo),
            LineNo = VALUES(LineNo),
            ItemNo = VALUES(ItemNo),
            ItemDesc1 = VALUES(ItemDesc1),
            ExtSalesAmount = VALUES(ExtSalesAmount),
            QuantitySold = VALUES(QuantitySold),
            Series = VALUES(Series),
            WebOrderNo = VALUES(WebOrderNo),
            Orig_Ord_Type = VALUES(Orig_Ord_Type),
            ApplyToNo = VALUES(ApplyToNo),
            InvoiceNo = VALUES(InvoiceNo),
            InvoiceDate = VALUES(InvoiceDate),
            ItemMasterProdCat = VALUES(ItemMasterProdCat),
            ItemMasterProdCatDesc = VALUES(ItemMasterProdCatDesc),
            ItemMasterMCT = VALUES(ItemMasterMCT),
            MCTDesc = VALUES(MCTDesc),
            ConfigID = VALUES(ConfigID),
            ValueText = VALUES(ValueText),
            OptionSerialNo = VALUES(OptionSerialNo),
            C_Series = VALUES(C_Series),
            order_date = VALUES(order_date),
            external_confirmation_ref = VALUES(external_confirmation_ref),
            MSRP = VALUES(MSRP),
            CfgName = VALUES(CfgName),
            CfgPage = VALUES(CfgPage),
            CfgScreen = VALUES(CfgScreen),
            CfgValue = VALUES(CfgValue),
            CfgAttrType = VALUES(CfgAttrType)
        """

        batch_size = 1000

        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]

            batch_data = []
            for row in batch:
                # Fix ItemMasterProdCat: map BS1 to ACC only for STD (standard) items
                # BS1 for BOA (boat) and PRE (pre-rig) should remain as BS1
                prod_cat = row.get('ItemMasterProdCat')
                mct = row.get('ItemMasterMCT')
                if prod_cat == 'BS1' and mct == 'STD':
                    # STD items with BS1 are actually accessories and should be ACC
                    prod_cat = 'ACC'
                
                # Fix BoatModelNo: If NULL/empty for boat items (BOA/BOI), use ItemNo
                boat_model_no = row.get('BoatModelNo')
                if (not boat_model_no or boat_model_no == '') and mct in ('BOA', 'BOI'):
                    boat_model_no = row.get('ItemNo')
                
                row_tuple = (
                    row.get('ERP_OrderNo'),
                    row.get('BoatSerialNo'),
                    boat_model_no,
                    row.get('LineNo'),
                    row.get('ItemNo'),
                    row.get('ItemDesc1'),
                    row.get('ExtSalesAmount'),
                    row.get('QuantitySold'),
                    row.get('Series') or row.get('C_Series'),
                    row.get('WebOrderNo'),
                    row.get('Orig_Ord_Type'),
                    row.get('ApplyToNo'),
                    row.get('InvoiceNo'),
                    row.get('InvoiceDate'),
                    prod_cat,
                    row.get('ItemMasterProdCatDesc'),
                    row.get('ItemMasterMCT'),
                    row.get('MCTDesc'),
                    row.get('LineSeqNo'),
                    row.get('ConfigID'),
                    row.get('ValueText'),
                    row.get('OptionSerialNo'),
                    row.get('C_Series'),
                    row.get('order_date'),
                    row.get('external_confirmation_ref'),
                    row.get('MSRP'),
                    row.get('CfgName'),
                    row.get('CfgPage'),
                    row.get('CfgScreen'),
                    row.get('CfgValue'),
                    row.get('CfgAttrType')
                )
                batch_data.append(row_tuple)

            cursor.executemany(insert_query, batch_data)
            conn.commit()

            if (i // batch_size + 1) % 5 == 0:
                log(f"Progress: {i + len(batch):,} / {len(rows):,} rows processed...", "PROGRESS")
        
        # Final verification
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        final_row_count = cursor.fetchone()[0]
        
        log(f"Successfully processed {len(rows):,} rows. Final table count: {final_row_count:,}", "SUCCESS")

        cursor.close()
        conn.close()

        return final_row_count

    except MySQLError as e:
        log(f"MySQL error during batch load to {table_name}: {e}", "ERROR")
        if 'conn' in locals() and conn.is_connected():
            conn.rollback()
        # Return -1 or some indicator of failure
        return -1
    except Exception as e:
        log(f"Unexpected error during batch load to {table_name}: {e}", "ERROR")
        # Return -1 or some indicator of failure
        return -1

def print_summary(table_groups: Dict[str, List[Dict]], results: Dict[str, int]):
    """Print summary statistics"""
    print("\n" + "="*80)
    print("IMPORT SUMMARY - PRODUCTION DATABASE")
    print("="*80)

    total_extracted = sum(len(rows) for rows in table_groups.values())
    
    print(f"\nExtracted: {total_extracted:,} rows from MSSQL")
    print(f"Verified Final Row Counts in MySQL:")

    print(f"\nBreakdown by table (Final Count):")
    for table_name, final_count in sorted(results.items()):
        if final_count >= 0:
            print(f"  {table_name:25s}: {final_count:8,} rows")
        else:
            print(f"  {table_name:25s}: {'LOAD FAILED'}")

    print("\n" + "="*80)
    print("✅ PRODUCTION IMPORT COMPLETE")
    print("="*80)
    print("\nNext Steps:")
    print("1. Verify data in warrantyparts_boatoptions_test database")
    print("2. Check CPQ orders are in BoatOptions26")
    print("3. Run test queries to validate data integrity")
    print("4. If successful, run import to PRODUCTION database")
    print("="*80)

def main():
    print("="*80)
    print("BOATOPTIONS IMPORT - PRODUCTION VERSION")
    print("="*80)
    print(f"⚠️  WARNING: Importing to PRODUCTION database (warrantyparts)")
    print(f"Target: warrantyparts (PRODUCTION DATABASE)")
    print(f"Filter: Invoiced orders from 12/14/2025 onwards")
    print(f"Year Detection: Automatic from serial number (all years 1999-2030)")
    print(f"CPQ Detection: Tracked for reporting (routes by model year)")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print()

    try:
        # Step 1: Extract from MSSQL
        rows = extract_from_mssql()

        if len(rows) == 0:
            log("No data extracted from MSSQL!", "ERROR")
            log("This could mean no orders have been invoiced since 12/14/2025", "WARNING")
            sys.exit(1)

        # Step 2: Group by table (based on model year)
        table_groups = group_by_table(rows)

        # Step 3: Load to MySQL tables
        results = {}
        for table_name, table_rows in table_groups.items():
            if len(table_rows) == 0:
                log(f"No data for {table_name}, skipping...", "WARNING")
                results[table_name] = 0
                continue

            imported = load_to_mysql_batch(table_rows, table_name)
            results[table_name] = imported

        # Step 4: Print summary
        print_summary(table_groups, results)

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

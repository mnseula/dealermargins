#!/usr/bin/env python3
"""
BoatOptions Import Script - PRODUCTION VERSION

Imports INVOICED boat orders from TODAY to warrantyparts database.

Routing: Model year detected from serial number suffix → warrantyparts.BoatOptions{YY}

Usage:
    python3 import_boatoptions_production.py
"""

import sys
from datetime import datetime
from typing import List, Dict
import pymssql
import mysql.connector
from mysql.connector import Error as MySQLError

# ============================================================================
# DATABASE CONFIGURATION - ALWAYS PRODUCTION
# ============================================================================

MSSQL_CONFIG = {
    'server': 'MPL1ITSSQL086.POLARISIND.COM',
    'database': 'CSIPRD',
    'user': 'svcSpecs01',
    'password': 'SD4nzr0CJ5oj38',
    'timeout': 300,
    'login_timeout': 60
}

MSSQL_DATABASE = MSSQL_CONFIG['database']

MYSQL_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'warrantyparts',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD'
}

# ============================================================================
# TABLE MAPPING BY YEAR
# ============================================================================

def get_table_for_year(year: int) -> str:
    """Map model year to BoatOptions table name."""
    if 1999 <= year <= 2004:
        return 'BoatOptions99_04'
    elif 2005 <= year <= 2007:
        return 'BoatOptions05_07'
    elif 2008 <= year <= 2010:
        return 'BoatOptions08_10'
    elif 2011 <= year <= 2014:
        return 'BoatOptions11_14'
    elif year >= 2015:
        return f'BoatOptions{year % 100:02d}'
    else:
        return 'BoatOptionsBefore_05'


# ============================================================================
# MSSQL QUERY - TODAY'S INVOICED ORDERS ONLY, NO NEGATIVE QUANTITIES
# ============================================================================

def build_query(db: str) -> str:
    return f"""
WITH BoatOrders AS (
    SELECT DISTINCT
        coi.co_num,
        coi.site_ref,
        COALESCE(
            NULLIF(coi.Uf_BENN_BoatSerialNumber, ''),
            ser.ser_num
        ) AS Uf_BENN_BoatSerialNumber,
        coi.Uf_BENN_BoatModel,
        coi.config_id
    FROM [{db}].[dbo].[coitem_mst] coi
    LEFT JOIN [{db}].[dbo].[serial_mst] ser
        ON coi.co_num = ser.ref_num
        AND coi.co_line = ser.ref_line
        AND coi.co_release = ser.ref_release
        AND coi.item = ser.item
        AND coi.site_ref = ser.site_ref
        AND ser.ref_type = 'O'
    WHERE coi.site_ref = 'BENN'
        AND (
            (coi.Uf_BENN_BoatSerialNumber IS NOT NULL AND coi.Uf_BENN_BoatSerialNumber != '')
            OR (coi.config_id IS NOT NULL AND coi.config_id != '')
            OR (ser.ser_num IS NOT NULL AND ser.ser_num != '')
        )
),
OrderedRows AS (

-- Part 1: Main order lines (boat, engine, prerigs, accessories)
SELECT
    LEFT(coi.Uf_BENN_BoatWebOrderNumber, 30)            AS [WebOrderNo],
    LEFT(im.Uf_BENN_Series, 5)                          AS [C_Series],
    coi.qty_invoiced                                    AS [QuantitySold],
    LEFT(co.type, 1)                                    AS [Orig_Ord_Type],
    LEFT(ser.ser_num, 12)                               AS [OptionSerialNo],
    pcm.description                                     AS [MCTDesc],
    coi.co_line                                         AS [LineSeqNo],
    coi.co_line                                         AS [LineNo],
    LEFT(coi.item, 15)                                  AS [ItemNo],
    NULL                                                AS [ItemMasterProdCatDesc],
    LEFT(im.Uf_BENN_ProductCategory, 3)                 AS [ItemMasterProdCat],
    LEFT(im.Uf_BENN_MaterialCostType, 10)               AS [ItemMasterMCT],
    LEFT(coi.description, 100)                          AS [ItemDesc1],
    LEFT(LTRIM(RTRIM(iim.inv_num)), 30)                 AS [InvoiceNo],
    CASE
        WHEN ah.inv_date IS NOT NULL
        THEN CONVERT(INT, CONVERT(VARCHAR(8), ah.inv_date, 112))
        ELSE NULL
    END                                                 AS [InvoiceDate],
    CAST((coi.price * coi.qty_invoiced) AS DECIMAL(10,2)) AS [ExtSalesAmount],
    LEFT(coi.co_num, 30)                                AS [ERP_OrderNo],
    LEFT(COALESCE(coi.Uf_BENN_BoatSerialNumber, bo.Uf_BENN_BoatSerialNumber), 15) AS [BoatSerialNo],
    LEFT(COALESCE(coi.Uf_BENN_BoatModel, bo.Uf_BENN_BoatModel), 14) AS [BoatModelNo],
    ah.apply_to_inv_num                                 AS [ApplyToNo],
    ''                                                  AS [ConfigID],
    ''                                                  AS [ValueText],
    co.order_date                                       AS [order_date],
    co.external_confirmation_ref                        AS [external_confirmation_ref],
    NULL                                                AS [MSRP],
    NULL                                                AS [CfgName],
    NULL                                                AS [CfgPage],
    NULL                                                AS [CfgScreen],
    NULL                                                AS [CfgValue],
    NULL                                                AS [CfgAttrType]
FROM [{db}].[dbo].[coitem_mst] coi
INNER JOIN BoatOrders bo
    ON coi.co_num = bo.co_num
    AND coi.site_ref = bo.site_ref
LEFT JOIN [{db}].[dbo].[inv_item_mst] iim
    ON coi.co_num = iim.co_num
    AND coi.co_line = iim.co_line
    AND coi.co_release = iim.co_release
    AND coi.site_ref = iim.site_ref
LEFT JOIN [{db}].[dbo].[arinv_mst] ah
    ON iim.inv_num = ah.inv_num
    AND iim.site_ref = ah.site_ref
LEFT JOIN [{db}].[dbo].[co_mst] co
    ON coi.co_num = co.co_num
    AND coi.site_ref = co.site_ref
LEFT JOIN [{db}].[dbo].[item_mst] im
    ON coi.item = im.item
    AND coi.site_ref = im.site_ref
LEFT JOIN [{db}].[dbo].[prodcode_mst] pcm
    ON im.Uf_BENN_MaterialCostType = pcm.product_code
    AND im.site_ref = pcm.site_ref
LEFT JOIN [{db}].[dbo].[serial_mst] ser
    ON coi.co_num = ser.ref_num
    AND coi.co_line = ser.ref_line
    AND coi.co_release = ser.ref_release
    AND coi.item = ser.item
    AND coi.site_ref = ser.site_ref
    AND ser.ref_type = 'O'
WHERE coi.site_ref = 'BENN'
    AND iim.inv_num IS NOT NULL
    AND coi.qty_invoiced > 0
    AND CAST(ah.inv_date AS DATE) = CAST(GETDATE() AS DATE)

UNION ALL

-- Part 2: Configuration attributes for CPQ invoiced items
SELECT
    LEFT(coi.Uf_BENN_BoatWebOrderNumber, 30)            AS [WebOrderNo],
    LEFT(im.Uf_BENN_Series, 5)                          AS [C_Series],
    coi.qty_invoiced                                    AS [QuantitySold],
    LEFT(co.type, 1)                                    AS [Orig_Ord_Type],
    LEFT(coi.Uf_BENN_BoatModel, 14)                     AS [OptionSerialNo],
    CASE
        WHEN attr_detail.attr_name = 'Base Boat' THEN 'PONTOONS'
        WHEN attr_detail.attr_name LIKE '%Pre-Rig%'
             OR attr_detail.attr_name LIKE '%Rigging%'
             OR attr_detail.attr_name LIKE '%Pre Rig%' THEN 'PRE-RIG'
        WHEN attr_detail.Uf_BENN_Cfg_Price > 0 THEN 'ACCESSORIES'
        ELSE 'STANDARD FEATURES'
    END                                                 AS [MCTDesc],
    coi.co_line                                         AS [LineSeqNo],
    coi.co_line                                         AS [LineNo],
    LEFT(attr_detail.attr_name, 50)                     AS [ItemNo],
    NULL                                                AS [ItemMasterProdCatDesc],
    LEFT(im.Uf_BENN_ProductCategory, 3)                 AS [ItemMasterProdCat],
    CASE
        WHEN attr_detail.attr_name = 'Base Boat' THEN 'BOA'
        WHEN attr_detail.attr_name LIKE '%Pre-Rig%'
             OR attr_detail.attr_name LIKE '%Rigging%'
             OR attr_detail.attr_name LIKE '%Pre Rig%' THEN 'PRE'
        WHEN attr_detail.Uf_BENN_Cfg_Price > 0 THEN 'ACC'
        ELSE 'STD'
    END                                                 AS [ItemMasterMCT],
    LEFT(attr_detail.attr_value, 100)                   AS [ItemDesc1],
    LEFT(LTRIM(RTRIM(iim.inv_num)), 30)                 AS [InvoiceNo],
    CASE
        WHEN ah.inv_date IS NOT NULL
        THEN CONVERT(INT, CONVERT(VARCHAR(8), ah.inv_date, 112))
        ELSE NULL
    END                                                 AS [InvoiceDate],
    CAST(ISNULL(attr_detail.Uf_BENN_Cfg_Price, 0) AS DECIMAL(10,2)) AS [ExtSalesAmount],
    LEFT(coi.co_num, 30)                                AS [ERP_OrderNo],
    LEFT(ser.ser_num, 15)                               AS [BoatSerialNo],
    LEFT(coi.Uf_BENN_BoatModel, 14)                     AS [BoatModelNo],
    ah.apply_to_inv_num                                 AS [ApplyToNo],
    LEFT(coi.config_id, 30)                             AS [ConfigID],
    LEFT(attr_detail.attr_value, 100)                   AS [ValueText],
    co.order_date                                       AS [order_date],
    co.external_confirmation_ref                        AS [external_confirmation_ref],
    CAST(ISNULL(attr_detail.Uf_BENN_Cfg_MSRP, 0) AS DECIMAL(10,2)) AS [MSRP],
    LEFT(attr_detail.Uf_BENN_Cfg_Name, 100)             AS [CfgName],
    LEFT(attr_detail.Uf_BENN_Cfg_Page, 50)              AS [CfgPage],
    LEFT(attr_detail.Uf_BENN_Cfg_Screen, 50)            AS [CfgScreen],
    LEFT(attr_detail.Uf_BENN_Cfg_Value, 100)            AS [CfgValue],
    LEFT(attr_detail.attr_type, 20)                     AS [CfgAttrType]
FROM [{db}].[dbo].[coitem_mst] coi
INNER JOIN [{db}].[dbo].[cfg_attr_mst] attr_detail
    ON coi.config_id = attr_detail.config_id
    AND coi.site_ref = attr_detail.site_ref
    AND attr_detail.attr_value IS NOT NULL
    AND attr_detail.print_flag = 'E'
LEFT JOIN [{db}].[dbo].[cfg_comp_mst] ccm
    ON attr_detail.config_id = ccm.config_id
    AND attr_detail.comp_id = ccm.comp_id
    AND attr_detail.site_ref = ccm.site_ref
LEFT JOIN [{db}].[dbo].[inv_item_mst] iim
    ON coi.co_num = iim.co_num
    AND coi.co_line = iim.co_line
    AND coi.co_release = iim.co_release
    AND coi.site_ref = iim.site_ref
LEFT JOIN [{db}].[dbo].[arinv_mst] ah
    ON iim.inv_num = ah.inv_num
    AND iim.site_ref = ah.site_ref
LEFT JOIN [{db}].[dbo].[co_mst] co
    ON coi.co_num = co.co_num
    AND coi.site_ref = co.site_ref
LEFT JOIN [{db}].[dbo].[item_mst] im
    ON coi.item = im.item
    AND coi.site_ref = im.site_ref
LEFT JOIN [{db}].[dbo].[serial_mst] ser
    ON coi.co_num = ser.ref_num
    AND coi.co_line = ser.ref_line
    AND coi.co_release = ser.ref_release
    AND coi.item = ser.item
    AND coi.site_ref = ser.site_ref
    AND ser.ref_type = 'O'
WHERE coi.config_id IS NOT NULL
    AND coi.site_ref = 'BENN'
    AND coi.qty_invoiced > 0
    AND CAST(ah.inv_date AS DATE) = CAST(GETDATE() AS DATE)

)
SELECT
    [WebOrderNo], [C_Series], [QuantitySold], [Orig_Ord_Type], [OptionSerialNo],
    [MCTDesc],
    ROW_NUMBER() OVER (PARTITION BY [ERP_OrderNo] ORDER BY [LineSeqNo], [ItemNo]) AS [LineSeqNo],
    [LineNo], [ItemNo], [ItemMasterProdCatDesc], [ItemMasterProdCat], [ItemMasterMCT],
    [ItemDesc1], [InvoiceNo], [InvoiceDate], [ExtSalesAmount], [ERP_OrderNo],
    [BoatSerialNo], [BoatModelNo], [ApplyToNo], [ConfigID], [ValueText],
    [order_date], [external_confirmation_ref],
    [MSRP], [CfgName], [CfgPage], [CfgScreen], [CfgValue], [CfgAttrType]
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


def detect_model_year_from_serial(serial_number: str) -> int:
    """Detect model year from last 2 digits of serial number."""
    if not serial_number or len(serial_number) < 2:
        return datetime.now().year
    try:
        year_2digit = int(serial_number[-2:])
        return 2000 + year_2digit if year_2digit <= 50 else 1900 + year_2digit
    except (ValueError, TypeError):
        return datetime.now().year


def get_target_year(row: Dict) -> int:
    """Determine model year for this row from its serial number."""
    return detect_model_year_from_serial(row.get('BoatSerialNo'))


def extract_from_mssql() -> List[Dict]:
    """Extract today's invoiced boat orders from MSSQL."""
    log(f"Connecting to MSSQL ({MSSQL_CONFIG['server']} / {MSSQL_DATABASE})...")
    try:
        conn = pymssql.connect(**MSSQL_CONFIG)
        cursor = conn.cursor(as_dict=True)
        log("Connected to MSSQL", "SUCCESS")
        log(f"Extracting today's invoiced orders (no negative quantities)...")
        cursor.execute(build_query(MSSQL_DATABASE))
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
    """Group rows by target warrantyparts.BoatOptions table based on model year."""
    log("Grouping rows by target table...")
    groups: Dict[str, List[Dict]] = {}
    year_counts: Dict[int, int] = {}

    for row in rows:
        year = get_target_year(row)
        table_name = f'warrantyparts.{get_table_for_year(year)}'

        if table_name not in groups:
            groups[table_name] = []
        groups[table_name].append(row)
        year_counts[year] = year_counts.get(year, 0) + 1

    log("Rows grouped by table:")
    for table_name in sorted(groups.keys()):
        log(f"  {table_name}: {len(groups[table_name]):,} rows")

    log("Rows by model year:")
    for year in sorted(year_counts.keys()):
        log(f"  {year}: {year_counts[year]:,} rows")

    return groups


def deduplicate_rows(rows: List[Dict]) -> List[Dict]:
    """
    Deduplicate rows on composite key: BoatSerialNo + ItemNo + LineNo + LineSeqNo.
    When duplicates exist, prioritize ACC over BS1 for ItemMasterProdCat.
    """
    seen = {}
    duplicates_found = 0

    for row in rows:
        key = (
            row.get('BoatSerialNo', ''),
            row.get('ItemNo', ''),
            row.get('LineNo', 0),
            row.get('LineSeqNo', 0)
        )

        if key in seen:
            duplicates_found += 1
            existing = seen[key]
            if row.get('ItemMasterProdCat') == 'ACC' and existing.get('ItemMasterProdCat') != 'ACC':
                seen[key] = row
        else:
            seen[key] = row

    if duplicates_found > 0:
        log(f"Removed {duplicates_found:,} duplicate rows")

    return list(seen.values())


def load_to_mysql_batch(rows: List[Dict], table_name: str) -> int:
    """Load data to MySQL using batch inserts."""
    if not rows:
        log(f"No rows to import for {table_name}", "WARNING")
        return 0

    original_count = len(rows)
    rows = deduplicate_rows(rows)
    if len(rows) < original_count:
        log(f"Deduplicated from {original_count:,} to {len(rows):,} rows")

    log(f"Processing {len(rows):,} rows for {table_name}...")

    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()

        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        initial_count = cursor.fetchone()[0]

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
            BoatModelNo = VALUES(BoatModelNo),
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
                # Map BS1 → ACC for STD items
                prod_cat = row.get('ItemMasterProdCat')
                mct = row.get('ItemMasterMCT')
                if prod_cat == 'BS1' and mct == 'STD':
                    prod_cat = 'ACC'

                # Use ItemNo as BoatModelNo fallback for boat lines
                boat_model_no = row.get('BoatModelNo')
                if (not boat_model_no) and mct in ('BOA', 'BOI'):
                    boat_model_no = row.get('ItemNo')

                batch_data.append((
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
                ))

            cursor.executemany(insert_query, batch_data)
            conn.commit()

            progress = i + len(batch)
            if (i // batch_size + 1) % 5 == 0:
                log(f"Progress: {progress:,} / {len(rows):,} rows processed...", "PROGRESS")

        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        final_count = cursor.fetchone()[0]
        log(f"Inserted {len(rows):,} rows into {table_name}. Table now has {final_count:,} rows.", "SUCCESS")

        cursor.close()
        conn.close()
        return final_count

    except MySQLError as e:
        log(f"MySQL error loading {table_name}: {e}", "ERROR")
        if 'conn' in locals() and conn.is_connected():
            conn.rollback()
        return -1
    except Exception as e:
        log(f"Unexpected error loading {table_name}: {e}", "ERROR")
        return -1


def print_summary(table_groups: Dict[str, List[Dict]], results: Dict[str, int]):
    """Print import summary."""
    print("\n" + "=" * 80)
    print("IMPORT SUMMARY")
    print("=" * 80)
    total_extracted = sum(len(rows) for rows in table_groups.values())
    print(f"\nExtracted from MSSQL ({MSSQL_DATABASE}): {total_extracted:,} rows")
    print(f"\nFinal row counts in warrantyparts:")
    for table_name, final_count in sorted(results.items()):
        if final_count >= 0:
            print(f"  {table_name}: {final_count:,} rows")
        else:
            print(f"  {table_name}: LOAD FAILED")
    print("\n" + "=" * 80)
    print("IMPORT COMPLETE")
    print("=" * 80)


def main():
    print("=" * 80)
    print("BOATOPTIONS IMPORT - PRODUCTION")
    print("=" * 80)
    print(f"MSSQL Source:  {MSSQL_DATABASE} on {MSSQL_CONFIG['server']}")
    print(f"MySQL Target:  warrantyparts")
    print(f"Invoice Filter: Today only ({datetime.now().strftime('%Y-%m-%d')})")
    print(f"Started:       {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()

    try:
        rows = extract_from_mssql()

        if not rows:
            log("No invoiced orders found for today.", "WARNING")
            sys.exit(0)

        table_groups = group_by_table(rows)

        results = {}
        for table_name, table_rows in table_groups.items():
            results[table_name] = load_to_mysql_batch(table_rows, table_name)

        print_summary(table_groups, results)
        log("Import completed successfully.", "SUCCESS")

    except KeyboardInterrupt:
        log("Import cancelled by user.", "WARNING")
        sys.exit(1)
    except Exception as e:
        log(f"Import failed: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

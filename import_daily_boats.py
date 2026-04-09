#!/usr/bin/env python3
"""
Daily Boat Import Pipeline

Step 1: Import all invoiced line items  → {MYSQL_DB}.BoatOptions{YY}
Step 2: Import boat serial records      → {MYSQL_DB}.SerialNumberMaster
                                        → {MYSQL_DB}.SerialNumberRegistrationStatus

Runs daily, today's invoices only, always against CSIPRD.
Only processes boat orders (external_confirmation_ref LIKE 'SO%' or numeric).

Usage:
    python3 import_daily_boats.py
"""

import sys
import os
import csv
import tempfile
from datetime import datetime
from typing import List, Dict, Set, Tuple

import requests
import urllib3
import pymssql
import mysql.connector
import load_cpq_data
import build_liquifire_url

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================================
# CONFIGURATION - ALWAYS PRODUCTION
# ============================================================================

MSSQL_CONFIG = {
    'server': 'MPL1ITSSQL086.POLARISIND.COM',
    'database': 'CSIPRD',
    'user': 'svcSpecs01',
    'password': 'SD4nzr0CJ5oj38',
    'timeout': 300,
    'login_timeout': 60
}

MYSQL_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'warrantyparts',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD'
}

MSSQL_DB = MSSQL_CONFIG['database']
MYSQL_DB  = MYSQL_CONFIG['database']


# ============================================================================
# HELPERS
# ============================================================================

def log(message: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def get_table_for_year(year: int) -> str:
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


def detect_model_year(serial: str) -> int:
    """Detect 4-digit model year from ETW HIN last 2 chars."""
    if not serial or not str(serial).upper().startswith('ETW') or len(serial) < 12:
        return datetime.now().year
    try:
        y = int(serial[-2:])
        return 2000 + y if y <= 50 else 1900 + y
    except (ValueError, TypeError):
        return datetime.now().year


def load_rep_names() -> dict:
    """Return ({slsman_int: SalesRepName}, {state: SalesRepName})
    from Syteline_RepNames.xlsx on the network share and a state-based fallback
    built from SalesRepMaster in MySQL.
    """
    import pandas as pd
    path = r'\\elk1itsqvp001\qlik\Common\SourceData-Excel\Syteline_RepNames.xlsx'
    try:
        df = pd.read_excel(path, sheet_name='Names', usecols=['slsman', 'SalesRepName'],
                           engine='openpyxl')
        slsman_map = {
            int(row.slsman): str(row.SalesRepName).strip()
            for row in df.itertuples(index=False)
            if pd.notna(row.slsman) and pd.notna(row.SalesRepName)
        }
    except Exception as e:
        log(f"WARNING: Could not load rep names from network share ({e}) — ParentRepName will use state fallback only", "WARNING")
        slsman_map = {}

    # Build state -> SalesRepName fallback from SalesRepMaster in MySQL.
    # Territory field contains comma-separated state abbreviations.
    state_map = {}
    try:
        fb_conn = mysql.connector.connect(**MYSQL_CONFIG)
        fb_cur = fb_conn.cursor()
        fb_cur.execute("""
            SELECT RepNo, Territory FROM SalesRepMaster
            WHERE Brand = 'BEN' AND Active = 'Y'
              AND ParentRepName NOT LIKE '%DO NOT USE%'
              AND Territory IS NOT NULL AND Territory != ''
        """)
        for rep_no, territory in fb_cur.fetchall():
            rep_name = slsman_map.get(int(rep_no))
            if not rep_name:
                continue
            for state in territory.replace(',', ' ').split():
                state = state.strip().upper()
                if len(state) == 2:
                    state_map[state] = rep_name
        fb_cur.close()
        fb_conn.close()
    except Exception as e:
        log(f"WARNING: Could not build state fallback map ({e})", "WARNING")

    return slsman_map, state_map


def get_model_year_2digit(serial: str) -> str:
    """Return 2-digit model year string from last 2 chars of serial."""
    if serial and len(serial) >= 2 and serial[-2:].isdigit():
        return serial[-2:]
    return datetime.now().strftime('%y')


def get_full_model_year(two_digit: str) -> str:
    if not two_digit:
        return ''
    y = int(two_digit)
    return str(1900 + y) if y >= 90 else str(2000 + y)


# ============================================================================
# MSSQL QUERIES
# ============================================================================

def build_boatoptions_query(db: str) -> str:
    return f"""
WITH BoatOrders AS (
    -- One row per order: prefer ETW boat HIN over engine serials
    SELECT
        coi.co_num,
        coi.site_ref,
        COALESCE(
            MAX(CASE
                WHEN NULLIF(coi.Uf_BENN_BoatSerialNumber, '') LIKE 'ETW%'
                    THEN NULLIF(coi.Uf_BENN_BoatSerialNumber, '')
                WHEN ser.ser_num LIKE 'ETW%'
                    THEN ser.ser_num
                ELSE NULL
            END),
            MAX(NULLIF(coi.Uf_BENN_BoatSerialNumber, '')),
            MAX(ser.ser_num)
        ) AS Uf_BENN_BoatSerialNumber,
        MAX(NULLIF(coi.Uf_BENN_BoatModel, ''))  AS Uf_BENN_BoatModel,
        MAX(NULLIF(coi.config_id, ''))           AS config_id
    FROM [{db}].[dbo].[coitem_mst] coi
    LEFT JOIN [{db}].[dbo].[serial_mst] ser
        ON coi.co_num = ser.ref_num
        AND coi.co_line = ser.ref_line
        AND coi.co_release = ser.ref_release
        AND coi.item = ser.item
        AND coi.site_ref = ser.site_ref
        AND ser.ref_type = 'O'
    LEFT JOIN [{db}].[dbo].[co_mst] co_bo
        ON coi.co_num = co_bo.co_num
        AND coi.site_ref = co_bo.site_ref
    WHERE coi.site_ref = 'BENN'
        AND (
            co_bo.external_confirmation_ref LIKE 'SO%'
            OR TRY_CAST(co_bo.external_confirmation_ref AS BIGINT) IS NOT NULL
        )
        AND (
            (coi.Uf_BENN_BoatSerialNumber IS NOT NULL AND coi.Uf_BENN_BoatSerialNumber != '')
            OR (coi.config_id IS NOT NULL AND coi.config_id != '')
            OR (ser.ser_num IS NOT NULL AND ser.ser_num != '')
        )
    GROUP BY coi.co_num, coi.site_ref
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
    CASE WHEN iim.tax_date IS NOT NULL
         THEN CONVERT(INT, CONVERT(VARCHAR(8), iim.tax_date, 112))
         ELSE NULL
    END                                                 AS [InvoiceDate],
    CAST((coi.price * coi.qty_invoiced) AS DECIMAL(10,2)) AS [ExtSalesAmount],
    LEFT(coi.co_num, 30)                                AS [ERP_OrderNo],
    LEFT(COALESCE(coi.Uf_BENN_BoatSerialNumber, bo.Uf_BENN_BoatSerialNumber), 15) AS [BoatSerialNo],
    LEFT(COALESCE(coi.Uf_BENN_BoatModel, bo.Uf_BENN_BoatModel), 14) AS [BoatModelNo],
    NULL                                                AS [ApplyToNo],
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
    ON coi.co_num = bo.co_num AND coi.site_ref = bo.site_ref
LEFT JOIN (
    -- Get the most recent invoice per line regardless of co_release.
    -- Joining on co_release causes stale data when orders are re-released
    -- after modification: coitem_mst has the new release but inv_item_mst
    -- still holds the original release, so descriptions/prices were wrong.
    SELECT co_num, co_line, site_ref, inv_num, tax_date
    FROM (
        SELECT co_num, co_line, site_ref, inv_num, tax_date,
               ROW_NUMBER() OVER (
                   PARTITION BY co_num, co_line, site_ref
                   ORDER BY tax_date DESC, inv_num DESC
               ) AS rn
        FROM [{db}].[dbo].[inv_item_mst]
    ) ranked
    WHERE rn = 1
) iim ON coi.co_num = iim.co_num AND coi.co_line = iim.co_line
     AND coi.site_ref = iim.site_ref
LEFT JOIN [{db}].[dbo].[co_mst] co
    ON coi.co_num = co.co_num AND coi.site_ref = co.site_ref
LEFT JOIN [{db}].[dbo].[item_mst] im
    ON coi.item = im.item AND coi.site_ref = im.site_ref
LEFT JOIN [{db}].[dbo].[prodcode_mst] pcm
    ON im.Uf_BENN_MaterialCostType = pcm.product_code AND im.site_ref = pcm.site_ref
LEFT JOIN [{db}].[dbo].[serial_mst] ser
    ON coi.co_num = ser.ref_num AND coi.co_line = ser.ref_line
    AND coi.co_release = ser.ref_release AND coi.item = ser.item
    AND coi.site_ref = ser.site_ref AND ser.ref_type = 'O'
WHERE coi.site_ref = 'BENN'
    AND TRY_CAST(co.external_confirmation_ref AS BIGINT) IS NOT NULL
    AND iim.inv_num IS NOT NULL
    AND iim.inv_num NOT LIKE 'CR%'
    AND coi.qty_invoiced > 0
    AND co.co_num NOT LIKE 'WN%'
    AND co.co_num NOT LIKE 'WP%'
    AND co.co_num NOT LIKE 'WW%'
    AND CAST(iim.tax_date AS DATE) = CAST(GETDATE() AS DATE)

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
    CASE WHEN iim.tax_date IS NOT NULL
         THEN CONVERT(INT, CONVERT(VARCHAR(8), iim.tax_date, 112))
         ELSE NULL
    END                                                 AS [InvoiceDate],
    CAST(ISNULL(attr_detail.Uf_BENN_Cfg_Price, 0) AS DECIMAL(10,2)) AS [ExtSalesAmount],
    LEFT(coi.co_num, 30)                                AS [ERP_OrderNo],
    LEFT(ser.ser_num, 15)                               AS [BoatSerialNo],
    LEFT(coi.Uf_BENN_BoatModel, 14)                     AS [BoatModelNo],
    NULL                                                AS [ApplyToNo],
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
    ON coi.config_id = attr_detail.config_id AND coi.site_ref = attr_detail.site_ref
    AND attr_detail.attr_value IS NOT NULL AND attr_detail.print_flag = 'E'
LEFT JOIN [{db}].[dbo].[cfg_comp_mst] ccm
    ON attr_detail.config_id = ccm.config_id AND attr_detail.comp_id = ccm.comp_id
    AND attr_detail.site_ref = ccm.site_ref
LEFT JOIN (
    SELECT co_num, co_line, site_ref, inv_num, tax_date
    FROM (
        SELECT co_num, co_line, site_ref, inv_num, tax_date,
               ROW_NUMBER() OVER (
                   PARTITION BY co_num, co_line, site_ref
                   ORDER BY tax_date DESC, inv_num DESC
               ) AS rn
        FROM [{db}].[dbo].[inv_item_mst]
    ) ranked
    WHERE rn = 1
) iim ON coi.co_num = iim.co_num AND coi.co_line = iim.co_line
     AND coi.site_ref = iim.site_ref
LEFT JOIN [{db}].[dbo].[co_mst] co
    ON coi.co_num = co.co_num AND coi.site_ref = co.site_ref
LEFT JOIN [{db}].[dbo].[item_mst] im
    ON coi.item = im.item AND coi.site_ref = im.site_ref
LEFT JOIN [{db}].[dbo].[serial_mst] ser
    ON coi.co_num = ser.ref_num AND coi.co_line = ser.ref_line
    AND coi.co_release = ser.ref_release AND coi.item = ser.item
    AND coi.site_ref = ser.site_ref AND ser.ref_type = 'O'
WHERE coi.config_id IS NOT NULL
    AND coi.site_ref = 'BENN'
    AND co.external_confirmation_ref LIKE 'SO%'
    AND iim.inv_num NOT LIKE 'CR%'
    AND coi.qty_invoiced > 0
    AND co.co_num NOT LIKE 'WN%'
    AND co.co_num NOT LIKE 'WP%'
    AND co.co_num NOT LIKE 'WW%'
    AND CAST(iim.tax_date AS DATE) = CAST(GETDATE() AS DATE)

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
WHERE [ERP_OrderNo] IN (
    SELECT DISTINCT [ERP_OrderNo]
    FROM OrderedRows
    WHERE [ItemMasterMCT] IN ('BOA', 'BOI')
)
ORDER BY [ERP_OrderNo], [LineSeqNo]
"""


def build_serial_master_query(db: str) -> str:
    return f"""
    SELECT DISTINCT
        COALESCE(NULLIF(coi.Uf_BENN_BoatSerialNumber, ''), ser.ser_num) AS BoatSerialNo,
        coi.item                                AS BoatItemNo,
        coi.description                         AS BoatDesc1,
        im.Uf_BENN_Series                       AS Series,
        coi.co_num                              AS ERP_OrderNo,
        LEFT(coi.Uf_BENN_BoatWebOrderNumber, 30) AS WebOrderNo,
        iim.inv_num                             AS InvoiceNo,
        LEFT(LTRIM(RTRIM(ISNULL(iim.apply_num, iim.inv_num))), 30) AS ApplyToNo,
        LEFT(co.orig_order_type, 1)             AS OrigOrderType,
        CASE WHEN iim.tax_date IS NOT NULL
            THEN CONVERT(INT, CONVERT(VARCHAR(8), iim.tax_date, 112))
            ELSE NULL
        END                                     AS InvoiceDate,
        co.cust_num                             AS DealerNumber,
        cust.name                               AS DealerName,
        cust.city                               AS DealerCity,
        cust.state                              AS DealerState,
        cust.zip                                AS DealerZip,
        cust.country                            AS DealerCountry,
        coi.Uf_BENN_BoatModel                   AS BoatModelNo,
        co.order_date                           AS OrderDate,
        co.Uf_BENN_ProductionNumber             AS ProdNo,
        co.Uf_BENN_BenningtonOwned              AS BenningtonOwned,
        coi.Uf_BENN_PannelColor                 AS PanelColor,
        coi.Uf_BENN_BaseVnyl                    AS BaseVinyl,
        coi.Uf_BENN_PreSold                     AS Presold,
        coi.qty_invoiced                        AS Quantity,
        coi.config_id                           AS ConfigId,
        co.external_confirmation_ref            AS SoNumber,
        co.slsman                               AS SlsMan
    FROM [{db}].[dbo].[coitem_mst] coi
    LEFT JOIN [{db}].[dbo].[serial_mst] ser
        ON coi.co_num = ser.ref_num
        AND coi.co_line = ser.ref_line
        AND coi.co_release = ser.ref_release
        AND coi.item = ser.item
        AND coi.site_ref = ser.site_ref
        AND ser.ref_type = 'O'
    INNER JOIN [{db}].[dbo].[inv_item_mst] iim
        ON coi.co_num = iim.co_num
        AND coi.co_line = iim.co_line
        AND coi.co_release = iim.co_release
        AND coi.site_ref = iim.site_ref
    INNER JOIN [{db}].[dbo].[co_mst] co
        ON coi.co_num = co.co_num
        AND coi.site_ref = co.site_ref
    LEFT JOIN [{db}].[dbo].[item_mst] im
        ON coi.item = im.item
        AND coi.site_ref = im.site_ref
    LEFT JOIN [{db}].[dbo].[custaddr_mst] cust
        ON co.cust_num = cust.cust_num
        AND co.site_ref = cust.site_ref
        AND cust.cust_seq = 0
    WHERE coi.site_ref = 'BENN'
        AND im.Uf_BENN_MaterialCostType IN ('BOA', 'BOI')
        AND (
            co.external_confirmation_ref LIKE 'SO%'
            OR TRY_CAST(co.external_confirmation_ref AS BIGINT) IS NOT NULL
        )
        AND (
            (coi.Uf_BENN_BoatSerialNumber IS NOT NULL AND coi.Uf_BENN_BoatSerialNumber != '')
            OR ser.ser_num IS NOT NULL
        )
        AND iim.inv_num IS NOT NULL
        AND iim.inv_num NOT LIKE 'CR%'
        AND coi.qty_invoiced > 0
        AND co.co_num NOT LIKE 'WN%'
        AND co.co_num NOT LIKE 'WP%'
        AND co.co_num NOT LIKE 'WW%'
        AND CAST(iim.tax_date AS DATE) = CAST(GETDATE() AS DATE)
    ORDER BY BoatSerialNo
    """


def fetch_color_attrs(config_ids: set, db: str) -> dict:
    """Fetch color/config attributes from cfg_attr_mst for CPQ boats."""
    if not config_ids:
        return {}

    conn = pymssql.connect(**MSSQL_CONFIG)
    cursor = conn.cursor(as_dict=True)
    config_colors: dict = {}
    id_list = list(config_ids)

    for i in range(0, len(id_list), 500):
        batch = id_list[i:i + 500]
        placeholders = ','.join(['%s'] * len(batch))
        cursor.execute(f"""
            SELECT config_id, attr_name, attr_value
            FROM [{db}].[dbo].[cfg_attr_mst]
            WHERE config_id IN ({placeholders})
                AND site_ref = 'BENN'
                AND attr_value IS NOT NULL AND attr_value != ''
                AND (
                    attr_name LIKE '%Accent Panel%'
                    OR attr_name LIKE '%Color Package%'
                    OR attr_name LIKE '%Trim Accent%'
                    OR attr_name LIKE '%Vinyl%'
                    OR attr_name = 'PANEL COLOR'
                )
        """, tuple(batch))

        for row in cursor.fetchall():
            cid = row['config_id']
            attr = (row.get('attr_name') or '').upper()
            val  = row.get('attr_value')
            if cid not in config_colors:
                config_colors[cid] = {
                    'AccentPanel': None, 'ColorPackage': None,
                    'TrimAccent': None, 'PanelColor_cfg': None,
                    'BaseVinyl': None
                }
            if 'ACCENT PANEL' in attr:
                config_colors[cid]['AccentPanel'] = val
            elif 'COLOR PACKAGE' in attr:
                config_colors[cid]['ColorPackage'] = val
            elif 'TRIM ACCENT' in attr:
                config_colors[cid]['TrimAccent'] = val
            elif 'VINYL' in attr:
                config_colors[cid]['BaseVinyl'] = val
            elif attr == 'PANEL COLOR':
                config_colors[cid]['PanelColor_cfg'] = val

    cursor.close()
    conn.close()
    log(f"Fetched color attributes for {len(config_colors)} configured boats")
    return config_colors


def fetch_color_attrs_from_boatoptions(serial_numbers: list, mysql_conn) -> dict:
    """
    Fetch color attributes from BoatOptions{YY} line items for legacy boats.
    EOS stores color values in ItemDesc1 with category prefixes like:
    - 'PANEL ACCENT GEMINI BLACK SMTH' -> AccentPanel
    - 'TRIM ACCENT IRONWOOD SV S' -> TrimAccent
    - 'BLACKOUT LUXE M' -> ColorPackage
    
    Returns dict: {serial_number: {'PanelColor': '...', 'AccentPanel': '...', 'TrimAccent': '...', 'ColorPackage': '...'}}
    """
    if not serial_numbers:
        return {}
    
    cursor = mysql_conn.cursor()
    serial_colors = {}
    
    # Group serials by model year to query correct BoatOptions table
    serials_by_year = {}
    for serial in serial_numbers:
        year = detect_model_year(serial)
        table = get_table_for_year(year)
        serials_by_year.setdefault(table, []).append(serial)
    
    for table, serials in serials_by_year.items():
        try:
            # Check if table exists
            cursor.execute(f"""
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = '{MYSQL_DB}' AND table_name = '{table}'
            """)
            if not cursor.fetchone():
                continue
            
            # Query for color line items
            placeholders = ','.join(['%s'] * len(serials))
            cursor.execute(f"""
                SELECT BoatSerialNo, ItemMasterProdCat, ItemMasterMCT, ItemDesc1, CfgName, ItemNo
                FROM {MYSQL_DB}.{table}
                WHERE BoatSerialNo IN ({placeholders})
                    AND (
                        CfgName IN ('baseVinyl','panelColor','accentPanelColor','trim','anodizing')
                        OR ItemDesc1 LIKE 'PANEL ACCENT%'
                        OR ItemDesc1 LIKE 'TRIM ACCENT%'
                        OR ItemDesc1 LIKE 'BASE VINYL%'
                        OR ItemDesc1 LIKE 'VINYL BASE%'
                        OR ItemDesc1 LIKE 'COLOR PACKAGE%'
                        OR ItemDesc1 LIKE 'BLACKOUT LUXE%'
                        OR ItemMasterProdCat IN ('H3A', 'H3T', 'H3P')
                        OR ItemMasterMCT IN ('H3A', 'H3T', 'H3P', 'A0V')
                        OR (ItemMasterProdCat = 'ACC' AND ItemNo IN (
                            'PANEL COLOR', 'ACCENT PANEL CO', 'BASE VINYL',
                            'Trim Accents', 'Exterior Color '
                        ))
                    )
            """, tuple(serials))

            for row in cursor.fetchall():
                serial  = row[0]
                cat     = (row[1] or '').upper()
                mct     = (row[2] or '').upper()
                desc    = (row[3] or '').strip()
                cfgname = (row[4] or '').lower()
                itemno  = (row[5] or '').strip()

                if serial not in serial_colors:
                    serial_colors[serial] = {
                        'PanelColor': None, 'AccentPanel': None,
                        'TrimAccent': None, 'ColorPackage': None, 'BaseVinyl': None
                    }

                desc_upper = desc.upper()
                itemno_upper = itemno.upper()

                # ACC-format rows (OrigOrderType='O' boats): ItemNo identifies the field,
                # ItemDesc1 is the clean value
                if cat == 'ACC' and itemno_upper == 'PANEL COLOR':
                    serial_colors[serial]['PanelColor'] = desc
                elif cat == 'ACC' and itemno_upper.startswith('ACCENT PANEL'):
                    serial_colors[serial]['AccentPanel'] = desc
                elif cat == 'ACC' and itemno_upper == 'BASE VINYL':
                    serial_colors[serial]['BaseVinyl'] = desc
                elif cat == 'ACC' and itemno_upper.startswith('TRIM ACCENT'):
                    serial_colors[serial]['TrimAccent'] = desc
                elif cat == 'ACC' and itemno_upper.startswith('EXTERIOR COLOR'):
                    serial_colors[serial]['ColorPackage'] = desc
                # CPQ boats: CfgName → ItemDesc1 is already the clean human-readable value
                elif cfgname == 'basevinyl':
                    serial_colors[serial]['BaseVinyl'] = desc
                elif cfgname == 'panelcolor':
                    serial_colors[serial]['PanelColor'] = desc
                elif cfgname == 'accentpanelcolor':
                    serial_colors[serial]['AccentPanel'] = desc
                elif cfgname == 'trim':
                    serial_colors[serial]['TrimAccent'] = desc
                elif cfgname == 'anodizing':
                    serial_colors[serial]['ColorPackage'] = desc
                # Legacy boats: ItemDesc1 includes category prefix — strip it
                elif 'BASE VINYL' in desc_upper or 'VINYL BASE' in desc_upper or mct == 'A0V':
                    for prefix in ('BASE VINYL', 'VINYL BASE'):
                        if desc_upper.startswith(prefix):
                            desc = desc[len(prefix):].strip()
                            break
                    serial_colors[serial]['BaseVinyl'] = desc
                elif 'PANEL ACCENT' in desc_upper:
                    serial_colors[serial]['AccentPanel'] = desc.replace('PANEL ACCENT', '').strip()
                elif 'TRIM ACCENT' in desc_upper:
                    serial_colors[serial]['TrimAccent'] = desc.replace('TRIM ACCENT', '').strip()
                elif 'COLOR PACKAGE' in desc_upper:
                    serial_colors[serial]['ColorPackage'] = desc.replace('COLOR PACKAGE', '').strip()
                elif desc:
                    if cat == 'H3P' or mct == 'H3P' or 'LUXE' in desc_upper:
                        serial_colors[serial]['ColorPackage'] = desc
                    elif cat == 'H3A' or mct == 'H3A':
                        serial_colors[serial]['AccentPanel'] = desc
                    elif cat == 'H3T' or mct == 'H3T':
                        serial_colors[serial]['TrimAccent'] = desc
                        
        except Exception as e:
            log(f"Error querying {table} for colors: {e}", "WARNING")
            continue
    
    cursor.close()
    populated = sum(1 for v in serial_colors.values() if any(v.values()))
    log(f"Fetched color attributes from BoatOptions for {populated} boats")
    return serial_colors


import re as _re

_LIQUIFIRE_BASE = "https://polarismarine.liquifire.com/polarismarine"

def _is_valid_liquifire_image(url: str) -> bool:
    """Returns True if the URL yields a real image (JPEG, >10KB)."""
    try:
        r = requests.get(url, verify=False, timeout=10)
        return (r.status_code == 200
                and 'jpeg' in r.headers.get('Content-Type', '')
                and len(r.content) > 10000)
    except Exception:
        return False


def _normalize_liquifire_url(url: str, item_no: str = '') -> str:
    """
    Validate and normalize a Liquifire URL from CPQ.
    Cycle through fallbacks until a real JPEG is returned:
      1. cat[orthographic] with original asset/view
      2. cat[pon] with original asset/view
      3. swap asset+view to item_no/side, keep all color params  ← configured colors
      4. cat[pon], asset[{item_no}], view[side]   ← bare hull fallback
      5. cat[pon], asset[{item_no}], view[]        ← last resort
    Liquifire returns a tiny GIF (~3-4KB) for invalid combinations.
    If CPQ returns a non-Liquifire URL (e.g. configurator.inforcloudsuite.com),
    skip straight to the item_no fallbacks.
    """
    cpq_model = ''
    if 'liquifire.com' not in url:
        # Not a Liquifire URL (e.g. configurator.inforcloudsuite.com).
        # Extract the model name from the filename (e.g. HighRes2026_23MSB.png → 23MSB)
        # so we can try it in Liquifire before falling back to the EOS item_no.
        m = _re.search(r'HighRes\d+_([A-Za-z0-9]+)\.png', url)
        if m:
            cpq_model = m.group(1)
        url = f"{_LIQUIFIRE_BASE}?set=cat[pon],asset[],view[]&call=url[file:PS/main]&sink"

    # If the CPQ URL is a furniture swatch (asset[furn_*]) and we have an item_no,
    # skip the original-URL candidates entirely — they'll just render a furniture image
    # that happens to be large enough to pass the >20KB size check.
    is_furn_url = 'asset[furn_' in url
    if is_furn_url and item_no:
        candidates = []
    else:
        candidates = [
            _re.sub(r'cat\[[^\]]*\]', 'cat[orthographic]', url),
            _re.sub(r'cat\[[^\]]*\]', 'cat[pon]', url),
        ]
    if item_no:
        # Keep all color params from the CPQ URL but fix asset and view —
        # handles cases where CPQ returns a furniture swatch (asset[furn_*], view[])
        # instead of the boat hull image.
        configured_url = _re.sub(r'asset\[[^\]]*\]', f'asset[{item_no}]', url)
        configured_url = _re.sub(r'view\[[^\]]*\]', 'view[side]', configured_url)
        configured_url = _re.sub(r'cat\[[^\]]*\]', 'cat[pon]', configured_url)
        candidates += [
            configured_url,
            f"{_LIQUIFIRE_BASE}?set=cat[pon],asset[{item_no}],view[side]&call=url[file:PS/main]&sink",
            f"{_LIQUIFIRE_BASE}?set=cat[pon],asset[{item_no}],view[]&call=url[file:PS/main]&sink",
        ]
        # Some EOS item numbers have a middle digit Liquifire doesn't use (e.g. 23M1SB → 23MSB).
        # Strip a single digit between the series letters and try those variants too.
        stripped_no = _re.sub(r'^(\d{2}[A-Za-z]+)\d([A-Za-z].*)$', r'\1\2', item_no)
        if stripped_no != item_no:
            stripped_configured = _re.sub(r'asset\[[^\]]*\]', f'asset[{stripped_no}]', url)
            stripped_configured = _re.sub(r'view\[[^\]]*\]', 'view[side]', stripped_configured)
            stripped_configured = _re.sub(r'cat\[[^\]]*\]', 'cat[pon]', stripped_configured)
            candidates += [
                stripped_configured,
                f"{_LIQUIFIRE_BASE}?set=cat[pon],asset[{stripped_no}],view[side]&call=url[file:PS/main]&sink",
            ]

    # If CPQ returned a configurator URL with a model name, try that in Liquifire first
    if cpq_model:
        candidates += [
            f"{_LIQUIFIRE_BASE}?set=cat[pon],asset[{cpq_model}],view[side]&call=url[file:PS/main]&sink",
        ]

    for candidate in candidates:
        if _is_valid_liquifire_image(candidate):
            return candidate

    # Nothing worked — return the cat[pon] version as best effort
    return _re.sub(r'cat\[[^\]]*\]', 'cat[pon]', url)


def fetch_cpq_image_urls(so_numbers: list, config_id_map: dict = None,
                         itemno_map: dict = None) -> dict:
    """
    For each SO number (CPQ boats), fetch LastConfigurationImageLink from
    CPQ CPQEQ OrderLine entity (PRD environment).
    Falls back to querying by ConfigurationId when ExternalId lookup returns nothing
    (e.g. orders with non-standard SO numbers like SOORE000001).
    If the CPQ URL is invalid (e.g. furniture swatch instead of boat image),
    cycles through fallback Liquifire URLs using the BoatItemNo.
    Returns dict: {so_number: image_url}
    """
    if not so_numbers:
        return {}
    if config_id_map is None:
        config_id_map = {}
    if itemno_map is None:
        itemno_map = {}

    try:
        resp = requests.post(load_cpq_data.TOKEN_ENDPOINT_PRD, data={
            'grant_type':    'password',
            'client_id':     load_cpq_data.CLIENT_ID_PRD,
            'client_secret': load_cpq_data.CLIENT_SECRET_PRD,
            'username':      load_cpq_data.SERVICE_KEY_PRD,
            'password':      load_cpq_data.SERVICE_SECRET_PRD,
        }, verify=False, timeout=30)
        token = resp.json()['access_token']
    except Exception as e:
        log(f"CPQ auth failed — skipping image URL fetch: {e}", "WARNING")
        return {}

    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
    eq_base = ('https://mingle-ionapi.inforcloudsuite.com'
               '/QA2FNBZCKUAUH7QB_PRD/CPQEQ/RuntimeApi/EnterpriseQuoting/Entities')

    image_urls: dict = {}
    for so in so_numbers:
        try:
            # Primary: look up order by ExternalId (standard SO00xxxxxx format)
            r = requests.get(f"{eq_base}/Order",
                             params={'$filter': f"ExternalId eq '{so}'", '$top': 1},
                             headers=headers, verify=False, timeout=30)
            if r.status_code == 200:
                items = r.json().get('items', [])
                if items:
                    order_id = items[0]['Id']
                    r2 = requests.get(f"{eq_base}/OrderLine",
                                      params={'$filter': f"Order eq '{order_id}'", '$top': 50},
                                      headers=headers, verify=False, timeout=30)
                    if r2.status_code == 200:
                        for line in r2.json().get('items', []):
                            url = line.get('LastConfigurationImageLink')
                            if url:
                                image_urls[so] = _normalize_liquifire_url(url, itemno_map.get(so, ''))
                                break
                    if so in image_urls:
                        continue

            # Fallback: query OrderLine directly by ConfigurationId
            # Handles orders with non-standard external refs (SOORE*, SONKF*, etc.)
            config_id = config_id_map.get(so)
            if config_id:
                r3 = requests.get(f"{eq_base}/OrderLine",
                                  params={'$filter': f"ConfigurationId eq '{config_id}'", '$top': 10},
                                  headers=headers, verify=False, timeout=30)
                if r3.status_code == 200:
                    for line in r3.json().get('items', []):
                        url = line.get('LastConfigurationImageLink')
                        if url:
                            image_urls[so] = _normalize_liquifire_url(url, itemno_map.get(so, ''))
                            log(f"Image found via ConfigurationId fallback for {so} ({config_id})")
                            break
                else:
                    log(f"ConfigurationId fallback returned {r3.status_code} for {so}", "WARNING")

        except Exception as e:
            log(f"CPQ image fetch failed for {so}: {e}", "WARNING")

    log(f"Fetched CPQ image URLs for {len(image_urls)}/{len(so_numbers)} orders")
    return image_urls


def ensure_snm_image_column(conn) -> None:
    """Add LiquifireImageUrl column to SerialNumberMaster if not already present."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            f"ALTER TABLE {MYSQL_DB}.SerialNumberMaster "
            "ADD COLUMN LiquifireImageUrl VARCHAR(2000) DEFAULT NULL"
        )
        conn.commit()
        log(f"Added LiquifireImageUrl column to {MYSQL_DB}.SerialNumberMaster")
    except Exception:
        pass  # column already exists — that's fine
    cursor.close()


# ============================================================================
# STEP 1 — BOATOPTIONS LOAD
# ============================================================================

def deduplicate_rows(rows: List[Dict]) -> List[Dict]:
    seen: dict = {}
    for row in rows:
        key = (row.get('BoatSerialNo', ''), row.get('ItemNo', ''),
               row.get('LineNo', 0), row.get('LineSeqNo', 0))
        if key in seen:
            if row.get('ItemMasterProdCat') == 'ACC' and seen[key].get('ItemMasterProdCat') != 'ACC':
                seen[key] = row
        else:
            seen[key] = row
    return list(seen.values())


def group_by_table(rows: List[Dict]) -> Dict[str, List[Dict]]:
    groups: Dict[str, List[Dict]] = {}
    year_counts: Dict[int, int] = {}
    for row in rows:
        year  = detect_model_year(row.get('BoatSerialNo'))
        table = f'{MYSQL_DB}.{get_table_for_year(year)}'
        groups.setdefault(table, []).append(row)
        year_counts[year] = year_counts.get(year, 0) + 1

    log("Rows grouped by table:")
    for t in sorted(groups):
        log(f"  {t}: {len(groups[t]):,} rows")
    log("Rows by model year:")
    for yr in sorted(year_counts):
        log(f"  {yr}: {year_counts[yr]:,} rows")
    return groups


def load_boatoptions_batch(rows: List[Dict], table_name: str, conn) -> int:
    original = len(rows)
    rows = deduplicate_rows(rows)
    if len(rows) < original:
        log(f"Deduplicated {original - len(rows)} rows for {table_name}")

    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    initial = cursor.fetchone()[0]

    insert_sql = f"""
    INSERT INTO {table_name} (
        ERP_OrderNo, BoatSerialNo, BoatModelNo, LineNo, ItemNo, ItemDesc1,
        ExtSalesAmount, QuantitySold, Series, WebOrderNo, Orig_Ord_Type,
        ApplyToNo, InvoiceNo, InvoiceDate, ItemMasterProdCat, ItemMasterProdCatDesc,
        ItemMasterMCT, MCTDesc, LineSeqNo, ConfigID, ValueText,
        OptionSerialNo, C_Series, order_date, external_confirmation_ref,
        MSRP, CfgName, CfgPage, CfgScreen, CfgValue, CfgAttrType
    ) VALUES (
        %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
    )
    ON DUPLICATE KEY UPDATE
        BoatModelNo=VALUES(BoatModelNo), ItemDesc1=VALUES(ItemDesc1),
        ExtSalesAmount=VALUES(ExtSalesAmount), QuantitySold=VALUES(QuantitySold),
        Series=VALUES(Series), WebOrderNo=VALUES(WebOrderNo),
        Orig_Ord_Type=VALUES(Orig_Ord_Type), ApplyToNo=VALUES(ApplyToNo),
        InvoiceNo=VALUES(InvoiceNo), InvoiceDate=VALUES(InvoiceDate),
        ItemMasterProdCat=VALUES(ItemMasterProdCat),
        ItemMasterProdCatDesc=VALUES(ItemMasterProdCatDesc),
        ItemMasterMCT=VALUES(ItemMasterMCT), MCTDesc=VALUES(MCTDesc),
        ConfigID=VALUES(ConfigID), ValueText=VALUES(ValueText),
        OptionSerialNo=VALUES(OptionSerialNo), C_Series=VALUES(C_Series),
        order_date=VALUES(order_date),
        external_confirmation_ref=VALUES(external_confirmation_ref),
        MSRP=VALUES(MSRP), CfgName=VALUES(CfgName), CfgPage=VALUES(CfgPage),
        CfgScreen=VALUES(CfgScreen), CfgValue=VALUES(CfgValue), CfgAttrType=VALUES(CfgAttrType)
    """

    for i in range(0, len(rows), 1000):
        batch = rows[i:i + 1000]
        data  = []
        for row in batch:
            prod_cat = row.get('ItemMasterProdCat')
            mct      = row.get('ItemMasterMCT')
            if prod_cat == 'BS1' and mct == 'STD':
                prod_cat = 'ACC'
            # Items not in item_mst (NULL MCT) with a price are accessories
            if not mct and (row.get('ExtSalesAmount') or 0) > 0:
                mct      = 'ACC'
                prod_cat = prod_cat or 'ACC'
            boat_model_no = row.get('BoatModelNo')
            if not boat_model_no and mct in ('BOA', 'BOI'):
                boat_model_no = row.get('ItemNo')
            
            data.append((
                row.get('ERP_OrderNo'), row.get('BoatSerialNo'), boat_model_no,
                row.get('LineNo'), row.get('ItemNo'), row.get('ItemDesc1'),
                row.get('ExtSalesAmount'), row.get('QuantitySold'),
                row.get('Series') or row.get('C_Series') or _series_from_model(boat_model_no),
                row.get('WebOrderNo'), row.get('Orig_Ord_Type'), row.get('ApplyToNo'),
                row.get('InvoiceNo'), row.get('InvoiceDate'), prod_cat,
                row.get('ItemMasterProdCatDesc'), row.get('ItemMasterMCT'),
                row.get('MCTDesc'), row.get('LineSeqNo'), row.get('ConfigID'),
                row.get('ValueText'), row.get('OptionSerialNo'), row.get('C_Series'),
                row.get('order_date'), row.get('external_confirmation_ref'),
                row.get('MSRP'), row.get('CfgName'), row.get('CfgPage'),
                row.get('CfgScreen'), row.get('CfgValue'), row.get('CfgAttrType')
            ))
        cursor.executemany(insert_sql, data)
        conn.commit()

    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    final = cursor.fetchone()[0]
    log(f"Loaded {len(rows):,} rows into {table_name} (was {initial:,}, now {final:,})", "SUCCESS")
    cursor.close()
    return final


# ============================================================================
def _series_from_model(model: str) -> str:
    """Extract Bennington series from model name when Uf_BENN_Series is NULL.
    Model format: {2-digit-year}{series}{floorplan}, e.g. '23M1SB' -> 'M1', '22SSB' -> 'S'
    """
    if not model:
        return ''
    suffix = model[2:] if len(model) > 2 and model[:2].isdigit() else model
    for s in ('LXS', 'QX', 'SV', 'SX', 'M1', 'M2', 'M3', 'Q', 'R', 'S', 'L', 'M'):
        if suffix.startswith(s):
            return s
    return ''


# STEP 1b — MISSING ENGINE BACKFILL
# ============================================================================

def build_missing_engines_query(db: str, so_numbers: List[str]) -> str:
    """
    For a given list of SO numbers imported today, fetch any engine lines
    that were invoiced on a different date (and thus missed by the main query).
    Uses the same BoatOrders CTE to assign the correct BoatSerialNo.
    """
    placeholders = ','.join(f"'{so}'" for so in so_numbers)
    return f"""
WITH BoatOrders AS (
    SELECT
        coi.co_num,
        coi.site_ref,
        COALESCE(
            MAX(CASE
                WHEN NULLIF(coi.Uf_BENN_BoatSerialNumber, '') LIKE 'ETW%'
                    THEN NULLIF(coi.Uf_BENN_BoatSerialNumber, '')
                WHEN ser.ser_num LIKE 'ETW%'
                    THEN ser.ser_num
                ELSE NULL
            END),
            MAX(NULLIF(coi.Uf_BENN_BoatSerialNumber, '')),
            MAX(ser.ser_num)
        ) AS Uf_BENN_BoatSerialNumber,
        MAX(NULLIF(coi.Uf_BENN_BoatModel, '')) AS Uf_BENN_BoatModel
    FROM [{db}].[dbo].[coitem_mst] coi
    LEFT JOIN [{db}].[dbo].[serial_mst] ser
        ON coi.co_num = ser.ref_num
        AND coi.co_line = ser.ref_line
        AND coi.co_release = ser.ref_release
        AND coi.item = ser.item
        AND coi.site_ref = ser.site_ref
        AND ser.ref_type = 'O'
    LEFT JOIN [{db}].[dbo].[co_mst] co_bo
        ON coi.co_num = co_bo.co_num
        AND coi.site_ref = co_bo.site_ref
    WHERE coi.site_ref = 'BENN'
        AND coi.co_num IN ({placeholders})
    GROUP BY coi.co_num, coi.site_ref
)
SELECT
    LEFT(coi.Uf_BENN_BoatWebOrderNumber, 30)             AS [WebOrderNo],
    LEFT(im.Uf_BENN_Series, 5)                           AS [C_Series],
    -- Use qty_ordered for engines not yet invoiced (drop-ship pending)
    COALESCE(NULLIF(coi.qty_invoiced, 0), coi.qty_ordered) AS [QuantitySold],
    LEFT(co.type, 1)                                     AS [Orig_Ord_Type],
    LEFT(ser.ser_num, 12)                                AS [OptionSerialNo],
    COALESCE(pcm.description, 'Engine')                  AS [MCTDesc],
    coi.co_line                                          AS [LineSeqNo],
    coi.co_line                                          AS [LineNo],
    LEFT(coi.item, 15)                                   AS [ItemNo],
    NULL                                                 AS [ItemMasterProdCatDesc],
    LEFT(im.Uf_BENN_ProductCategory, 3)                  AS [ItemMasterProdCat],
    LEFT(im.Uf_BENN_MaterialCostType, 10)                AS [ItemMasterMCT],
    LEFT(coi.description, 100)                           AS [ItemDesc1],
    LEFT(LTRIM(RTRIM(iim.inv_num)), 30)                  AS [InvoiceNo],
    CASE WHEN iim.tax_date IS NOT NULL
         THEN CONVERT(INT, CONVERT(VARCHAR(8), iim.tax_date, 112))
         ELSE NULL
    END                                                  AS [InvoiceDate],
    CAST((coi.price * COALESCE(NULLIF(coi.qty_invoiced, 0), coi.qty_ordered)) AS DECIMAL(10,2)) AS [ExtSalesAmount],
    LEFT(coi.co_num, 30)                                 AS [ERP_OrderNo],
    LEFT(COALESCE(coi.Uf_BENN_BoatSerialNumber, bo.Uf_BENN_BoatSerialNumber), 15) AS [BoatSerialNo],
    LEFT(COALESCE(coi.Uf_BENN_BoatModel, bo.Uf_BENN_BoatModel), 14) AS [BoatModelNo],
    NULL                                                 AS [ApplyToNo],
    ''                                                   AS [ConfigID],
    ''                                                   AS [ValueText],
    co.order_date                                        AS [order_date],
    co.external_confirmation_ref                         AS [external_confirmation_ref],
    NULL AS [MSRP], NULL AS [CfgName], NULL AS [CfgPage],
    NULL AS [CfgScreen], NULL AS [CfgValue], NULL AS [CfgAttrType]
FROM [{db}].[dbo].[coitem_mst] coi
INNER JOIN BoatOrders bo
    ON coi.co_num = bo.co_num AND coi.site_ref = bo.site_ref
LEFT JOIN (
    SELECT co_num, co_line, site_ref, inv_num, tax_date
    FROM (
        SELECT co_num, co_line, site_ref, inv_num, tax_date,
               ROW_NUMBER() OVER (
                   PARTITION BY co_num, co_line, site_ref
                   ORDER BY tax_date DESC, inv_num DESC
               ) AS rn
        FROM [{db}].[dbo].[inv_item_mst]
    ) ranked
    WHERE rn = 1
) iim ON coi.co_num = iim.co_num AND coi.co_line = iim.co_line
     AND coi.site_ref = iim.site_ref
LEFT JOIN [{db}].[dbo].[co_mst] co
    ON coi.co_num = co.co_num AND coi.site_ref = co.site_ref
LEFT JOIN [{db}].[dbo].[item_mst] im
    ON coi.item = im.item AND coi.site_ref = im.site_ref
LEFT JOIN [{db}].[dbo].[prodcode_mst] pcm
    ON im.Uf_BENN_MaterialCostType = pcm.product_code AND im.site_ref = pcm.site_ref
LEFT JOIN [{db}].[dbo].[serial_mst] ser
    ON coi.co_num = ser.ref_num AND coi.co_line = ser.ref_line
    AND coi.co_release = ser.ref_release AND coi.item = ser.item
    AND coi.site_ref = ser.site_ref AND ser.ref_type = 'O'
WHERE coi.site_ref = 'BENN'
    AND coi.co_num IN ({placeholders})
    AND im.Uf_BENN_MaterialCostType = 'ENG'
    AND coi.qty_ordered > 0
    AND iim.inv_num NOT LIKE 'CR%'
ORDER BY coi.co_num, coi.co_line
"""


def backfill_missing_engines(so_numbers: List[str], mysql_conn) -> int:
    """
    For today's imported SOs, check MSSQL for engine lines that were invoiced
    on a different date and therefore missed by the main daily import query.
    Only inserts engines not already present in MySQL.
    """
    if not so_numbers:
        return 0

    # Fetch engine rows from MSSQL for today's SOs
    mssql_conn = pymssql.connect(**MSSQL_CONFIG)
    cursor = mssql_conn.cursor(as_dict=True)
    cursor.execute(build_missing_engines_query(MSSQL_DB, so_numbers))
    engine_rows = cursor.fetchall()
    cursor.close()
    mssql_conn.close()

    if not engine_rows:
        log("No engine rows found for today's SOs in MSSQL")
        return 0

    log(f"Found {len(engine_rows)} engine row(s) in MSSQL for today's SOs")

    # Check which engines are already in MySQL to avoid duplicates
    mysql_cursor = mysql_conn.cursor()
    new_rows = []
    for row in engine_rows:
        serial = row.get('BoatSerialNo') or ''
        item   = row.get('ItemNo') or ''
        so     = row.get('ERP_OrderNo') or ''
        line   = row.get('LineNo') or 0
        if not serial or not item:
            continue
        year  = detect_model_year(serial)
        table = f"{MYSQL_DB}.{get_table_for_year(year)}"
        mysql_cursor.execute(
            f"SELECT 1 FROM {table} WHERE BoatSerialNo=%s AND ItemNo=%s AND ERP_OrderNo=%s AND LineNo=%s LIMIT 1",
            (serial, item, so, line)
        )
        if not mysql_cursor.fetchone():
            new_rows.append(row)

    mysql_cursor.close()

    if not new_rows:
        log("All engine rows already present in MySQL — nothing to backfill")
        return 0

    # Look up dealer info for each boat being backfilled
    serials = list({r.get('BoatSerialNo') for r in new_rows if r.get('BoatSerialNo')})
    dealer_map = {}
    if serials:
        dl_cursor = mysql_conn.cursor()
        fmt = ','.join(['%s'] * len(serials))
        dl_cursor.execute(
            f"SELECT Boat_SerialNo, DealerName, DealerNumber FROM {MYSQL_DB}.SerialNumberMaster "
            f"WHERE Boat_SerialNo IN ({fmt})",
            serials
        )
        for sn, dname, dnum in dl_cursor.fetchall():
            dealer_map[sn] = (dname or '', dnum or '')
        dl_cursor.close()

    log(f"Backfilling {len(new_rows)} missing engine row(s):")
    for r in new_rows:
        sn      = r.get('BoatSerialNo', '')
        so      = r.get('ERP_OrderNo', '')
        desc    = r.get('ItemDesc1', '')
        item    = r.get('ItemNo', '')
        dname, dnum = dealer_map.get(sn, ('', ''))
        log(f"  Engine backfilled: SO={so}  Boat={sn}  Engine={item} ({desc})  Dealer={dname} ({dnum})")

    table_groups = group_by_table(new_rows)
    inserted = 0
    for table_name, rows in table_groups.items():
        load_boatoptions_batch(rows, table_name, mysql_conn)
        inserted += len(rows)

    log(f"Engine backfill complete — {inserted} row(s) inserted", "SUCCESS")
    return inserted


# ============================================================================
# STEP 1c — SWEEP: ALL BOATS MISSING ENGINES (LOOKBACK WINDOW)
# ============================================================================

def find_sos_missing_engines(mysql_conn, lookback_days: int = 180) -> List[tuple]:
    """
    Query MySQL for all (ERP_OrderNo, BoatSerialNo) pairs in BoatOptions26
    that have a BOA row but no ENG row, within the lookback window.
    Returns list of (so_number, serial) tuples.
    """
    cursor = mysql_conn.cursor()
    cursor.execute(f"""
        SELECT DISTINCT b.ERP_OrderNo, b.BoatSerialNo
        FROM {MYSQL_DB}.BoatOptions26 b
        WHERE b.ItemMasterMCT = 'BOA'
          AND b.ERP_OrderNo IS NOT NULL
          AND b.ERP_OrderNo != ''
          AND b.BoatSerialNo IS NOT NULL
          AND b.BoatSerialNo != ''
          AND b.InvoiceDate >= DATE_FORMAT(CURDATE() - INTERVAL {lookback_days} DAY, '%Y%m%d') + 0
          AND NOT EXISTS (
              SELECT 1 FROM {MYSQL_DB}.BoatOptions26 e
              WHERE e.ERP_OrderNo = b.ERP_OrderNo
                AND e.ItemMasterMCT = 'ENG'
          )
        ORDER BY b.ERP_OrderNo
    """)
    rows = cursor.fetchall()
    cursor.close()
    return rows


def sweep_missing_engines(mysql_conn, lookback_days: int = 180) -> int:
    """
    Step 1c: Scan all boats in the lookback window that are missing an engine
    row and attempt to backfill from CSIPRD. Reuses the same engine query and
    insert logic as Step 1b.
    """
    missing = find_sos_missing_engines(mysql_conn, lookback_days)
    if not missing:
        log("Step 1c: No boats missing engines found in the lookback window")
        return 0

    so_numbers = list({row[0] for row in missing})
    log(f"Step 1c: Found {len(missing)} boat(s) missing engines across {len(so_numbers)} SO(s) — querying CSIPRD...")
    return backfill_missing_engines(so_numbers, mysql_conn)


# ============================================================================
# STEP 1d — SWEEP: CPQ BOATS MISSING LIQUIFIRE IMAGE (LOOKBACK WINDOW)
# ============================================================================

def sweep_missing_liquifire_urls(mysql_conn, lookback_days: int = 180) -> int:
    """
    Step 1d: Find CPQ boats (ERP_OrderNo LIKE 'SO%') in the lookback window
    whose LiquifireImageUrl is NULL, fetch the real URL from CPQ, and update
    SerialNumberMaster.
    """
    cursor = mysql_conn.cursor()
    cursor.execute(f"""
        SELECT Boat_SerialNo, ERP_OrderNo, BoatItemNo
        FROM {MYSQL_DB}.SerialNumberMaster
        WHERE ERP_OrderNo LIKE 'SO%%'
          AND LiquifireImageUrl IS NULL
          AND InvoiceDateYYYYMMDD >= DATE_FORMAT(CURDATE() - INTERVAL {lookback_days} DAY, '%Y%m%d') + 0
        ORDER BY ERP_OrderNo DESC
    """)
    rows = cursor.fetchall()
    cursor.close()

    if not rows:
        log("Step 1d: No CPQ boats missing Liquifire URLs in the lookback window")
        return 0

    so_numbers  = [r[1] for r in rows]
    itemno_map  = {r[1]: r[2] for r in rows}
    serial_map  = {r[1]: r[0] for r in rows}

    log(f"Step 1d: Found {len(rows)} CPQ boat(s) missing Liquifire URLs — querying CPQ PRD...")
    image_urls = fetch_cpq_image_urls(so_numbers, itemno_map=itemno_map)

    if not image_urls:
        log("Step 1d: No image URLs returned from CPQ")
        return 0

    cursor = mysql_conn.cursor()
    updated = 0
    for so, url in image_urls.items():
        serial = serial_map.get(so)
        if not serial or not url:
            continue
        cursor.execute(
            f"UPDATE {MYSQL_DB}.SerialNumberMaster SET LiquifireImageUrl = %s WHERE Boat_SerialNo = %s",
            (url, serial)
        )
        if cursor.rowcount:
            log(f"  Image updated: {serial} ({so}) — {url[:80]}...")
            updated += 1

    mysql_conn.commit()
    cursor.close()
    log(f"Step 1d: Updated Liquifire URLs for {updated} boat(s)", "SUCCESS")
    return updated


def sweep_missing_liquifire_urls_matrix(mysql_conn, lookback_days: int = 180) -> int:
    """
    Step 1e: Fallback for CPQ boats that still have no LiquifireImageUrl after
    Step 1d (CPQ order no longer in PRD).  Builds the URL from CPQ color
    matrices + BoatOptions26 config data using build_liquifire_url.py.
    """
    cursor = mysql_conn.cursor()
    cursor.execute(f"""
        SELECT DISTINCT bo.BoatSerialNo
        FROM {MYSQL_DB}.BoatOptions26 bo
        JOIN {MYSQL_DB}.SerialNumberMaster snm ON snm.Boat_SerialNo = bo.BoatSerialNo
        WHERE bo.ConfigID IS NOT NULL AND bo.ConfigID != ''
          AND bo.BoatModelNo IS NOT NULL AND bo.BoatModelNo NOT IN ('', 'Base Boat')
          AND (
            snm.LiquifireImageUrl IS NULL
            OR snm.LiquifireImageUrl = ''
            OR snm.LiquifireImageUrl LIKE '%asset[furn\\_%'
            OR snm.LiquifireImageUrl LIKE '%view[]%'
            OR snm.LiquifireImageUrl LIKE '%asset[]%'
            -- CPQ PRD sometimes returns a URL whose asset year predates the boat model year.
            -- The furniture params make it render large enough to pass the >20KB check but
            -- the hull is wrong (shows only deck/tube). Catch by comparing asset year in the
            -- URL against the first 2 chars of BoatModelNo.
            OR (
                bo.BoatModelNo REGEXP '^[0-9]{2}'
                AND snm.LiquifireImageUrl REGEXP 'asset\\\\[[0-9]{2}'
                AND CAST(SUBSTRING(bo.BoatModelNo, 1, 2) AS UNSIGNED) <>
                    CAST(SUBSTRING(snm.LiquifireImageUrl,
                        LOCATE('asset[', snm.LiquifireImageUrl) + 6, 2) AS UNSIGNED)
            )
          )
          AND snm.InvoiceDateYYYYMMDD >= DATE_FORMAT(
                CURDATE() - INTERVAL {lookback_days} DAY, '%Y%m%d') + 0
    """)
    serials = [r[0] for r in cursor.fetchall()]
    cursor.close()

    if not serials:
        log("Step 1e: No CPQ boats missing or bad Liquifire URLs — matrix fallback not needed")
        return 0

    log(f"Step 1e: {len(serials)} boat(s) missing or bad Liquifire URL — building from CPQ matrices...")
    try:
        token = build_liquifire_url.get_trn_token()
        matrices = build_liquifire_url.load_matrices(token)
    except Exception as exc:
        log(f"Step 1e: Failed to load CPQ matrices — {exc}", "ERROR")
        return 0

    bo_cursor = mysql_conn.cursor()
    updated = 0
    for serial in serials:
        try:
            config, model, series = build_liquifire_url.get_boat_config(bo_cursor, serial)
            if not model:
                log(f"  {serial}: no model in BoatOptions26 — skipped")
                continue

            url = build_liquifire_url.build_url(serial, config, model, series, matrices)
            if not url:
                log(f"  {serial} ({model}): could not build URL — skipped")
                continue

            ok, size = build_liquifire_url.test_url(url)

            # Year fallback: try next model years if current asset missing
            if not ok and len(model) >= 2 and model[:2].isdigit():
                year = int(model[:2])
                for try_year in range(year + 1, year + 4):
                    fallback_model = f'{try_year:02d}{model[2:]}'
                    fallback_url = url.replace(f'asset[{model}]', f'asset[{fallback_model}]')
                    ok, size = build_liquifire_url.test_url(fallback_url)
                    if ok:
                        log(f"  {serial} ({model}): using fallback asset [{fallback_model}]")
                        url = fallback_url
                        break

            # Fallback: try view[side] with cat[pon] for models without a 3qtr asset
            if not ok:
                side_url = url.replace('cat[3qtr],', 'cat[pon],').replace(',view[3qtr]', ',view[side]')
                ok, size = build_liquifire_url.test_url(side_url)
                if ok:
                    log(f"  {serial} ({model}): using fallback view[side]")
                    url = side_url

            if not ok:
                log(f"  {serial} ({model}): URL did not render — skipped")
                continue

            cursor2 = mysql_conn.cursor()
            cursor2.execute(
                f"UPDATE {MYSQL_DB}.SerialNumberMaster SET LiquifireImageUrl = %s WHERE Boat_SerialNo = %s",
                (url, serial)
            )
            mysql_conn.commit()
            cursor2.close()
            log(f"  {serial} ({model}): stored ({size:,} bytes)")
            updated += 1

        except Exception as exc:
            log(f"  {serial}: error — {exc}", "WARNING")
            continue

    bo_cursor.close()
    log(f"Step 1e: Built and stored Liquifire URLs for {updated} boat(s)", "SUCCESS")
    return updated


# ============================================================================
# STEP 2 — SERIAL NUMBER MASTER LOAD
# ============================================================================

def load_serial_master(boats: List[Dict], conn) -> Tuple[int, int]:
    if not boats:
        return 0, 0

    cursor = conn.cursor()
    cursor.execute("SELECT Boat_SerialNo FROM SerialNumberMaster")
    existing = {row[0] for row in cursor.fetchall()}
    new_boats = [b for b in boats if b.get('BoatSerialNo') not in existing]
    skipped   = len(boats) - len(new_boats)
    log(f"{len(new_boats)} new boats for SerialNumberMaster ({skipped} already exist)")

    if not new_boats:
        # Update all fields for existing boats — handles re-invoice to a different dealer
        # as well as same-day re-run scenario.
        # NOTE: InvoiceNo and InvoiceDateYYYYMMDD are NOT overwritten here.
        # The boat invoice is captured correctly on first insert. Overwriting it
        # can cause the wrong invoice to be stored when the engine is invoiced
        # on a later date (engine invoice number overwrites boat invoice number),
        # which breaks the window sticker tool by hiding all boat data.
        update_sql = """
            UPDATE {table}
            SET ERP_OrderNo          = %s,
                InvoiceNo            = CASE WHEN (InvoiceNo IS NULL OR InvoiceNo = '') THEN %s ELSE InvoiceNo END,
                ApplyToNo            = CASE WHEN (ApplyToNo IS NULL OR ApplyToNo = '') THEN %s ELSE ApplyToNo END,
                OrigOrderType        = CASE WHEN (OrigOrderType IS NULL OR OrigOrderType = '') THEN %s ELSE OrigOrderType END,
                InvoiceDateYYYYMMDD  = CASE WHEN (InvoiceDateYYYYMMDD IS NULL OR InvoiceDateYYYYMMDD = '') THEN %s ELSE InvoiceDateYYYYMMDD END,
                DealerNumber         = %s,
                DealerName           = %s,
                DealerCity           = %s,
                DealerState          = %s,
                DealerZip            = %s,
                DealerCountry        = %s,
                WebOrderNo           = %s,
                Presold              = %s,
                PanelColor    = CASE WHEN %s <> '' THEN %s ELSE PanelColor    END,
                AccentPanel   = CASE WHEN %s <> '' THEN %s ELSE AccentPanel   END,
                BaseVinyl     = CASE WHEN %s <> '' THEN %s ELSE BaseVinyl     END,
                ColorPackage  = CASE WHEN %s <> '' THEN %s ELSE ColorPackage  END,
                TrimAccent    = CASE WHEN %s <> '' THEN %s ELSE TrimAccent    END,
                ParentRepName = COALESCE(CASE WHEN %s <> '' THEN %s ELSE ParentRepName END, '')
            WHERE Boat_SerialNo = %s
        """
        update_data = [
            (b['ERP_OrderNo'], b['InvoiceNo'], b['ApplyToNo'], b['OrigOrderType'],
             b['InvoiceDate'], b['DealerNumber'], b['DealerName'], b['DealerCity'],
             b['DealerState'], b['DealerZip'], b['DealerCountry'],
             b['WebOrderNo'], b['Presold'],
             b['PanelColor'],    b['PanelColor'],
             b['AccentPanel'],   b['AccentPanel'],
             b['BaseVinyl'],     b['BaseVinyl'],
             b['ColorPackage'],  b['ColorPackage'],
             b['TrimAccent'],    b['TrimAccent'],
             b['ParentRepName'], b['ParentRepName'],
             b['BoatSerialNo'])
            for b in boats
        ]
        cursor.executemany(update_sql.format(table='SerialNumberMaster'), update_data)
        conn.commit()
        log(f"Updated {len(boats)} existing boats in {MYSQL_DB}.SerialNumberMaster (dealer + colors)", "SUCCESS")
        cursor.close()
        return 0, skipped

    csv_file = tempfile.NamedTemporaryFile(
        mode='w', delete=False, suffix='_snm.csv', newline='')
    try:
        writer = csv.writer(csv_file, lineterminator='\n')
        for b in new_boats:
            writer.writerow([
                b.get('SN_MY', ''),         b.get('BoatSerialNo', ''),
                b.get('BoatItemNo', ''),     b.get('Series', ''),
                b.get('BoatDesc1', ''),      b.get('SerialModelYear', ''),
                b.get('ERP_OrderNo', ''),    b.get('InvoiceNo', ''),
                b.get('ApplyToNo', ''),      b.get('OrigOrderType', 'O'),
                b.get('InvoiceDate', ''),    b.get('DealerNumber', ''),
                b.get('DealerName', ''),     b.get('DealerCity', ''),
                b.get('DealerState', ''),    b.get('DealerZip', ''),
                b.get('DealerCountry', ''),  b.get('WebOrderNo', ''),
                1,
                b.get('ProdNo', ''),         b.get('BenningtonOwned', 0),
                0,
                b.get('PanelColor', ''),     b.get('AccentPanel', ''),
                b.get('BaseVinyl', ''),      b.get('ColorPackage', ''),
                b.get('TrimAccent', ''),     b.get('Presold', 'N'),
                b.get('Quantity', 1),        b.get('LiquifireImageUrl', ''),
                b.get('ParentRepName', ''),
            ])
        csv_file.close()

        cursor.execute("""
            CREATE TEMPORARY TABLE temp_snm (
                SN_MY VARCHAR(4), Boat_SerialNo VARCHAR(50), BoatItemNo VARCHAR(50),
                Series VARCHAR(20), BoatDesc1 VARCHAR(255), SerialModelYear VARCHAR(4),
                ERP_OrderNo VARCHAR(30), InvoiceNo VARCHAR(30), ApplyToNo VARCHAR(30),
                OrigOrderType VARCHAR(1), InvoiceDate VARCHAR(20),
                DealerNumber VARCHAR(20), DealerName VARCHAR(100), DealerCity VARCHAR(50),
                DealerState VARCHAR(10), DealerZip VARCHAR(20), DealerCountry VARCHAR(50),
                WebOrderNo VARCHAR(30), Active INT, ProdNo VARCHAR(50),
                BenningtonOwned INT, SN_ID INT,
                PanelColor VARCHAR(100),
                AccentPanel VARCHAR(100), BaseVinyl VARCHAR(100),
                ColorPackage VARCHAR(100), TrimAccent VARCHAR(100),
                Presold VARCHAR(1), Quantity INT,
                LiquifireImageUrl VARCHAR(2000), ParentRepName VARCHAR(255)
            )
        """)

        csv_path = csv_file.name.replace('\\', '/')
        cursor.execute(f"""
            LOAD DATA LOCAL INFILE '{csv_path}'
            INTO TABLE temp_snm
            FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"'
            LINES TERMINATED BY '\\n'
        """)

        insert_sql = """
            INSERT IGNORE INTO {table} (
                SN_MY, Boat_SerialNo, BoatItemNo, Series, BoatDesc1, SerialModelYear,
                ERP_OrderNo, InvoiceNo, ApplyToNo, OrigOrderType, InvoiceDateYYYYMMDD,
                DealerNumber, DealerName, DealerCity, DealerState, DealerZip, DealerCountry,
                WebOrderNo, Active, ProdNo, BenningtonOwned, SN_ID, PanelColor, AccentPanel, BaseVinyl,
                ColorPackage, TrimAccent, Presold, Quantity, LiquifireImageUrl, ParentRepName
            )
            SELECT
                SN_MY, Boat_SerialNo, BoatItemNo, Series, BoatDesc1, SerialModelYear,
                ERP_OrderNo, InvoiceNo, ApplyToNo, OrigOrderType, InvoiceDate,
                DealerNumber, DealerName, DealerCity, DealerState, DealerZip, DealerCountry,
                WebOrderNo, Active, ProdNo, BenningtonOwned, SN_ID, PanelColor, AccentPanel, BaseVinyl,
                ColorPackage, TrimAccent, Presold, Quantity, LiquifireImageUrl, ParentRepName
            FROM temp_snm
        """

        # Insert into current database (warrantyparts_test for dev, warrantyparts for prod)
        cursor.execute(insert_sql.format(table='SerialNumberMaster'))
        inserted = cursor.rowcount

        cursor.execute("DROP TEMPORARY TABLE temp_snm")

        # UPDATE dealer + invoice + color fields for all boats in today's batch.
        # INSERT IGNORE skips existing rows, but UPDATE ensures re-invoiced boats
        # (credited from one dealer and re-sold to another) get their dealer info refreshed.
        update_sql = """
            UPDATE {table}
            SET ERP_OrderNo          = %s,
                InvoiceNo            = %s,
                ApplyToNo            = %s,
                OrigOrderType        = %s,
                InvoiceDateYYYYMMDD  = %s,
                DealerNumber         = %s,
                DealerName           = %s,
                DealerCity           = %s,
                DealerState          = %s,
                DealerZip            = %s,
                DealerCountry        = %s,
                WebOrderNo           = %s,
                Presold              = %s,
                PanelColor    = CASE WHEN %s <> '' THEN %s ELSE PanelColor    END,
                AccentPanel   = CASE WHEN %s <> '' THEN %s ELSE AccentPanel   END,
                BaseVinyl     = CASE WHEN %s <> '' THEN %s ELSE BaseVinyl     END,
                ColorPackage  = CASE WHEN %s <> '' THEN %s ELSE ColorPackage  END,
                TrimAccent    = CASE WHEN %s <> '' THEN %s ELSE TrimAccent    END,
                ParentRepName = COALESCE(CASE WHEN %s <> '' THEN %s ELSE ParentRepName END, '')
            WHERE Boat_SerialNo = %s
        """
        update_data = [
            (b['ERP_OrderNo'], b['InvoiceNo'], b['ApplyToNo'], b['OrigOrderType'],
             b['InvoiceDate'], b['DealerNumber'], b['DealerName'], b['DealerCity'],
             b['DealerState'], b['DealerZip'], b['DealerCountry'],
             b['WebOrderNo'], b['Presold'],
             b['PanelColor'],    b['PanelColor'],
             b['AccentPanel'],   b['AccentPanel'],
             b['BaseVinyl'],     b['BaseVinyl'],
             b['ColorPackage'],  b['ColorPackage'],
             b['TrimAccent'],    b['TrimAccent'],
             b['ParentRepName'], b['ParentRepName'],
             b['BoatSerialNo'])
            for b in boats
        ]
        cursor.executemany(update_sql.format(table='SerialNumberMaster'), update_data)

        conn.commit()
        log(f"Inserted {inserted} boats into {MYSQL_DB}.SerialNumberMaster", "SUCCESS")
        log(f"Updated dealer + color fields for {len(boats)} boats in {MYSQL_DB}.SerialNumberMaster", "SUCCESS")
        return inserted, skipped

    finally:
        os.unlink(csv_file.name)
        cursor.close()


def reconcile_snm_invoices(boats: List[Dict], conn) -> int:
    """
    After loading SNM, verify each boat's InvoiceNo in SNM matches an InvoiceNo
    in BoatOptions{YY} for the same serial.

    When a boat is re-invoiced in Syteline, the SNM query picks up the new
    inv_num and overwrites InvoiceNo in SerialNumberMaster. But the BoatOptions
    import (Step 1) already ran under the original invoice, so BoatOptions still
    has the old InvoiceNo. The window sticker tool then finds 0 records because
    it filters BoatOptions by the SNM invoice.

    Fix: if SNM's InvoiceNo doesn't appear in BoatOptions for that serial,
    update SNM to use the invoice that BoatOptions actually has.
    """
    if not boats:
        return 0

    cursor = conn.cursor()
    fixed = 0

    for boat in boats:
        serial     = boat.get('BoatSerialNo')
        snm_invoice = (boat.get('InvoiceNo') or '').strip()
        if not serial or not snm_invoice:
            continue

        model_year = detect_model_year(serial)
        bo_table   = get_table_for_year(model_year)

        # Check which invoice(s) BoatOptions actually has for this serial
        try:
            cursor.execute(
                f"SELECT InvoiceNo, COUNT(*) AS cnt FROM {bo_table} "
                "WHERE BoatSerialNo = %s AND InvoiceNo IS NOT NULL AND InvoiceNo != '' "
                "GROUP BY InvoiceNo ORDER BY cnt DESC",
                (serial,)
            )
            bo_rows = cursor.fetchall()
        except Exception:
            continue  # Table may not exist for this year

        if not bo_rows:
            continue  # No BoatOptions records yet — boat imported today, nothing to reconcile

        bo_invoices = [row[0] for row in bo_rows]
        if snm_invoice in bo_invoices:
            continue  # SNM invoice matches BoatOptions — all good

        # SNM invoice not found in BoatOptions — use the invoice with the most BO rows
        bo_invoice = bo_rows[0][0]
        cursor.execute(
            "UPDATE SerialNumberMaster SET InvoiceNo = %s "
            "WHERE Boat_SerialNo = %s AND InvoiceNo = %s",
            (bo_invoice, serial, snm_invoice)
        )
        if cursor.rowcount > 0:
            log(f"  Re-invoice reconciled {serial}: SNM had {snm_invoice} → corrected to {bo_invoice} (from BoatOptions)", "WARNING")
            fixed += 1

    conn.commit()
    cursor.close()
    return fixed


def load_registration_status(boats: List[Dict], conn) -> Tuple[int, int]:
    if not boats:
        return 0, 0

    cursor = conn.cursor()
    cursor.execute("SELECT Boat_SerialNo FROM SerialNumberRegistrationStatus")
    existing  = {row[0] for row in cursor.fetchall()}
    new_boats = [b for b in boats if b.get('BoatSerialNo') not in existing]
    skipped   = len(boats) - len(new_boats)

    if not new_boats:
        cursor.close()
        return 0, skipped

    csv_file = tempfile.NamedTemporaryFile(
        mode='w', delete=False, suffix='_reg.csv', newline='')
    try:
        writer = csv.writer(csv_file)
        for b in new_boats:
            snd = 1 if (b.get('Presold') or '').strip().upper() == 'Y' else 0
            writer.writerow([b.get('SN_MY', ''), b.get('BoatSerialNo', ''),
                             0, 1, 0, snd, 0])  # Registered=0, FieldInventory=1, Unknown=0, SND=presold, BenningtonOwned=0
        csv_file.close()

        cursor.execute("""
            CREATE TEMPORARY TABLE temp_reg (
                SN_MY VARCHAR(4), Boat_SerialNo VARCHAR(50), Registered INT,
                FieldInventory INT, Unknown_col INT, SND INT, BenningtonOwned INT
            )
        """)
        csv_path = csv_file.name.replace('\\', '/')
        cursor.execute(f"""
            LOAD DATA LOCAL INFILE '{csv_path}'
            INTO TABLE temp_reg
            FIELDS TERMINATED BY ',' LINES TERMINATED BY '\\n'
        """)
        cursor.execute("""
            INSERT IGNORE INTO SerialNumberRegistrationStatus
                (SN_MY, Boat_SerialNo, Registered, FieldInventory,
                 `Unknown`, SND, BenningtonOwned)
            SELECT SN_MY, Boat_SerialNo, Registered, FieldInventory,
                   Unknown_col, SND, BenningtonOwned
            FROM temp_reg
        """)
        inserted = cursor.rowcount
        cursor.execute("DROP TEMPORARY TABLE temp_reg")
        conn.commit()
        log(f"Inserted {inserted} boats into SerialNumberRegistrationStatus", "SUCCESS")
        return inserted, skipped

    finally:
        os.unlink(csv_file.name)
        cursor.close()


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 80)
    print("DAILY BOAT IMPORT PIPELINE")
    print("=" * 80)
    print(f"MSSQL Source:   {MSSQL_DB} on {MSSQL_CONFIG['server']}")
    print(f"MySQL Target:   {MYSQL_DB}")
    print(f"Invoice Filter: {datetime.now().strftime('%Y-%m-%d')} (today)")
    print(f"Started:        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()

    bo_results: dict = {}
    raw_boats:  list = []
    snm_inserted = snm_skipped = reg_inserted = reg_skipped = snm_reconciled = 0

    try:
        # ── STEP 0: CPQ Data ─────────────────────────────────────────────────
        print()
        log("=" * 60)
        log("STEP 0: CPQ DATA IMPORT")
        log("=" * 60)
        load_cpq_data.main()

        # ── STEP 1: BoatOptions ─────────────────────────────────────────────
        print()
        log("=" * 60)
        log("STEP 1: BOATOPTIONS IMPORT")
        log("=" * 60)

        log(f"Connecting to MSSQL ({MSSQL_CONFIG['server']})...")
        mssql_conn = pymssql.connect(**MSSQL_CONFIG)
        cursor = mssql_conn.cursor(as_dict=True)
        log("Connected. Extracting today's invoiced line items...", "SUCCESS")
        cursor.execute(build_boatoptions_query(MSSQL_DB))
        boat_option_rows = cursor.fetchall()
        log(f"Extracted {len(boat_option_rows):,} rows from MSSQL", "SUCCESS")
        cursor.close()
        mssql_conn.close()

        if boat_option_rows:
            mysql_conn  = mysql.connector.connect(**MYSQL_CONFIG)
            table_groups = group_by_table(boat_option_rows)
            for table_name, rows in table_groups.items():
                bo_results[table_name] = load_boatoptions_batch(rows, table_name, mysql_conn)

            # ── STEP 1b: Engine backfill ─────────────────────────────────────
            print()
            log("=" * 60)
            log("STEP 1b: MISSING ENGINE BACKFILL")
            log("=" * 60)
            today_so_numbers = list({
                row.get('ERP_OrderNo') for row in boat_option_rows
                if row.get('ERP_OrderNo')
            })
            log(f"Checking {len(today_so_numbers)} SO(s) for missing engine rows...")
            backfill_missing_engines(today_so_numbers, mysql_conn)

            # ── STEP 1c: Sweep all boats missing engines (180-day window) ────
            print()
            log("=" * 60)
            log("STEP 1c: SWEEP — ALL BOATS MISSING ENGINES (180-DAY WINDOW)")
            log("=" * 60)
            sweep_missing_engines(mysql_conn, lookback_days=180)

            # ── STEP 1d: Sweep CPQ boats missing Liquifire image URLs ────────
            print()
            log("=" * 60)
            log("STEP 1d: SWEEP — CPQ BOATS MISSING LIQUIFIRE IMAGE (14-DAY WINDOW)")
            log("=" * 60)
            sweep_missing_liquifire_urls(mysql_conn, lookback_days=14)

            # ── STEP 1e: Matrix fallback for boats CPQ PRD couldn't resolve ──
            print()
            log("=" * 60)
            log("STEP 1e: SWEEP — LIQUIFIRE MATRIX FALLBACK (180-DAY WINDOW)")
            log("=" * 60)
            sweep_missing_liquifire_urls_matrix(mysql_conn, lookback_days=180)
            mysql_conn.close()
        else:
            log("No line items found for today.", "WARNING")

        # ── STEP 2: SerialNumberMaster ──────────────────────────────────────
        print()
        log("=" * 60)
        log("STEP 2: SERIAL NUMBER MASTER IMPORT")
        log("=" * 60)

        log(f"Connecting to MSSQL ({MSSQL_CONFIG['server']})...")
        mssql_conn = pymssql.connect(**MSSQL_CONFIG)
        cursor = mssql_conn.cursor(as_dict=True)
        log("Connected. Extracting today's invoiced boats...", "SUCCESS")
        cursor.execute(build_serial_master_query(MSSQL_DB))
        raw_boats = cursor.fetchall()
        log(f"Extracted {len(raw_boats)} boats from MSSQL", "SUCCESS")
        cursor.close()
        mssql_conn.close()

        # Deduplicate by BoatSerialNo — MSSQL can return the same HIN twice when a boat
        # has multiple invoice records (e.g., partial invoicing or correction invoices).
        seen_serials: set = set()
        deduped: list = []
        for b in raw_boats:
            serial = b.get('BoatSerialNo')
            if serial and serial not in seen_serials:
                seen_serials.add(serial)
                deduped.append(b)
            elif serial:
                log(f"Duplicate HIN from MSSQL (skipping): {serial}", "WARNING")
        if len(deduped) < len(raw_boats):
            log(f"Deduplicated: {len(raw_boats)} → {len(deduped)} boats")
        raw_boats = deduped

        prepared = []
        if raw_boats:
            config_ids  = {b.get('ConfigId') for b in raw_boats if b.get('ConfigId')}
            color_attrs = fetch_color_attrs(config_ids, MSSQL_DB)

            # Also fetch color attributes from BoatOptions for legacy boats (non-CPQ)
            mysql_conn_bo = mysql.connector.connect(**MYSQL_CONFIG)
            serials = [b.get('BoatSerialNo') for b in raw_boats if b.get('BoatSerialNo')]
            boatoptions_colors = fetch_color_attrs_from_boatoptions(serials, mysql_conn_bo)
            mysql_conn_bo.close()

            rep_names, state_rep_map = load_rep_names()
            log(f"Loaded {len(rep_names)} rep names, {len(state_rep_map)} state mappings")

            # Fetch Liquifire image URLs from CPQ for CPQ boats.
            # Use ERP_OrderNo (co_num = SO00936xxx) as the CPQ ExternalId — not
            # external_confirmation_ref, which can be a CPQ-generated ref like SOORE000001.
            so_to_config_id = {
                str(b.get('ERP_OrderNo', '')): b.get('ConfigId')
                for b in raw_boats
                if str(b.get('ERP_OrderNo', '')).startswith('SO')
            }
            so_to_itemno = {
                str(b.get('ERP_OrderNo', '')): (b.get('BoatItemNo') or '').strip()
                for b in raw_boats
                if str(b.get('ERP_OrderNo', '')).startswith('SO')
            }
            cpq_so_numbers = list(so_to_config_id.keys())
            if cpq_so_numbers:
                log(f"Fetching CPQ image URLs for {len(cpq_so_numbers)} CPQ order(s)...")
                cpq_image_urls = fetch_cpq_image_urls(cpq_so_numbers, config_id_map=so_to_config_id,
                                                      itemno_map=so_to_itemno)
            else:
                cpq_image_urls = {}

            # Detect CPQ boats by checking for CfgName in boat_option_rows
            def is_cpq_boat(serial_no):
                """Check if boat has CPQ configuration (CfgName field populated)"""
                for row in boat_option_rows:
                    if row.get('BoatSerialNo') == serial_no:
                        cfg_name = row.get('CfgName')
                        if cfg_name and str(cfg_name).strip():
                            return True
                return False
            
            prepared: list = []
            for boat in raw_boats:
                serial = boat.get('BoatSerialNo')
                if not serial:
                    continue
                sn_my = get_model_year_2digit(serial)
                cfg   = color_attrs.get(boat.get('ConfigId'), {}) if boat.get('ConfigId') else {}
                bo_colors = boatoptions_colors.get(serial, {})  # Fallback for legacy boats
                
                # Use CPQ config attrs if available, otherwise fall back to BoatOptions
                panel_color = (boat.get('PanelColor') or cfg.get('PanelColor_cfg') or bo_colors.get('PanelColor') or '').strip()
                accent_panel = (cfg.get('AccentPanel') or bo_colors.get('AccentPanel') or '').strip()
                trim_accent = (cfg.get('TrimAccent') or bo_colors.get('TrimAccent') or '').strip()
                color_package = (cfg.get('ColorPackage') or bo_colors.get('ColorPackage') or '').strip()
                
                # Detect if this is a CPQ boat
                is_cpq = is_cpq_boat(serial)
                
                prepared.append({
                    'SN_MY':           sn_my,
                    'BoatSerialNo':    serial,
                    'BoatItemNo':      (boat.get('BoatItemNo') or '').strip(),
                    'Series':          (boat.get('Series') or '').strip(),
                    'BoatDesc1':       (boat.get('BoatDesc1') or '').strip(),
                    'SerialModelYear': get_full_model_year(sn_my),
                    'ERP_OrderNo':     (boat.get('ERP_OrderNo') or '').strip(),
                    'InvoiceNo':       (boat.get('InvoiceNo') or '').strip(),
                    'ApplyToNo':       (boat.get('ApplyToNo') or '').strip(),
                    'OrigOrderType':   (boat.get('OrigOrderType') or 'O').strip(),
                    'InvoiceDate':     boat.get('InvoiceDate') or '',
                    'DealerNumber':    (boat.get('DealerNumber') or '').strip().lstrip('0'),
                    'DealerName':      (boat.get('DealerName') or '').strip(),
                    'DealerCity':      (boat.get('DealerCity') or '').strip(),
                    'DealerState':     (boat.get('DealerState') or '').strip(),
                    'DealerZip':       (boat.get('DealerZip') or '').strip(),
                    'DealerCountry':   (boat.get('DealerCountry') or '').strip(),
                    'WebOrderNo':      (boat.get('WebOrderNo') or '').strip(),
                    'ProdNo':          str(boat.get('ProdNo') or '').strip(),
                    'BenningtonOwned': 1 if boat.get('BenningtonOwned') in (1, True, 'Y', 'y', '1') else 0,
                    'PanelColor':      panel_color,
                    'AccentPanel':     accent_panel,
                    'BaseVinyl':       (cfg.get('BaseVinyl') or boat.get('BaseVinyl') or bo_colors.get('BaseVinyl') or '').strip(),
                    'ColorPackage':    color_package,
                    'TrimAccent':      trim_accent,
                    'ParentRepName':   (
                        (rep_names.get(int(boat['SlsMan'])) if boat.get('SlsMan') not in (None, '', 0) else None)
                        or state_rep_map.get((boat.get('DealerState') or '').strip().upper())
                        or ''
                    ),
                    'Presold':         'Y' if boat.get('Presold') in (1, True, 'Y', 'y') else 'N',
                    'Quantity':        int(boat.get('Quantity') or 1),
                    'LiquifireImageUrl': cpq_image_urls.get(str(boat.get('ERP_OrderNo', '')),
                                         'https://s3.amazonaws.com/eosstatic/images/0/5880c9a7a9d29ae43164c78f/Generic-01.jpg'),
                    'IsCPQ':           is_cpq,
                })

            mysql_conn = mysql.connector.connect(**MYSQL_CONFIG, allow_local_infile=True)
            ensure_snm_image_column(mysql_conn)
            snm_inserted, snm_skipped = load_serial_master(prepared, mysql_conn)
            reg_inserted, reg_skipped = load_registration_status(prepared, mysql_conn)
            snm_reconciled = reconcile_snm_invoices(prepared, mysql_conn)
            if snm_reconciled:
                log(f"Invoice reconciliation: corrected {snm_reconciled} boat(s) where SNM invoice didn't match BoatOptions", "WARNING")

            # Update SerialNumberMaster with Liquifire URLs for all boats with SO order numbers.
            # This covers both CPQ-configured boats and OrigOrderType='O' boats which EOS may
            # have inserted without a URL.
            boats_with_image = [b for b in prepared if b.get('LiquifireImageUrl')]
            boats_without_image = [b for b in prepared
                                   if str(b.get('ERP_OrderNo', '')).startswith('SO')
                                   and not b.get('LiquifireImageUrl')]

            so_boats_count = len(boats_with_image) + len(boats_without_image)
            log(f"Boats with SO order numbers: {so_boats_count} total")
            log(f"  - With image URLs: {len(boats_with_image)}")
            log(f"  - Without image URLs: {len(boats_without_image)}")

            if boats_without_image:
                log(f"Boats missing image URLs: {[b['BoatSerialNo'] for b in boats_without_image]}", "WARNING")

            if boats_with_image:
                cursor = mysql_conn.cursor()
                for boat in boats_with_image:
                    cursor.execute(
                        f"UPDATE {MYSQL_DB}.SerialNumberMaster "
                        "SET LiquifireImageUrl = %s WHERE Boat_SerialNo = %s",
                        (boat['LiquifireImageUrl'], boat['BoatSerialNo'])
                    )
                mysql_conn.commit()
                cursor.close()
                # Note: rowcount=0 is normal for new boats — LiquifireImageUrl was already
                # written via the INSERT from temp_snm. The UPDATE is needed only for
                # OrigOrderType='O' boats that EOS inserted without a URL.
                log(f"Image URLs applied for {len(boats_with_image)} boat(s) in {MYSQL_DB}.SerialNumberMaster", "SUCCESS")

            mysql_conn.close()
        else:
            log("No boats found for today.", "WARNING")

        # ── SUMMARY ─────────────────────────────────────────────────────────
        today_str    = datetime.now().strftime('%Y-%m-%d')
        log_filename = f"import_{today_str}.log"

        lines = []
        lines.append("=" * 80)
        lines.append("PIPELINE SUMMARY")
        lines.append("=" * 80)
        lines.append(f"\nSTEP 1 - BoatOptions ({MYSQL_DB}):")
        if bo_results:
            for table, count in sorted(bo_results.items()):
                lines.append(f"  {table}: {count:,} rows total")
        else:
            lines.append("  No data loaded")
        lines.append(f"\nSTEP 2 - SerialNumberMaster ({MYSQL_DB}):")
        lines.append(f"  Boats found today:        {len(raw_boats)}")
        lines.append(f"  SerialNumberMaster:       {snm_inserted} inserted, {snm_skipped} already existed")
        lines.append(f"  RegistrationStatus:       {reg_inserted} inserted, {reg_skipped} already existed")
        lines.append(f"  Invoice reconciled:       {snm_reconciled if prepared else 0} boat(s) corrected")

        # ── DEALER TABLE ────────────────────────────────────────────────────
        if prepared:
            lines.append(f"\n{'-' * 100}")
            lines.append(f"  {'Serial':<15} {'Dealer#':<10} {'Dealer Name':<42} {'City':<22} {'State'}")
            lines.append(f"  {'-'*15} {'-'*10} {'-'*42} {'-'*22} {'-'*5}")
            for b in sorted(prepared, key=lambda x: x['BoatSerialNo']):
                lines.append(
                    f"  {b['BoatSerialNo']:<15} {b['DealerNumber']:<10} "
                    f"{b['DealerName']:<42} {b['DealerCity']:<22} {b['DealerState']}"
                )
            lines.append(f"{'-' * 100}")

        lines.append(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 80)

        output = "\n".join(lines)
        print()
        print(output)

        with open(log_filename, 'w', encoding='utf-8') as f:
            f.write(output + "\n")
        log(f"Summary written to {log_filename}")

    except KeyboardInterrupt:
        log("Cancelled by user.", "WARNING")
        sys.exit(1)
    except Exception as e:
        log(f"Fatal error: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

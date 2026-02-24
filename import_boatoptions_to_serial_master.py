#!/usr/bin/env python3
"""
Bulk Import Boats to SerialNumberMaster and SerialNumberRegistrationStatus

Automated replacement for the PHP pipeline (QlikView → NPrinting → CSV → PHP → MySQL).
Queries MSSQL directly for all invoiced boats and inserts missing ones into MySQL
with real dealer information and color/configuration fields.

Usage:
    python3 import_serial_master.py          (uses STG MSSQL)
    python3 import_serial_master.py --PRD    (uses PRD MSSQL)
"""

import sys
import os
import csv
import tempfile
from datetime import datetime
from typing import List, Dict, Set, Optional, Tuple, cast, Any
import pymssql
import mysql.connector
from mysql.connector import Error as MySQLError


def load_env_file(env_path: str = '.env'):
    """Load KEY=VALUE pairs from .env into environment variables."""
    if not os.path.exists(env_path):
        return

    with open(env_path, 'r', encoding='utf-8') as env_file:
        for line in env_file:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue

            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            if key and key not in os.environ:
                os.environ[key] = value


def get_env_int(key: str, default: int) -> int:
    """Read integer environment variable with fallback."""
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


load_env_file()

# ==================== CONFIGURATION - HARDCODED TO PRODUCTION ====================

MSSQL_CONFIG = {
    'server': os.getenv('MSSQL_PRD_SERVER', 'MPL1ITSSQL086.POLARISIND.COM'),
    'database': 'CSIPRD',  # Hardcoded to production database
    'user': os.getenv('MSSQL_PRD_USER', 'svcSpecs01'),
    'password': os.getenv('MSSQL_PRD_PASSWORD'),
    'timeout': get_env_int('MSSQL_TIMEOUT', 300),
    'login_timeout': get_env_int('MSSQL_LOGIN_TIMEOUT', 60)
}

MSSQL_DATABASE = MSSQL_CONFIG['database']

MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST'),
    'port': get_env_int('MYSQL_PORT', 3306),
    'database': 'warrantyparts',
    'user': os.getenv('MYSQL_USER'),
    'password': os.getenv('MYSQL_PASSWORD')
}

ORDER_DATE_CUTOFF = '2021-01-01'


def log(message: str, level: str = "INFO"):
    """Print timestamped log message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def get_model_year_from_serial(serial_number: str) -> Optional[str]:
    """Extract 2-digit model year from the last 2 characters of the HIN."""
    if not serial_number or len(serial_number) < 2:
        return None
    last2 = serial_number[-2:]
    if last2.isdigit():
        return last2
    return None


def get_full_model_year(two_digit_year: str) -> str:
    """Convert 2-digit year to 4-digit (e.g., '26' -> '2026', '99' -> '1999')."""
    if not two_digit_year:
        return ''
    yr = int(two_digit_year)
    if yr >= 90:
        return str(1900 + yr)
    else:
        return str(2000 + yr)


def extract_boats_from_mssql() -> List[Dict]:
    """Query MSSQL for all invoiced boats with dealer information."""
    db = MSSQL_DATABASE

    query = f"""
    SELECT DISTINCT
        COALESCE(NULLIF(coi.Uf_BENN_BoatSerialNumber, ''), ser.ser_num) AS BoatSerialNo,
        coi.item AS BoatItemNo,
        coi.description AS BoatDesc1,
        im.Uf_BENN_Series AS Series,
        coi.co_num AS ERP_OrderNo,
        LEFT(coi.Uf_BENN_BoatWebOrderNumber, 30) AS WebOrderNo,
        iim.inv_num AS InvoiceNo,
        CASE WHEN ah.inv_date IS NOT NULL 
            THEN CONVERT(INT, CONVERT(VARCHAR(8), ah.inv_date, 112)) 
            ELSE NULL 
        END AS InvoiceDate,
        co.cust_num AS DealerNumber,
        cust.name AS DealerName,
        cust.city AS DealerCity,
        cust.state AS DealerState,
        cust.zip AS DealerZip,
        cust.country AS DealerCountry,
        coi.Uf_BENN_BoatModel AS BoatModelNo,
        co.order_date AS OrderDate,
        co.Uf_BENN_ProductionNumber AS ProdNo,
        co.Uf_BENN_BenningtonOwned AS BenningtonOwned,
        coi.Uf_BENN_PannelColor AS PanelColor,
        coi.Uf_BENN_BaseVnyl AS BaseVinyl,
        coi.config_id AS ConfigId
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
    INNER JOIN [{db}].[dbo].[arinv_mst] ah
        ON iim.inv_num = ah.inv_num
        AND iim.site_ref = ah.site_ref
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
            (coi.Uf_BENN_BoatSerialNumber IS NOT NULL AND coi.Uf_BENN_BoatSerialNumber != '')
            OR ser.ser_num IS NOT NULL
        )
        AND iim.inv_num IS NOT NULL
        AND coi.qty_invoiced > 0
        AND co.order_date >= '{ORDER_DATE_CUTOFF}'
    ORDER BY BoatSerialNo
    """

    log(f"Connecting to MSSQL (PRD: {MSSQL_CONFIG['server']} / {MSSQL_DATABASE})...")

    conn = pymssql.connect(
        server=MSSQL_CONFIG['server'],
        database=MSSQL_CONFIG['database'],
        user=MSSQL_CONFIG['user'],
        password=MSSQL_CONFIG['password'],
        timeout=MSSQL_CONFIG['timeout'],
        login_timeout=MSSQL_CONFIG['login_timeout']
    )
    cursor = conn.cursor(as_dict=True)

    log("Executing boat query...")
    cursor.execute(query)
    rows = cast(List[Dict[str, Any]], cursor.fetchall() or [])
    log(f"Fetched {len(rows)} invoiced boats from MSSQL")

    cursor.close()
    conn.close()

    return rows


def fetch_color_fields_bulk(boats: List[Dict]) -> Dict:
    """Fetch color/config attributes from cfg_attr_mst for all config_ids."""
    config_ids = {b.get('ConfigId') for b in boats if b.get('ConfigId')}

    if not config_ids:
        return {}

    db = MSSQL_DATABASE
    conn = pymssql.connect(
        server=MSSQL_CONFIG['server'],
        database=MSSQL_CONFIG['database'],
        user=MSSQL_CONFIG['user'],
        password=MSSQL_CONFIG['password'],
        timeout=MSSQL_CONFIG['timeout'],
        login_timeout=MSSQL_CONFIG['login_timeout']
    )
    cursor = conn.cursor(as_dict=True)

    config_colors = {}
    config_id_list = list(config_ids)

    batch_size = 500
    for i in range(0, len(config_id_list), batch_size):
        batch = config_id_list[i:i + batch_size]
        placeholders = ','.join(['%s'] * len(batch))

        query = f"""
        SELECT
            config_id,
            attr_name,
            attr_value
        FROM [{db}].[dbo].[cfg_attr_mst]
        WHERE config_id IN ({placeholders})
            AND site_ref = 'BENN'
            AND attr_value IS NOT NULL
            AND attr_value != ''
            AND (
                attr_name LIKE '%Accent Panel%'
                OR attr_name LIKE '%Color Package%'
                OR attr_name LIKE '%Trim Accent%'
                OR attr_name = 'PANEL COLOR'
            )
        """

        cursor.execute(query, tuple(batch))
        results = cast(List[Dict[str, Any]], cursor.fetchall() or [])

        for row in results:
            cid = row['config_id']
            attr_name = (row.get('attr_name') or '').upper()
            attr_value = row.get('attr_value')

            if cid not in config_colors:
                config_colors[cid] = {
                    'AccentPanel': None,
                    'ColorPackage': None,
                    'TrimAccent': None,
                    'PanelColor_cfg': None
                }

            if 'ACCENT PANEL' in attr_name:
                config_colors[cid]['AccentPanel'] = attr_value
            elif 'COLOR PACKAGE' in attr_name:
                config_colors[cid]['ColorPackage'] = attr_value
            elif 'TRIM ACCENT' in attr_name:
                config_colors[cid]['TrimAccent'] = attr_value
            elif attr_name == 'PANEL COLOR':
                config_colors[cid]['PanelColor_cfg'] = attr_value

    cursor.close()
    conn.close()

    log(f"Fetched color attributes for {len(config_colors)} configured boats")
    return config_colors


def get_existing_serials(mysql_cursor) -> Set[str]:
    """Get all existing Boat_SerialNo values from SerialNumberMaster."""
    log("Loading existing serial numbers from SerialNumberMaster...")
    mysql_cursor.execute("SELECT Boat_SerialNo FROM SerialNumberMaster")
    existing = set(row[0] for row in mysql_cursor.fetchall())
    log(f"Found {len(existing)} existing serial numbers")
    return existing


def get_existing_registration_serials(mysql_cursor) -> Set[str]:
    """Get all existing Boat_SerialNo values from SerialNumberRegistrationStatus."""
    mysql_cursor.execute("SELECT Boat_SerialNo FROM SerialNumberRegistrationStatus")
    return set(row[0] for row in mysql_cursor.fetchall())


def bulk_insert_serial_master(mysql_cursor, boats: List[Dict]) -> Tuple[int, int]:
    """Bulk insert boats into SerialNumberMaster using LOAD DATA LOCAL INFILE."""
    if not boats:
        return 0, 0

    log(f"Preparing {len(boats)} boats for SerialNumberMaster bulk insert...")

    csv_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='_serial_master.csv', newline='')

    try:
        writer = csv.writer(csv_file)
        for boat in boats:
            writer.writerow([
                boat.get('SN_MY', ''),
                boat.get('BoatSerialNo', ''),
                boat.get('BoatItemNo', ''),
                boat.get('Series', ''),
                boat.get('BoatDesc1', ''),
                boat.get('SerialModelYear', ''),
                boat.get('ERP_OrderNo', ''),
                boat.get('InvoiceNo', ''),
                boat.get('InvoiceDate', ''),
                boat.get('DealerNumber', ''),
                boat.get('DealerName', ''),
                boat.get('DealerCity', ''),
                boat.get('DealerState', ''),
                boat.get('DealerZip', ''),
                boat.get('DealerCountry', ''),
                boat.get('WebOrderNo', ''),
                0,  # Active
                boat.get('ProdNo', ''),
                boat.get('BenningtonOwned', ''),
                boat.get('PanelColor', ''),
                boat.get('AccentPanel', ''),
                boat.get('BaseVinyl', ''),
                boat.get('ColorPackage', ''),
                boat.get('TrimAccent', '')
            ])
        csv_file.close()

        # Create temp table
        mysql_cursor.execute("""
            CREATE TEMPORARY TABLE temp_serial_master (
                SN_MY VARCHAR(4),
                Boat_SerialNo VARCHAR(50),
                BoatItemNo VARCHAR(50),
                Series VARCHAR(20),
                BoatDesc1 VARCHAR(255),
                SerialModelYear VARCHAR(4),
                ERP_OrderNo VARCHAR(30),
                InvoiceNo VARCHAR(30),
                InvoiceDate VARCHAR(20),
                DealerNumber VARCHAR(20),
                DealerName VARCHAR(100),
                DealerCity VARCHAR(50),
                DealerState VARCHAR(10),
                DealerZip VARCHAR(20),
                DealerCountry VARCHAR(50),
                WebOrderNo VARCHAR(30),
                Active INT,
                ProdNo VARCHAR(50),
                BenningtonOwned VARCHAR(10),
                PanelColor VARCHAR(100),
                AccentPanel VARCHAR(100),
                BaseVinyl VARCHAR(100),
                ColorPackage VARCHAR(100),
                TrimAccent VARCHAR(100)
            )
        """)

        # Bulk load
        csv_path = csv_file.name.replace('\\', '/')
        mysql_cursor.execute(f"""
            LOAD DATA LOCAL INFILE '{csv_path}'
            INTO TABLE temp_serial_master
            FIELDS TERMINATED BY ','
            OPTIONALLY ENCLOSED BY '"'
            LINES TERMINATED BY '\n'
        """)

        # Insert (skip duplicates)
        mysql_cursor.execute("""
            INSERT IGNORE INTO SerialNumberMaster (
                SN_MY, Boat_SerialNo, BoatItemNo, Series, BoatDesc1, SerialModelYear,
                ERP_OrderNo, InvoiceNo, InvoiceDate, DealerNumber, DealerName,
                DealerCity, DealerState, DealerZip, DealerCountry, WebOrderNo, Active,
                ProdNo, BenningtonOwned, PanelColor, AccentPanel, BaseVinyl, ColorPackage, TrimAccent
            )
            SELECT
                SN_MY, Boat_SerialNo, BoatItemNo, Series, BoatDesc1, SerialModelYear,
                ERP_OrderNo, InvoiceNo, InvoiceDate, DealerNumber, DealerName,
                DealerCity, DealerState, DealerZip, DealerCountry, WebOrderNo, Active,
                ProdNo, BenningtonOwned, PanelColor, AccentPanel, BaseVinyl, ColorPackage, TrimAccent
            FROM temp_serial_master
        """)
        inserted = mysql_cursor.rowcount

        mysql_cursor.execute("DROP TEMPORARY TABLE temp_serial_master")

        log(f"✅ Inserted {inserted} boats into SerialNumberMaster")
        return inserted, len(boats) - inserted

    finally:
        os.unlink(csv_file.name)


def bulk_insert_registration_status(mysql_cursor, boats: List[Dict]) -> Tuple[int, int]:
    """Bulk insert boats into SerialNumberRegistrationStatus."""
    if not boats:
        return 0, 0

    log(f"Preparing {len(boats)} boats for SerialNumberRegistrationStatus bulk insert...")

    csv_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='_reg_status.csv', newline='')

    try:
        writer = csv.writer(csv_file)
        for boat in boats:
            writer.writerow([
                boat.get('SN_MY', ''),
                boat.get('BoatSerialNo', ''),
                0,  # Registered
                0,  # FieldInventory
                0,  # Unknown
                0,  # SND
                0   # BenningtonOwned
            ])
        csv_file.close()

        # Create temp table
        mysql_cursor.execute("""
            CREATE TEMPORARY TABLE temp_reg_status (
                SN_MY VARCHAR(4),
                Boat_SerialNo VARCHAR(50),
                Registered INT,
                FieldInventory INT,
                Unknown_col INT,
                SND INT,
                BenningtonOwned INT
            )
        """)

        # Bulk load
        csv_path = csv_file.name.replace('\\', '/')
        mysql_cursor.execute(f"""
            LOAD DATA LOCAL INFILE '{csv_path}'
            INTO TABLE temp_reg_status
            FIELDS TERMINATED BY ','
            LINES TERMINATED BY '\n'
        """)

        # Insert (skip duplicates)
        mysql_cursor.execute("""
            INSERT IGNORE INTO SerialNumberRegistrationStatus (
                SN_MY, Boat_SerialNo, Registered, FieldInventory, `Unknown`, SND, BenningtonOwned
            )
            SELECT
                SN_MY, Boat_SerialNo, Registered, FieldInventory, Unknown_col, SND, BenningtonOwned
            FROM temp_reg_status
        """)
        inserted = mysql_cursor.rowcount

        mysql_cursor.execute("DROP TEMPORARY TABLE temp_reg_status")

        log(f"✅ Inserted {inserted} boats into SerialNumberRegistrationStatus")
        return inserted, len(boats) - inserted

    finally:
        os.unlink(csv_file.name)


def print_summary(total_boats: int, master_inserted: int, master_skipped: int,
                  status_inserted: int, status_skipped: int):
    """Print summary of import results."""
    print("\n" + "=" * 80)
    print("IMPORT SUMMARY")
    print("=" * 80)
    print(f"Total boats from MSSQL:           {total_boats}")
    print(f"SerialNumberMaster inserted:      {master_inserted} ({master_skipped} skipped/duplicates)")
    print(f"RegistrationStatus inserted:      {status_inserted} ({status_skipped} skipped/duplicates)")
    print(f"MSSQL Source:                     PRD ({MSSQL_CONFIG['server']})")
    print(f"MySQL Target:                     {MYSQL_CONFIG['database']}")
    print(f"Completed:                        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)


def main():
    print("=" * 80)
    print("BULK IMPORT BOATS TO SERIALNUMBERMASTER")
    print("=" * 80)
    print(f"MSSQL Source: PRD ({MSSQL_CONFIG['server']} / {MSSQL_DATABASE})")
    print(f"MySQL Target: {MYSQL_CONFIG['database']} ({MYSQL_CONFIG['host']})")
    print(f"Order Date Cutoff: {ORDER_DATE_CUTOFF}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()

    try:
        # Step 1: Extract all invoiced boats from MSSQL
        log("STEP 1: Extracting invoiced boats from MSSQL...")
        raw_boats = extract_boats_from_mssql()

        if not raw_boats:
            log("No boats found in MSSQL!", "ERROR")
            sys.exit(1)

        # Step 2: Fetch color/config attributes in bulk
        log("STEP 2: Fetching color/config attributes...")
        config_colors = fetch_color_fields_bulk(raw_boats)

        # Step 3: Connect to MySQL and check existing
        log("STEP 3: Connecting to MySQL and checking existing boats...")
        mysql_conn = mysql.connector.connect(
            **MYSQL_CONFIG,
            allow_local_infile=True
        )
        mysql_cursor = mysql_conn.cursor(buffered=True)

        existing_master = get_existing_serials(mysql_cursor)
        existing_status = get_existing_registration_serials(mysql_cursor)

        # Step 4: Prepare boats for insert (only new ones)
        log("STEP 4: Preparing boats for insert...")

        new_for_master = []
        new_for_status = []

        for boat in raw_boats:
            serial = boat.get('BoatSerialNo')
            if not serial:
                continue

            # Derive model year from serial number
            sn_my = get_model_year_from_serial(serial)
            if not sn_my:
                # Fallback: try from invoice date
                inv_date = boat.get('InvoiceDate')
                if inv_date:
                    try:
                        date_str = str(int(inv_date))
                        if len(date_str) >= 4:
                            sn_my = date_str[2:4]
                    except (ValueError, TypeError):
                        pass
            if not sn_my:
                sn_my = datetime.now().strftime('%y')

            full_year = get_full_model_year(sn_my)

            # Merge color fields from config attributes
            config_id = boat.get('ConfigId')
            cfg_colors = config_colors.get(config_id, {}) if config_id else {}

            # PanelColor: prefer coitem field, fallback to config attribute
            panel_color = boat.get('PanelColor') or cfg_colors.get('PanelColor_cfg') or ''

            prepared = {
                'SN_MY': sn_my,
                'BoatSerialNo': serial,
                'BoatItemNo': boat.get('BoatItemNo') or '',
                'Series': boat.get('Series') or '',
                'BoatDesc1': boat.get('BoatDesc1') or '',
                'SerialModelYear': full_year,
                'ERP_OrderNo': boat.get('ERP_OrderNo') or '',
                'InvoiceNo': boat.get('InvoiceNo') or '',
                'InvoiceDate': boat.get('InvoiceDate') or '',
                'DealerNumber': boat.get('DealerNumber', '').lstrip('0') or '',
                'DealerName': boat.get('DealerName') or '',
                'DealerCity': boat.get('DealerCity') or '',
                'DealerState': boat.get('DealerState') or '',
                'DealerZip': boat.get('DealerZip') or '',
                'DealerCountry': boat.get('DealerCountry') or '',
                'WebOrderNo': boat.get('WebOrderNo') or '',
                'ProdNo': boat.get('ProdNo') or '',
                'BenningtonOwned': boat.get('BenningtonOwned') or '',
                'PanelColor': panel_color,
                'AccentPanel': cfg_colors.get('AccentPanel') or '',
                'BaseVinyl': boat.get('BaseVinyl') or '',
                'ColorPackage': cfg_colors.get('ColorPackage') or '',
                'TrimAccent': cfg_colors.get('TrimAccent') or ''
            }

            if serial not in existing_master:
                new_for_master.append(prepared)

            if serial not in existing_status:
                new_for_status.append(prepared)

        log(f"Found {len(new_for_master)} new boats for SerialNumberMaster")
        log(f"Found {len(new_for_status)} new boats for SerialNumberRegistrationStatus")

        if not new_for_master and not new_for_status:
            log("No new boats to insert. Everything is up to date.")
            mysql_cursor.close()
            mysql_conn.close()
            print_summary(len(raw_boats), 0, 0, 0, 0)
            return

        # Step 5: Bulk insert
        log("STEP 5: Inserting new boats...")

        master_inserted, master_skipped = 0, 0
        status_inserted, status_skipped = 0, 0

        if new_for_master:
            master_inserted, master_skipped = bulk_insert_serial_master(mysql_cursor, new_for_master)
            mysql_conn.commit()

        if new_for_status:
            status_inserted, status_skipped = bulk_insert_registration_status(mysql_cursor, new_for_status)
            mysql_conn.commit()

        mysql_cursor.close()
        mysql_conn.close()
        log("✅ Database connection closed")

        # Summary
        print_summary(len(raw_boats), master_inserted, master_skipped,
                      status_inserted, status_skipped)

    except Exception as e:
        log(f"Fatal error: {str(e)}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

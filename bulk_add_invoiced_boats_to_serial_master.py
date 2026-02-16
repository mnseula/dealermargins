#!/usr/bin/env python3
"""
Bulk Add Invoiced Boats to SerialNumberMaster

This script processes ALL invoiced boats from BoatOptions tables and adds them to
SerialNumberMaster and SerialNumberRegistrationStatus with their ACTUAL dealer information.

Unlike add_boat_to_serial_master.py which adds one boat with a test dealer, this script:
- Finds all invoiced boats across all BoatOptions tables
- Gets actual dealer information from the ERP system
- Adds each boat with its real dealer
- Processes multiple boats in bulk

The script queries MSSQL for boat orders with dealer information, then inserts into MySQL.

Usage:
    # Staging (default)
    python3 bulk_add_invoiced_boats_to_serial_master.py
    
    # Production
    python3 bulk_add_invoiced_boats_to_serial_master.py --prd

Command Line Arguments:
    --prd, --production    Use production MSSQL database (CSIPRD)
                           Default is staging (CSISTG) if not specified

Optional arguments:
    --limit N        Process only N boats (for testing)
    --dry-run        Show what would be done without making changes
    --year YYYY      Process only boats from specific year (e.g., 2026)

Examples:
    python3 bulk_add_invoiced_boats_to_serial_master.py
    python3 bulk_add_invoiced_boats_to_serial_master.py --limit 10 --dry-run
    python3 bulk_add_invoiced_boats_to_serial_master.py --year 2026
    python3 bulk_add_invoiced_boats_to_serial_master.py --prd --year 2026

Author: Claude Code
Date: 2026-02-12
"""

import sys
import argparse
from datetime import datetime
from typing import List, Dict, Tuple
import pymssql
import mysql.connector
from mysql.connector import Error as MySQLError

# ============================================================================
# COMMAND LINE ARGUMENTS
# ============================================================================

parser = argparse.ArgumentParser(
    description='Bulk add invoiced boats to SerialNumberMaster',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
    # Staging (default)
    python3 bulk_add_invoiced_boats_to_serial_master.py
    python3 bulk_add_invoiced_boats_to_serial_master.py --limit 10 --dry-run
    python3 bulk_add_invoiced_boats_to_serial_master.py --year 2026
    
    # Production
    python3 bulk_add_invoiced_boats_to_serial_master.py --prd
    python3 bulk_add_invoiced_boats_to_serial_master.py --prd --year 2026
    
    # In JAMS - Staging job:
    Command: python3 bulk_add_invoiced_boats_to_serial_master.py
    
    # In JAMS - Production job:
    Command: python3 bulk_add_invoiced_boats_to_serial_master.py --prd
    """
)
parser.add_argument(
    '--prd', '--production',
    action='store_true',
    dest='use_production',
    default=False,
    help='Use production MSSQL database (CSIPRD). Default is staging (CSISTG).'
)
parser.add_argument(
    '--limit',
    type=int,
    metavar='N',
    help='Process only N boats (for testing)'
)
parser.add_argument(
    '--dry-run',
    action='store_true',
    help='Show what would be done without making changes'
)
parser.add_argument(
    '--year',
    type=int,
    metavar='YYYY',
    help='Process only boats from specific year (e.g., 2026)'
)
args = parser.parse_args()

# ============================================================================
# DATABASE CONFIGURATIONS
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

# MySQL (Destination - SerialNumberMaster)
MYSQL_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'warrantyparts',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD'
}

# ============================================================================
# SQL QUERIES
# ============================================================================

# Query to get invoiced boats with dealer information from ERP
MSSQL_BOAT_QUERY = """
-- Get invoiced boats with dealer information
SELECT DISTINCT
    -- Boat serial number (HIN)
    COALESCE(
        NULLIF(coi.Uf_BENN_BoatSerialNumber, ''),
        ser.ser_num
    ) AS BoatSerialNo,

    -- Boat model and description
    coi.item AS BoatItemNo,
    coi.description AS BoatDesc1,
    im.Uf_BENN_Series AS Series,

    -- Order and invoice info
    coi.co_num AS ERP_OrderNo,
    LEFT(coi.Uf_BENN_BoatWebOrderNumber, 30) AS WebOrderNo,
    iim.inv_num AS InvoiceNo,
    CASE
        WHEN ah.inv_date IS NOT NULL
        THEN CONVERT(INT, CONVERT(VARCHAR(8), ah.inv_date, 112))
        ELSE NULL
    END AS InvoiceDate,

    -- Dealer information
    co.cust_num AS DealerNumber,
    cust.name AS DealerName,
    cust.city AS DealerCity,
    cust.state AS DealerState,
    cust.zip AS DealerZip,
    cust.country AS DealerCountry,

    -- Additional fields
    coi.Uf_BENN_BoatModel AS BoatModelNo,
    co.order_date AS OrderDate

FROM [CSISTG].[dbo].[coitem_mst] coi

-- Join to get serial number (for CPQ boats)
LEFT JOIN [CSISTG].[dbo].[serial_mst] ser
    ON coi.co_num = ser.ref_num
    AND coi.co_line = ser.ref_line
    AND coi.co_release = ser.ref_release
    AND coi.item = ser.item
    AND coi.site_ref = ser.site_ref
    AND ser.ref_type = 'O'

-- Join to get invoice
INNER JOIN [CSISTG].[dbo].[inv_item_mst] iim
    ON coi.co_num = iim.co_num
    AND coi.co_line = iim.co_line
    AND coi.co_release = iim.co_release
    AND coi.site_ref = iim.site_ref

-- Join to get invoice date
INNER JOIN [CSISTG].[dbo].[arinv_mst] ah
    ON iim.inv_num = ah.inv_num
    AND iim.site_ref = ah.site_ref

-- Join to get order details
INNER JOIN [CSISTG].[dbo].[co_mst] co
    ON coi.co_num = co.co_num
    AND coi.site_ref = co.site_ref

-- Join to get item details
LEFT JOIN [CSISTG].[dbo].[item_mst] im
    ON coi.item = im.item
    AND coi.site_ref = im.site_ref

-- Join to get dealer/customer information
LEFT JOIN [CSISTG].[dbo].[customer_mst] cust
    ON co.cust_num = cust.cust_num
    AND co.site_ref = cust.site_ref

WHERE coi.site_ref = 'BENN'
    -- Must be a boat item (BOA or BOI material cost type)
    AND im.Uf_BENN_MaterialCostType IN ('BOA', 'BOI')
    -- Must have serial number
    AND (
        (coi.Uf_BENN_BoatSerialNumber IS NOT NULL AND coi.Uf_BENN_BoatSerialNumber != '')
        OR ser.ser_num IS NOT NULL
    )
    -- Must be invoiced
    AND iim.inv_num IS NOT NULL
    AND coi.qty_invoiced > 0
    -- Only recent orders (adjust date as needed)
    AND co.order_date >= '2015-01-01'
    {year_filter}
    {limit_clause}

ORDER BY BoatSerialNo
"""

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def log(message: str, level: str = "INFO"):
    """Print timestamped log message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def detect_model_year_from_serial(serial_number: str) -> str:
    """
    Detect model year from serial number suffix.
    Returns 2-digit year (e.g., '26' for 2026).
    """
    if not serial_number or len(serial_number) < 2:
        return datetime.now().strftime('%y')

    try:
        year_suffix = serial_number[-2:]
        year_int = int(year_suffix)

        # Determine century: 00-50 = 2000s, 51-99 = 1900s
        if year_int <= 50:
            full_year = 2000 + year_int
        else:
            full_year = 1900 + year_int

        return str(full_year)[-2:]  # Return last 2 digits
    except:
        return datetime.now().strftime('%y')

def get_invoiced_boats_from_erp(year_filter: str = None, limit: int = None) -> List[Dict]:
    """
    Query MSSQL ERP system for invoiced boats with dealer information.
    Returns list of boat records with dealer details.
    """
    log("Connecting to MSSQL (ERP database)...")

    try:
        conn = pymssql.connect(**MSSQL_CONFIG)
        cursor = conn.cursor(as_dict=True)
        log("✅ Connected to MSSQL")

        # Build query with optional filters
        query = MSSQL_BOAT_QUERY

        # Add year filter if specified
        if year_filter:
            query = query.replace('{year_filter}', f"AND YEAR(co.order_date) = {year_filter}")
        else:
            query = query.replace('{year_filter}', '')

        # Add limit if specified
        if limit:
            query = query.replace('{limit_clause}', f'TOP {limit}')
        else:
            query = query.replace('{limit_clause}', '')

        log(f"Querying invoiced boats from ERP{f' (year={year_filter})' if year_filter else ''}{f' (limit={limit})' if limit else ''}...")
        cursor.execute(query)
        rows = cursor.fetchall()

        log(f"✅ Found {len(rows):,} invoiced boats in ERP")

        cursor.close()
        conn.close()

        return rows

    except pymssql.Error as e:
        log(f"MSSQL error: {e}", "ERROR")
        raise
    except Exception as e:
        log(f"Unexpected error: {e}", "ERROR")
        raise

def check_existing_boats(cursor, serial_numbers: List[str]) -> Tuple[set, set]:
    """
    Check which boats already exist in SerialNumberMaster and SerialNumberRegistrationStatus.
    Returns (set of serials in master, set of serials in status).
    """
    if not serial_numbers:
        return set(), set()

    # Check SerialNumberMaster
    placeholders = ','.join(['%s'] * len(serial_numbers))
    cursor.execute(
        f"SELECT Boat_SerialNo FROM SerialNumberMaster WHERE Boat_SerialNo IN ({placeholders})",
        serial_numbers
    )
    in_master = {row[0] for row in cursor.fetchall()}

    # Check SerialNumberRegistrationStatus
    cursor.execute(
        f"SELECT Boat_SerialNo FROM SerialNumberRegistrationStatus WHERE Boat_SerialNo IN ({placeholders})",
        serial_numbers
    )
    in_status = {row[0] for row in cursor.fetchall()}

    return in_master, in_status

def insert_boats_batch(cursor, boats: List[Dict], dry_run: bool = False) -> Tuple[int, int]:
    """
    Insert boats into SerialNumberMaster and SerialNumberRegistrationStatus in batch.
    Returns (master_count, status_count) of successful insertions.
    """
    if not boats:
        return 0, 0

    master_count = 0
    status_count = 0

    # Prepare batch data for SerialNumberMaster
    master_insert = """
        INSERT INTO SerialNumberMaster (
            SN_MY,
            Boat_SerialNo,
            BoatItemNo,
            Series,
            BoatDesc1,
            SerialModelYear,
            ERP_OrderNo,
            InvoiceNo,
            InvoiceDateYYYYMMDD,
            DealerNumber,
            DealerName,
            DealerCity,
            DealerState,
            DealerZip,
            DealerCountry,
            WebOrderNo,
            Active
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            BoatItemNo = VALUES(BoatItemNo),
            Series = VALUES(Series),
            BoatDesc1 = VALUES(BoatDesc1),
            ERP_OrderNo = VALUES(ERP_OrderNo),
            InvoiceNo = VALUES(InvoiceNo),
            InvoiceDateYYYYMMDD = VALUES(InvoiceDateYYYYMMDD),
            DealerNumber = VALUES(DealerNumber),
            DealerName = VALUES(DealerName),
            DealerCity = VALUES(DealerCity),
            DealerState = VALUES(DealerState),
            DealerZip = VALUES(DealerZip),
            DealerCountry = VALUES(DealerCountry),
            WebOrderNo = VALUES(WebOrderNo)
    """

    # Prepare batch data for SerialNumberRegistrationStatus
    status_insert = """
        INSERT INTO SerialNumberRegistrationStatus (
            SN_MY,
            Boat_SerialNo,
            Registered,
            FieldInventory,
            Unknown,
            SND,
            BenningtonOwned
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            SN_MY = VALUES(SN_MY)
    """

    master_data = []
    status_data = []

    for boat in boats:
        model_year = detect_model_year_from_serial(boat['BoatSerialNo'])

        # Prepare SerialNumberMaster data
        master_data.append((
            model_year,                           # SN_MY
            boat['BoatSerialNo'],                 # Boat_SerialNo
            boat['BoatItemNo'],                   # BoatItemNo
            boat['Series'] or '',                 # Series
            boat['BoatDesc1'] or '',              # BoatDesc1
            f"20{model_year}",                    # SerialModelYear
            boat['ERP_OrderNo'],                  # ERP_OrderNo
            boat['InvoiceNo'],                    # InvoiceNo
            boat['InvoiceDate'],                  # InvoiceDateYYYYMMDD
            boat['DealerNumber'] or '',           # DealerNumber
            boat['DealerName'] or 'UNKNOWN',      # DealerName
            boat['DealerCity'] or '',             # DealerCity
            boat['DealerState'] or '',            # DealerState
            boat['DealerZip'] or '',              # DealerZip
            boat['DealerCountry'] or 'US',        # DealerCountry
            boat['WebOrderNo'] or '',             # WebOrderNo
            0                                      # Active (0 = unregistered)
        ))

        # Prepare SerialNumberRegistrationStatus data
        status_data.append((
            model_year,                # SN_MY
            boat['BoatSerialNo'],      # Boat_SerialNo
            0,                         # Registered (0 = not registered)
            0,                         # FieldInventory
            0,                         # Unknown
            0,                         # SND
            0                          # BenningtonOwned
        ))

    if dry_run:
        log(f"[DRY RUN] Would insert {len(master_data)} boats into SerialNumberMaster")
        log(f"[DRY RUN] Would insert {len(status_data)} boats into SerialNumberRegistrationStatus")
        return len(master_data), len(status_data)

    try:
        # Insert into SerialNumberMaster
        cursor.executemany(master_insert, master_data)
        master_count = cursor.rowcount
        log(f"✅ Inserted/updated {master_count} records in SerialNumberMaster")

        # Insert into SerialNumberRegistrationStatus
        cursor.executemany(status_insert, status_data)
        status_count = cursor.rowcount
        log(f"✅ Inserted/updated {status_count} records in SerialNumberRegistrationStatus")

        return master_count, status_count

    except MySQLError as e:
        log(f"MySQL error during batch insert: {e}", "ERROR")
        raise

def print_summary(total_boats: int, existing_master: int, existing_status: int,
                 inserted_master: int, inserted_status: int, dry_run: bool):
    """Print summary statistics"""
    print("\n" + "="*80)
    print("BULK ADD INVOICED BOATS - SUMMARY")
    print("="*80)
    print(f"\nTotal invoiced boats found: {total_boats:,}")
    print(f"Already in SerialNumberMaster: {existing_master:,}")
    print(f"Already in SerialNumberRegistrationStatus: {existing_status:,}")
    print(f"\n{'[DRY RUN] Would insert' if dry_run else 'Inserted/Updated'}:")
    print(f"  SerialNumberMaster: {inserted_master:,} records")
    print(f"  SerialNumberRegistrationStatus: {inserted_status:,} records")
    print("="*80)
    if dry_run:
        print("\n⚠️  This was a DRY RUN - no changes were made")
        print("Run without --dry-run to actually insert the data")
    else:
        print("\n✅ BULK INSERT COMPLETE")
    print("="*80)

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description='Bulk add invoiced boats to SerialNumberMaster with actual dealer information'
    )
    parser.add_argument('--limit', type=int, help='Process only N boats (for testing)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--year', type=int, help='Process only boats from specific year (e.g., 2026)')

    args = parser.parse_args()

    print("="*80)
    print("BULK ADD INVOICED BOATS TO SERIALNUMBERMASTER")
    print("="*80)
    print(f"Mode: {'DRY RUN' if args.dry_run else 'PRODUCTION'}")
    if args.limit:
        print(f"Limit: {args.limit} boats")
    if args.year:
        print(f"Year filter: {args.year}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print()

    try:
        # Step 1: Get invoiced boats from ERP with dealer information
        boats = get_invoiced_boats_from_erp(year_filter=args.year, limit=args.limit)

        if not boats:
            log("No invoiced boats found in ERP", "WARNING")
            sys.exit(0)

        # Extract serial numbers for existence check
        serial_numbers = [boat['BoatSerialNo'] for boat in boats if boat['BoatSerialNo']]

        if not serial_numbers:
            log("No boats with valid serial numbers found", "WARNING")
            sys.exit(0)

        log(f"Processing {len(serial_numbers):,} boats with valid serial numbers...")

        # Step 2: Connect to MySQL and check existing boats
        log("Connecting to MySQL database...")
        mysql_conn = mysql.connector.connect(**MYSQL_CONFIG)
        mysql_cursor = mysql_conn.cursor()
        log("✅ Connected to MySQL")

        log("Checking which boats already exist...")
        existing_master, existing_status = check_existing_boats(mysql_cursor, serial_numbers)

        log(f"Found {len(existing_master):,} boats already in SerialNumberMaster")
        log(f"Found {len(existing_status):,} boats already in SerialNumberRegistrationStatus")

        # Step 3: Filter to boats that need to be added (not in BOTH tables)
        # We'll insert/update all boats, ON DUPLICATE KEY UPDATE handles existing ones
        boats_to_process = [boat for boat in boats if boat['BoatSerialNo']]

        log(f"Processing {len(boats_to_process):,} boats...")

        # Step 4: Insert boats in batches
        batch_size = 1000
        total_master = 0
        total_status = 0

        for i in range(0, len(boats_to_process), batch_size):
            batch = boats_to_process[i:i + batch_size]
            log(f"Processing batch {i//batch_size + 1} ({len(batch)} boats)...")

            master_count, status_count = insert_boats_batch(mysql_cursor, batch, dry_run=args.dry_run)
            total_master += master_count
            total_status += status_count

            if not args.dry_run:
                mysql_conn.commit()
                log(f"✅ Committed batch {i//batch_size + 1}")

        # Step 5: Print summary
        print_summary(
            total_boats=len(boats),
            existing_master=len(existing_master),
            existing_status=len(existing_status),
            inserted_master=total_master,
            inserted_status=total_status,
            dry_run=args.dry_run
        )

        # Close connection
        mysql_cursor.close()
        mysql_conn.close()
        log("✅ Database connection closed")

        sys.exit(0)

    except KeyboardInterrupt:
        log("Process cancelled by user", "WARNING")
        sys.exit(1)
    except Exception as e:
        log(f"Process failed: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

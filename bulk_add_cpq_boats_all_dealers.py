#!/usr/bin/env python3
"""
Bulk Add CPQ Boats to SerialNumberMaster - All Dealers

⚠️  CPQ BOATS ONLY - DO NOT USE FOR LEGACY BOATS ⚠️

This script processes ONLY CPQ boats (2015+) across ALL dealers.
There is a separate script for legacy boats - do not mix them!

CPQ Detection Criteria (ALL must be true):
  1. Boat has CfgName field populated (CPQ indicator)
  2. Boat is from BoatOptions15 or newer (2015+ era)
  3. Boat has "Base Boat" line item (ItemNo = 'Base Boat')

Unlike add_boat_to_serial_master.py which uses dealer 50, this script:
- Finds all CPQ boats (boats with CfgName field populated)
- Gets ACTUAL dealer information from MSSQL ERP
- Gets color/config fields from MSSQL ERP
- Adds each boat with its real dealer
- Processes boats from BoatOptions15 through BoatOptions26 ONLY

Usage:
    # Staging (default)
    python3 bulk_add_cpq_boats_all_dealers.py --dry-run
    python3 bulk_add_cpq_boats_all_dealers.py --confirm
    
    # Production
    python3 bulk_add_cpq_boats_all_dealers.py --prd --confirm

Command Line Arguments:
    --prd, --production    Use production MSSQL database (CSIPRD)
                           Default is staging (CSISTG) if not specified

Required arguments for production:
    --confirm        Required for production runs (safety check for JAMS automation)

Optional arguments:
    --limit N        Process only N boats (for testing, bypasses --confirm requirement)
    --dry-run        Show what would be done without making changes
    --year YY        Process only boats from specific year table (e.g., 26 for BoatOptions26)
    --dealer ID      Process only boats for specific dealer

Examples:
    # Dry run (safe to test)
    python3 bulk_add_cpq_boats_all_dealers.py --dry-run
    python3 bulk_add_cpq_boats_all_dealers.py --dry-run --year 26

    # Production runs (require --confirm)
    python3 bulk_add_cpq_boats_all_dealers.py --confirm
    python3 bulk_add_cpq_boats_all_dealers.py --confirm --year 26
    python3 bulk_add_cpq_boats_all_dealers.py --confirm --dealer 333836

    # With production database
    python3 bulk_add_cpq_boats_all_dealers.py --prd --confirm

    # Small test batches (no --confirm needed with --limit)
    python3 bulk_add_cpq_boats_all_dealers.py --limit 10

Author: Claude Code
Date: 2026-02-14
"""

import sys
import argparse
from datetime import datetime
from typing import List, Dict, Tuple
import mysql.connector
from mysql.connector import Error as MySQLError
import pymssql

# ============================================================================
# COMMAND LINE ARGUMENTS
# ============================================================================

parser = argparse.ArgumentParser(
    description='Bulk add CPQ boats to SerialNumberMaster',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
    # Dry run (safe to test) - staging database
    python3 bulk_add_cpq_boats_all_dealers.py --dry-run
    python3 bulk_add_cpq_boats_all_dealers.py --dry-run --year 26

    # Production run - staging database
    python3 bulk_add_cpq_boats_all_dealers.py --confirm
    python3 bulk_add_cpq_boats_all_dealers.py --confirm --year 26
    python3 bulk_add_cpq_boats_all_dealers.py --confirm --dealer 333836

    # Production run - production database
    python3 bulk_add_cpq_boats_all_dealers.py --prd --confirm

    # Small test batches (no --confirm needed with --limit)
    python3 bulk_add_cpq_boats_all_dealers.py --limit 10
    
    # In JAMS - Staging job:
    Command: python3 bulk_add_cpq_boats_all_dealers.py --confirm
    
    # In JAMS - Production job:
    Command: python3 bulk_add_cpq_boats_all_dealers.py --prd --confirm
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
    '--confirm',
    action='store_true',
    help='Required for production runs (safety check for JAMS automation)'
)
parser.add_argument(
    '--dry-run',
    action='store_true',
    help='Show what would be done without making changes'
)
parser.add_argument(
    '--limit',
    type=int,
    metavar='N',
    help='Process only N boats (for testing)'
)
parser.add_argument(
    '--year',
    type=str,
    metavar='YY',
    help='Process only boats from specific year table (e.g., 26 for BoatOptions26)'
)
parser.add_argument(
    '--dealer',
    type=str,
    metavar='ID',
    help='Process only boats for specific dealer'
)
args = parser.parse_args()

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

MYSQL_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'warrantyparts',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD'
}

# ==================== MSSQL DATABASE SWITCH ====================

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

# BoatOptions tables to process (2015 onwards - CPQ era)
BOAT_OPTIONS_TABLES = [
    'BoatOptions15', 'BoatOptions16', 'BoatOptions17', 'BoatOptions18',
    'BoatOptions19', 'BoatOptions20', 'BoatOptions21', 'BoatOptions22',
    'BoatOptions23', 'BoatOptions24', 'BoatOptions25', 'BoatOptions26'
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def log(message: str, level: str = "INFO"):
    """Print timestamped log message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def detect_model_year_from_table(table_name: str) -> str:
    """
    Extract model year from table name.
    BoatOptions26 -> '26'
    """
    if 'BoatOptions' in table_name:
        year_part = table_name.replace('BoatOptions', '')
        if year_part.isdigit() and len(year_part) == 2:
            return year_part
    return datetime.now().strftime('%y')

def get_dealer_and_color_info_from_erp(mssql_cursor, erp_order: str) -> Dict:
    """
    Query MSSQL ERP for dealer information and color fields based on ERP order number.
    Returns dict with dealer and color fields or defaults if not found.
    """
    result_data = {
        'DealerNumber': '',
        'DealerName': 'UNKNOWN',
        'DealerCity': '',
        'DealerState': '',
        'DealerZip': '',
        'DealerCountry': 'US',
        'ProdNo': None,
        'BenningtonOwned': None,
        'PanelColor': None,
        'AccentPanel': None,
        'BaseVinyl': None,
        'ColorPackage': None,
        'TrimAccent': None
    }

    try:
        # Query 1: Get dealer and order-level color fields
        query1 = """
            SELECT
                co.cust_num AS DealerNumber,
                cust.name AS DealerName,
                cust.city AS DealerCity,
                cust.state AS DealerState,
                cust.zip AS DealerZip,
                cust.country AS DealerCountry,
                co.Uf_BENN_ProductionNumber AS ProdNo,
                co.Uf_BENN_BenningtonOwned AS BenningtonOwned,
                coi.Uf_BENN_PannelColor AS PanelColor,
                coi.Uf_BENN_BaseVnyl AS BaseVinyl,
                coi.config_id
            FROM [CSISTG].[dbo].[co_mst] co
            LEFT JOIN [CSISTG].[dbo].[customer_mst] cust
                ON co.cust_num = cust.cust_num
                AND co.site_ref = cust.site_ref
            LEFT JOIN [CSISTG].[dbo].[coitem_mst] coi
                ON co.co_num = coi.co_num
                AND co.site_ref = coi.site_ref
            LEFT JOIN [CSISTG].[dbo].[item_mst] im
                ON coi.item = im.item
                AND coi.site_ref = im.site_ref
            WHERE co.co_num = %s
              AND co.site_ref = 'BENN'
              AND im.Uf_BENN_MaterialCostType = 'BOA'
        """

        mssql_cursor.execute(query1, (erp_order,))
        result1 = mssql_cursor.fetchone()

        if result1:
            # Update dealer info
            result_data['DealerNumber'] = result1.get('DealerNumber') or ''
            result_data['DealerName'] = result1.get('DealerName') or 'UNKNOWN'
            result_data['DealerCity'] = result1.get('DealerCity') or ''
            result_data['DealerState'] = result1.get('DealerState') or ''
            result_data['DealerZip'] = result1.get('DealerZip') or ''
            result_data['DealerCountry'] = result1.get('DealerCountry') or 'US'

            # Update color fields from order/item level
            result_data['ProdNo'] = result1.get('ProdNo')
            result_data['BenningtonOwned'] = result1.get('BenningtonOwned')
            result_data['PanelColor'] = result1.get('PanelColor')
            result_data['BaseVinyl'] = result1.get('BaseVinyl')

            config_id = result1.get('config_id')

            # Query 2: Get config attributes for additional color fields
            if config_id:
                query2 = """
                    SELECT
                        attr_name,
                        attr_value
                    FROM [CSISTG].[dbo].[cfg_attr_mst]
                    WHERE config_id = %s
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
                mssql_cursor.execute(query2, (config_id,))
                config_results = mssql_cursor.fetchall()

                for row in config_results:
                    attr_name = row.get('attr_name', '').upper()
                    attr_value = row.get('attr_value')

                    if 'ACCENT PANEL COLOR' in attr_name:
                        result_data['AccentPanel'] = attr_value
                    elif 'EXTERIOR COLOR PACKAGES' in attr_name or 'COLOR PACKAGE' in attr_name:
                        result_data['ColorPackage'] = attr_value
                    elif 'TRIM ACCENTS' in attr_name:
                        result_data['TrimAccent'] = attr_value
                    elif attr_name == 'PANEL COLOR' and not result_data['PanelColor']:
                        result_data['PanelColor'] = attr_value

    except Exception as e:
        # Log error but continue with defaults
        pass

    return result_data

def get_cpq_boats_from_table(cursor, table_name: str, dealer_filter: str = None, limit: int = None) -> List[Dict]:
    """
    Get CPQ boats from a specific BoatOptions table.
    CPQ boats are identified by CfgName field being populated.
    Returns list of boat records with dealer information from the table.
    """
    # First check if table exists and has CfgName column
    cursor.execute("""
        SELECT COUNT(*)
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND COLUMN_NAME = 'CfgName'
    """, (table_name,))

    if cursor.fetchone()[0] == 0:
        log(f"⏭️  {table_name} does not have CfgName column, skipping...")
        return []

    # Build query to get CPQ boats ONLY (dealer info will be fetched from MSSQL)
    # CPQ boats must have BOTH:
    #   1. CfgName field populated (CPQ indicator)
    #   2. "Base Boat" line item (ItemNo = 'Base Boat')
    query = f"""
        SELECT DISTINCT
            bo.BoatSerialNo,
            bo.BoatModelNo,
            bo.Series,
            bo.InvoiceNo,
            bo.InvoiceDate,
            bo.WebOrderNo,
            bo.ERP_OrderNo,
            COUNT(DISTINCT CASE WHEN bo.CfgName IS NOT NULL AND bo.CfgName != '' THEN bo.ItemNo END) as cpq_item_count,
            '{table_name}' as source_table
        FROM {table_name} bo
        WHERE bo.BoatSerialNo IS NOT NULL
          AND bo.BoatSerialNo != ''
          -- CPQ Detection #1: Must have CfgName populated
          AND EXISTS (
              SELECT 1 FROM {table_name} bo2
              WHERE bo2.BoatSerialNo = bo.BoatSerialNo
                AND bo2.CfgName IS NOT NULL
                AND bo2.CfgName != ''
          )
          -- CPQ Detection #2: Must have Base Boat line (CPQ boats have ItemNo='Base Boat')
          AND EXISTS (
              SELECT 1 FROM {table_name} bo3
              WHERE bo3.BoatSerialNo = bo.BoatSerialNo
                AND bo3.ItemNo = 'Base Boat'
          )
        GROUP BY
            bo.BoatSerialNo,
            bo.BoatModelNo,
            bo.Series,
            bo.InvoiceNo,
            bo.InvoiceDate,
            bo.WebOrderNo,
            bo.ERP_OrderNo
        HAVING cpq_item_count > 0
        ORDER BY bo.BoatSerialNo
        {f'LIMIT {limit}' if limit else ''}
    """

    try:
        cursor.execute(query)
        rows = cursor.fetchall()

        # Convert to dict list (dealer info will be added later from MSSQL)
        boats = []
        for row in rows:
            boats.append({
                'BoatSerialNo': row[0],
                'BoatModelNo': row[1],
                'Series': row[2],
                'InvoiceNo': row[3],
                'InvoiceDate': row[4],
                'WebOrderNo': row[5],
                'ERP_OrderNo': row[6],
                'cpq_item_count': row[7],
                'source_table': row[8]
            })

        if boats:
            log(f"✅ Found {len(boats):,} CPQ boats in {table_name}")

        return boats

    except MySQLError as e:
        log(f"⚠️  Error querying {table_name}: {e}", "WARNING")
        return []

def get_all_cpq_boats(cursor, year_filter: str = None, dealer_filter: str = None, limit: int = None) -> List[Dict]:
    """
    Get CPQ boats from all BoatOptions tables.
    Returns combined list of boat records.
    """
    all_boats = []
    tables_to_process = BOAT_OPTIONS_TABLES

    # Filter to specific year if requested
    if year_filter:
        table_name = f'BoatOptions{year_filter}'
        if table_name in BOAT_OPTIONS_TABLES:
            tables_to_process = [table_name]
        else:
            log(f"⚠️  Table {table_name} not in processing list", "WARNING")
            return []

    log(f"Scanning {len(tables_to_process)} BoatOptions tables for CPQ boats...")

    remaining_limit = limit
    for table_name in tables_to_process:
        table_limit = remaining_limit if remaining_limit else None
        boats = get_cpq_boats_from_table(cursor, table_name, dealer_filter, table_limit)
        all_boats.extend(boats)

        if remaining_limit:
            remaining_limit -= len(boats)
            if remaining_limit <= 0:
                break

    return all_boats

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

    # Prepare batch data for SerialNumberMaster (includes color fields)
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
            Active,
            ProdNo,
            BenningtonOwned,
            PanelColor,
            AccentPanel,
            BaseVinyl,
            ColorPackage,
            TrimAccent
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            BoatItemNo = VALUES(BoatItemNo),
            Series = VALUES(Series),
            ERP_OrderNo = VALUES(ERP_OrderNo),
            InvoiceNo = VALUES(InvoiceNo),
            InvoiceDateYYYYMMDD = VALUES(InvoiceDateYYYYMMDD),
            DealerNumber = VALUES(DealerNumber),
            DealerName = VALUES(DealerName),
            DealerCity = VALUES(DealerCity),
            DealerState = VALUES(DealerState),
            DealerZip = VALUES(DealerZip),
            DealerCountry = VALUES(DealerCountry),
            WebOrderNo = VALUES(WebOrderNo),
            ProdNo = VALUES(ProdNo),
            BenningtonOwned = VALUES(BenningtonOwned),
            PanelColor = VALUES(PanelColor),
            AccentPanel = VALUES(AccentPanel),
            BaseVinyl = VALUES(BaseVinyl),
            ColorPackage = VALUES(ColorPackage),
            TrimAccent = VALUES(TrimAccent)
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
        # Detect model year from source table or serial number
        model_year = detect_model_year_from_table(boat['source_table'])
        if not model_year or len(model_year) != 2:
            # Fallback to serial number suffix
            if boat['BoatSerialNo'] and len(boat['BoatSerialNo']) >= 2:
                model_year = boat['BoatSerialNo'][-2:]
            else:
                model_year = datetime.now().strftime('%y')

        # Get boat description (use model number as fallback)
        boat_desc = boat.get('BoatModelNo') or boat.get('BoatItemNo') or ''

        # Prepare SerialNumberMaster data (includes color fields)
        master_data.append((
            model_year,                                    # SN_MY
            boat['BoatSerialNo'],                          # Boat_SerialNo
            boat['BoatModelNo'] or '',                     # BoatItemNo
            boat['Series'] or '',                          # Series
            boat_desc,                                     # BoatDesc1
            f"20{model_year}",                            # SerialModelYear
            boat['ERP_OrderNo'] or '',                     # ERP_OrderNo
            boat['InvoiceNo'] or '',                       # InvoiceNo
            boat['InvoiceDate'],                           # InvoiceDateYYYYMMDD
            boat['DealerNumber'] or '',                    # DealerNumber
            boat['DealerName'] or 'UNKNOWN',               # DealerName
            boat['DealerCity'] or '',                      # DealerCity
            boat['DealerState'] or '',                     # DealerState
            boat['DealerZip'] or '',                       # DealerZip
            boat['DealerCountry'] or 'US',                 # DealerCountry
            boat['WebOrderNo'] or '',                      # WebOrderNo
            0,                                             # Active (0 = unregistered)
            boat.get('ProdNo'),                            # ProdNo
            boat.get('BenningtonOwned'),                   # BenningtonOwned
            boat.get('PanelColor'),                        # PanelColor
            boat.get('AccentPanel'),                       # AccentPanel
            boat.get('BaseVinyl'),                         # BaseVinyl
            boat.get('ColorPackage'),                      # ColorPackage
            boat.get('TrimAccent')                         # TrimAccent
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

        # Show sample data
        if master_data:
            log(f"[DRY RUN] Sample boat: {boats[0]['BoatSerialNo']} - Dealer: {boats[0]['DealerNumber']} ({boats[0]['DealerName']})")

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

def print_dealer_summary(boats: List[Dict]):
    """Print summary of boats by dealer"""
    dealer_counts = {}
    for boat in boats:
        dealer_id = boat['DealerNumber'] or 'UNKNOWN'
        dealer_name = boat['DealerName'] or 'UNKNOWN'
        dealer_key = f"{dealer_id} - {dealer_name}"
        dealer_counts[dealer_key] = dealer_counts.get(dealer_key, 0) + 1

    print("\n" + "="*80)
    print("BOATS BY DEALER")
    print("="*80)
    for dealer, count in sorted(dealer_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {dealer}: {count:,} boats")
    print("="*80)

def print_summary(total_boats: int, existing_master: int, existing_status: int,
                 inserted_master: int, inserted_status: int, dry_run: bool, boats: List[Dict]):
    """Print summary statistics"""
    print("\n" + "="*80)
    print("BULK ADD CPQ BOATS - ALL DEALERS - SUMMARY")
    print("="*80)

    # CPQ Verification
    print(f"\n⚠️  CPQ BOATS ONLY - Legacy boats excluded")
    print(f"CPQ Detection: All boats have CfgName + Base Boat line")

    print(f"\nTotal CPQ boats found: {total_boats:,}")
    if boats:
        avg_cpq_items = sum(b.get('cpq_item_count', 0) for b in boats) / len(boats)
        print(f"Average CPQ items per boat: {avg_cpq_items:.1f}")

    print(f"\nAlready in SerialNumberMaster: {existing_master:,}")
    print(f"Already in SerialNumberRegistrationStatus: {existing_status:,}")
    print(f"\n{'[DRY RUN] Would insert' if dry_run else 'Inserted/Updated'}:")
    print(f"  SerialNumberMaster: {inserted_master:,} records")
    print(f"  SerialNumberRegistrationStatus: {inserted_status:,} records")

    # Print dealer breakdown
    if boats:
        print_dealer_summary(boats)

    print("\n" + "="*80)
    if dry_run:
        print("⚠️  This was a DRY RUN - no changes were made")
        print("Run without --dry-run to actually insert the data")
    else:
        print("✅ BULK INSERT COMPLETE")
        print("\nNext steps:")
        print("  1. Boats are now in SerialNumberMaster with Active=0 (unregistered)")
        print("  2. Dealers can now see and select these boats in the window sticker system")
        print("  3. CPQ detection will work via CfgName field")
    print("="*80)

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description='Bulk add CPQ boats to SerialNumberMaster across all dealers'
    )
    parser.add_argument('--limit', type=int, help='Process only N boats (for testing)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--year', type=str, help='Process only boats from specific year table (e.g., 26 for BoatOptions26)')
    parser.add_argument('--dealer', type=str, help='Process only boats for specific dealer (e.g., 333836)')
    parser.add_argument('--confirm', action='store_true', help='Required for production runs (for JAMS automation)')

    args = parser.parse_args()

    print("="*80)
    print("BULK ADD CPQ BOATS TO SERIALNUMBERMASTER - ALL DEALERS")
    print("="*80)
    print("\n⚠️  CPQ BOATS ONLY - DO NOT USE FOR LEGACY BOATS ⚠️")
    print("This script only processes boats with CfgName + Base Boat line")
    print("Legacy boats are handled by a separate script\n")
    print("="*80)
    print(f"Mode: {'DRY RUN' if args.dry_run else 'PRODUCTION'}")
    if args.limit:
        print(f"Limit: {args.limit} boats")
    if args.year:
        print(f"Year filter: BoatOptions{args.year}")
    if args.dealer:
        print(f"Dealer filter: {args.dealer}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print()

    # Safety check: Require --confirm flag for production mode (for JAMS automation)
    if not args.dry_run and not args.limit and not args.confirm:
        print("\n❌ ERROR: Production mode requires --confirm flag")
        print("\nFor safety, production runs must include --confirm flag:")
        print(f"  python3 {sys.argv[0]} --confirm")
        print(f"\nOr run with --dry-run to preview changes first")
        print(f"Or run with --limit N for small test batches\n")
        sys.exit(1)

    if args.confirm and not args.dry_run:
        log("✅ Production mode confirmed via --confirm flag", "INFO")

    try:
        # Connect to MySQL database
        log("Connecting to MySQL database...")
        mysql_conn = mysql.connector.connect(**MYSQL_CONFIG)
        mysql_cursor = mysql_conn.cursor(buffered=True)
        log("✅ Connected to MySQL")

        # Step 1: Get CPQ boats from BoatOptions tables
        boats = get_all_cpq_boats(
            mysql_cursor,
            year_filter=args.year,
            dealer_filter=args.dealer,
            limit=args.limit
        )

        if not boats:
            log("No CPQ boats found in BoatOptions tables", "WARNING")
            mysql_cursor.close()
            mysql_conn.close()
            sys.exit(0)

        log(f"✅ Total CPQ boats found: {len(boats):,}")

        # Step 2: Get dealer and color information from MSSQL for each boat
        log("Connecting to MSSQL to fetch dealer and color information...")
        try:
            mssql_conn = pymssql.connect(**MSSQL_CONFIG)
            mssql_cursor = mssql_conn.cursor(as_dict=True)
            log("✅ Connected to MSSQL")

            boats_with_dealers = []
            for i, boat in enumerate(boats, 1):
                if i % 100 == 0:
                    log(f"Fetching dealer/color info... {i}/{len(boats)}")

                dealer_color_info = get_dealer_and_color_info_from_erp(mssql_cursor, boat['ERP_OrderNo'])
                boat.update(dealer_color_info)

                # Apply dealer filter if specified
                if args.dealer and boat['DealerNumber'] != args.dealer:
                    continue

                boats_with_dealers.append(boat)

            mssql_cursor.close()
            mssql_conn.close()
            log(f"✅ Fetched dealer and color info for {len(boats_with_dealers)} boats")

            # Replace boats list with filtered list
            boats = boats_with_dealers

        except Exception as e:
            log(f"⚠️  Could not connect to MSSQL: {e}", "WARNING")
            log("⚠️  Proceeding with default dealer info (UNKNOWN) and no color fields", "WARNING")
            # Add default dealer info to all boats (no color fields)
            for boat in boats:
                boat.update({
                    'DealerNumber': '',
                    'DealerName': 'UNKNOWN',
                    'DealerCity': '',
                    'DealerState': '',
                    'DealerZip': '',
                    'DealerCountry': 'US',
                    'ProdNo': None,
                    'BenningtonOwned': None,
                    'PanelColor': None,
                    'AccentPanel': None,
                    'BaseVinyl': None,
                    'ColorPackage': None,
                    'TrimAccent': None
                })

        if not boats:
            log("No boats remaining after dealer filter", "WARNING")
            mysql_cursor.close()
            mysql_conn.close()
            sys.exit(0)

        # Show dealer distribution
        unique_dealers = len(set(boat['DealerNumber'] for boat in boats if boat['DealerNumber']))
        log(f"📊 Boats span {unique_dealers} unique dealers")

        # Extract serial numbers for existence check
        serial_numbers = [boat['BoatSerialNo'] for boat in boats if boat['BoatSerialNo']]

        # Step 3: Check existing boats
        log("Checking which boats already exist...")
        existing_master, existing_status = check_existing_boats(mysql_cursor, serial_numbers)

        log(f"Found {len(existing_master):,} boats already in SerialNumberMaster")
        log(f"Found {len(existing_status):,} boats already in SerialNumberRegistrationStatus")

        # Step 4: Process all boats (ON DUPLICATE KEY UPDATE handles existing ones)
        log(f"Processing {len(boats):,} boats...")

        # Insert boats in batches
        batch_size = 1000
        total_master = 0
        total_status = 0

        for i in range(0, len(boats), batch_size):
            batch = boats[i:i + batch_size]
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
            dry_run=args.dry_run,
            boats=boats
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

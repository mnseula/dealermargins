#!/usr/bin/env python3
"""
Add Boat to SerialNumberMaster and SerialNumberRegistrationStatus

This script adds a boat from the appropriate BoatOptions table to the SerialNumberMaster and
SerialNumberRegistrationStatus tables using test dealer 50 (PONTOON BOAT, LLC).

The script automatically determines which BoatOptions table to use based on the last 2 digits
of the hull serial number (e.g., ETWINVTEST0126 -> BoatOptions26).

Usage:
    # Staging (default)
    python3 add_boat_to_serial_master.py <hull_number> <erp_order>
    
    # Production
    python3 add_boat_to_serial_master.py --prd <hull_number> <erp_order>

Command Line Arguments:
    --prd, --production    Use production MSSQL database (CSIPRD)
                           Default is staging (CSISTG) if not specified

Example:
    python3 add_boat_to_serial_master.py ETWINVTEST0126 SO00936076
    python3 add_boat_to_serial_master.py --prd ETWINVTEST0126 SO00936076

Author: Claude Code
Date: 2026-02-09
"""

import mysql.connector
from mysql.connector import Error
import pymssql
import sys
import argparse
from datetime import datetime

# ==================== COMMAND LINE ARGUMENTS ====================

parser = argparse.ArgumentParser(
    description='Add boat to SerialNumberMaster and SerialNumberRegistrationStatus',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
    # Staging (default)
    python3 add_boat_to_serial_master.py ETWINVTEST0126 SO00936076
    
    # Production
    python3 add_boat_to_serial_master.py --prd ETWINVTEST0126 SO00936076
    
    # In JAMS - Staging job:
    Command: python3 add_boat_to_serial_master.py {{HULL_NUMBER}} {{ERP_ORDER}}
    
    # In JAMS - Production job:
    Command: python3 add_boat_to_serial_master.py --prd {{HULL_NUMBER}} {{ERP_ORDER}}
    """
)
parser.add_argument(
    '--prd', '--production',
    action='store_true',
    dest='use_production',
    default=False,
    help='Use production MSSQL database (CSIPRD). Default is staging (CSISTG).'
)
parser.add_argument('hull_number', help='Boat hull serial number')
parser.add_argument('erp_order', help='ERP order number')
args = parser.parse_args()

# ==================== CONFIGURATION ====================

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'warrantyparts',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD'
}

# Test dealer information (Dealer ID 50)
TEST_DEALER = {
    'DealerNumber': 50,
    'DealerName': 'PONTOON BOAT, LLC',
    'DealerCity': 'ELKHART',
    'DealerState': 'IN',
    'DealerZip': '46514',
    'DealerCountry': 'US'
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

# ==================== HELPER FUNCTIONS ====================

def log(message: str, level: str = "INFO"):
    """Print timestamped log message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def get_color_fields_from_mssql(erp_order: str) -> dict:
    """
    Query MSSQL for color and configuration fields.
    Returns dict with ProdNo, BenningtonOwned, PanelColor, AccentPanel, BaseVinyl, ColorPackage, TrimAccent
    """
    try:
        conn = pymssql.connect(**MSSQL_CONFIG)
        cursor = conn.cursor(as_dict=True)
        
        # Query 1: Get order-level fields and BOA line fields
        query1 = """
        SELECT 
            co.Uf_BENN_ProductionNumber AS ProdNo,
            co.Uf_BENN_BenningtonOwned AS BenningtonOwned,
            coi.Uf_BENN_PannelColor AS PanelColor,
            coi.Uf_BENN_BaseVnyl AS BaseVinyl,
            coi.config_id
        FROM [CSISTG].[dbo].[co_mst] co
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
        
        cursor.execute(query1, (erp_order,))
        result1 = cursor.fetchone()
        
        color_data = {
            'ProdNo': None,
            'BenningtonOwned': None,
            'PanelColor': None,
            'AccentPanel': None,
            'BaseVinyl': None,
            'ColorPackage': None,
            'TrimAccent': None
        }
        
        if result1:
            color_data['ProdNo'] = result1.get('ProdNo')
            color_data['BenningtonOwned'] = result1.get('BenningtonOwned')
            color_data['PanelColor'] = result1.get('PanelColor')
            color_data['BaseVinyl'] = result1.get('BaseVinyl')
            config_id = result1.get('config_id')
            
            # Query 2: Get config attributes for color fields
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
                cursor.execute(query2, (config_id,))
                config_results = cursor.fetchall()
                
                for row in config_results:
                    attr_name = row.get('attr_name', '').upper()
                    attr_value = row.get('attr_value')
                    
                    if 'ACCENT PANEL COLOR' in attr_name:
                        color_data['AccentPanel'] = attr_value
                    elif 'EXTERIOR COLOR PACKAGES' in attr_name or 'COLOR PACKAGE' in attr_name:
                        color_data['ColorPackage'] = attr_value
                    elif 'TRIM ACCENTS' in attr_name:
                        color_data['TrimAccent'] = attr_value
                    elif attr_name == 'PANEL COLOR' and not color_data['PanelColor']:
                        color_data['PanelColor'] = attr_value
        
        cursor.close()
        conn.close()
        
        return color_data
        
    except Exception as e:
        log(f"⚠️  Could not fetch color fields from MSSQL: {e}", "WARNING")
        return {
            'ProdNo': None,
            'BenningtonOwned': None,
            'PanelColor': None,
            'AccentPanel': None,
            'BaseVinyl': None,
            'ColorPackage': None,
            'TrimAccent': None
        }

def get_table_name_from_hull(hull_number: str) -> str:
    """
    Determine the BoatOptions table name from the hull number.
    Uses the last 2 digits of the serial number for new format (2015+),
    or searches appropriate legacy tables for older boats.
    Examples:
        ETWINVTEST0126 -> BoatOptions26
        ETWINVTEST0104 -> BoatOptions99_04 (for older test boats)
        ETW123456789 -> BoatOptions89
    """
    if len(hull_number) < 2:
        return None
    
    # Extract last 2 digits
    year_digits = hull_number[-2:]
    
    # For year 99-04 range, use the combined table
    try:
        year_int = int(year_digits)
        if 0 <= year_int <= 4 or year_int == 99:
            return "BoatOptions99_04"
        elif 5 <= year_int <= 7:
            return "BoatOptions05_07"
        elif 8 <= year_int <= 10:
            return "BoatOptions08_10"
        elif 11 <= year_int <= 14:
            return "BoatOptions11_14"
        else:
            return f"BoatOptions{year_digits}"
    except ValueError:
        return f"BoatOptions{year_digits}"

def get_model_year_from_invoice(invoice_date) -> str:
    """
    Extract model year from invoice date (format: YYYYMMDD).
    Returns 2-digit year (e.g., '26' for 2026).
    Falls back to current year if invoice_date is invalid.
    """
    if invoice_date:
        try:
            # Invoice date format is typically YYYYMMDD
            date_str = str(invoice_date)
            if len(date_str) >= 4:
                year = int(date_str[:4])
                return str(year)[-2:]  # Return last 2 digits
        except (ValueError, TypeError):
            pass
    
    # Fallback to current year
    from datetime import datetime
    return datetime.now().strftime('%y')

def search_all_tables(cursor, hull_number: str, erp_order: str):
    """
    Search all BoatOptions tables to find the boat.
    Handles both old format (integer ERP_OrderNo) and new format (string ERP_OrderNo).
    Returns (row, table_name) or (None, None) if not found.
    """
    # Get all BoatOptions tables
    cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = DATABASE() 
        AND table_name LIKE 'BoatOptions%'
        ORDER BY table_name
    """)
    
    tables = [row[0] for row in cursor.fetchall()]
    
    for table_name in tables:
        try:
            # Try with string format first (new tables)
            query = f"""
                SELECT
                    BoatSerialNo,
                    ItemNo,
                    ItemDesc1,
                    Series,
                    InvoiceNo,
                    InvoiceDate,
                    WebOrderNo,
                    ERP_OrderNo
                FROM {table_name}
                WHERE BoatSerialNo = %s
                  AND ItemMasterMCT = 'BOA'
            """
            
            cursor.execute(query, (hull_number,))
            row = cursor.fetchone()
            
            if row:
                # Check if ERP_OrderNo matches (handle both int and string)
                db_order = row[7]
                if db_order == erp_order or str(db_order) == erp_order or str(db_order) in erp_order:
                    return row, table_name
                # If erp_order is "0" in DB, accept any order number (for test boats)
                if db_order == 0 or db_order == "0":
                    return row, table_name
                    
        except Exception as e:
            # Table might have different schema, skip
            continue
    
    return None, None

def get_boat_info(cursor, hull_number: str, erp_order: str) -> dict:
    """
    Get boat information from the appropriate BoatOptions table.
    Returns dict with boat details or None if not found.
    """
    # First try the expected table based on hull number
    table_name = get_table_name_from_hull(hull_number)
    
    if table_name:
        log(f"Looking in {table_name} based on hull number pattern...")
        
        # Check if table exists
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = DATABASE() AND table_name = %s
        """, (table_name,))
        
        if cursor.fetchone()[0] > 0:
            try:
                query = f"""
                    SELECT
                        BoatSerialNo,
                        ItemNo,
                        ItemDesc1,
                        Series,
                        InvoiceNo,
                        InvoiceDate,
                        WebOrderNo,
                        ERP_OrderNo
                    FROM {table_name}
                    WHERE BoatSerialNo = %s
                      AND ItemMasterMCT = 'BOA'
                    LIMIT 1
                """
                
                cursor.execute(query, (hull_number,))
                row = cursor.fetchone()
                
                if row:
                    # Check if ERP_OrderNo matches
                    db_order = row[7]
                    if db_order == erp_order or str(db_order) == erp_order or str(db_order) in erp_order:
                        log(f"✅ Found boat in {table_name}")
                        model_year = get_model_year_from_invoice(row[5])  # Use invoice date for model year
                        return {
                            'serial_number': row[0],
                            'model': row[1],
                            'description': row[2],
                            'series': row[3],
                            'invoice_no': row[4],
                            'invoice_date': row[5],
                            'web_order_no': row[6],
                            'model_year': model_year,
                            'erp_order': erp_order,
                            'table_name': table_name
                        }
                    elif db_order == 0 or db_order == "0":
                        log(f"✅ Found boat in {table_name} (ERP_OrderNo is 0, accepting match)")
                        model_year = get_model_year_from_invoice(row[5])  # Use invoice date for model year
                        return {
                            'serial_number': row[0],
                            'model': row[1],
                            'description': row[2],
                            'series': row[3],
                            'invoice_no': row[4],
                            'invoice_date': row[5],
                            'web_order_no': row[6],
                            'model_year': model_year,
                            'erp_order': erp_order,
                            'table_name': table_name
                        }
            except Exception as e:
                log(f"⚠️  Error querying {table_name}: {e}", "WARNING")
    
    # If not found, search all tables
    log("Boat not found in expected table, searching all BoatOptions tables...")
    row, found_table = search_all_tables(cursor, hull_number, erp_order)
    
    if row:
        log(f"✅ Found boat in {found_table}")
        model_year = get_model_year_from_invoice(row[5])  # Use invoice date for model year
        return {
            'serial_number': row[0],
            'model': row[1],
            'description': row[2],
            'series': row[3],
            'invoice_no': row[4],
            'invoice_date': row[5],
            'web_order_no': row[6],
            'model_year': model_year,
            'erp_order': erp_order,
            'table_name': found_table
        }
    
    return None

def check_if_exists(cursor, hull_number: str) -> tuple:
    """
    Check if boat already exists in SerialNumberMaster and/or SerialNumberRegistrationStatus.
    Returns (exists_in_master, exists_in_status)
    """
    cursor.execute(
        "SELECT COUNT(*) FROM SerialNumberMaster WHERE Boat_SerialNo = %s",
        (hull_number,)
    )
    in_master = cursor.fetchone()[0] > 0

    cursor.execute(
        "SELECT COUNT(*) FROM SerialNumberRegistrationStatus WHERE Boat_SerialNo = %s",
        (hull_number,)
    )
    in_status = cursor.fetchone()[0] > 0

    return in_master, in_status

def insert_serial_number_master(cursor, boat_info: dict) -> bool:
    """
    Insert boat into SerialNumberMaster.
    Returns True on success, False on failure.
    """
    insert_query = """
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
    """

    values = (
        boat_info['model_year'],           # SN_MY
        boat_info['serial_number'],        # Boat_SerialNo
        boat_info['model'],                # BoatItemNo
        boat_info['series'],               # Series
        boat_info['description'],          # BoatDesc1
        f"20{boat_info['model_year']}",   # SerialModelYear
        boat_info['erp_order'],            # ERP_OrderNo
        boat_info['invoice_no'],           # InvoiceNo
        boat_info['invoice_date'],         # InvoiceDateYYYYMMDD
        TEST_DEALER['DealerNumber'],       # DealerNumber
        TEST_DEALER['DealerName'],         # DealerName
        TEST_DEALER['DealerCity'],         # DealerCity
        TEST_DEALER['DealerState'],        # DealerState
        TEST_DEALER['DealerZip'],          # DealerZip
        TEST_DEALER['DealerCountry'],      # DealerCountry
        boat_info['web_order_no'],         # WebOrderNo
        0,                                  # Active (0 = unregistered)
        boat_info.get('ProdNo'),           # ProdNo
        boat_info.get('BenningtonOwned'),  # BenningtonOwned
        boat_info.get('PanelColor'),       # PanelColor
        boat_info.get('AccentPanel'),      # AccentPanel
        boat_info.get('BaseVinyl'),        # BaseVinyl
        boat_info.get('ColorPackage'),     # ColorPackage
        boat_info.get('TrimAccent')        # TrimAccent
    )

    try:
        cursor.execute(insert_query, values)
        return True
    except Error as e:
        log(f"Error inserting into SerialNumberMaster: {e}", "ERROR")
        return False

def insert_serial_number_registration_status(cursor, boat_info: dict) -> bool:
    """
    Insert boat into SerialNumberRegistrationStatus.
    Returns True on success, False on failure.
    """
    insert_query = """
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
    """

    values = (
        boat_info['model_year'],      # SN_MY
        boat_info['serial_number'],   # Boat_SerialNo
        0,                             # Registered (0 = not registered)
        0,                             # FieldInventory
        0,                             # Unknown
        0,                             # SND
        0                              # BenningtonOwned
    )

    try:
        cursor.execute(insert_query, values)
        return True
    except Error as e:
        log(f"Error inserting into SerialNumberRegistrationStatus: {e}", "ERROR")
        return False

# ==================== MAIN EXECUTION ====================

def main():
    """Main execution"""
    if len(sys.argv) != 3:
        print("Usage: python3 add_boat_to_serial_master.py <hull_number> <erp_order>")
        print("Example: python3 add_boat_to_serial_master.py ETWINVTEST0126 SO00936076")
        sys.exit(1)

    hull_number = sys.argv[1]
    erp_order = sys.argv[2]

    print("=" * 80)
    print("ADD BOAT TO SERIALNUMBERMASTER")
    print("=" * 80)
    print(f"Hull Number:  {hull_number}")
    print(f"ERP Order:    {erp_order}")
    print(f"Test Dealer:  {TEST_DEALER['DealerNumber']} ({TEST_DEALER['DealerName']})")
    print(f"Started:      {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    try:
        # Connect to database
        log("Connecting to database...")
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(buffered=True)
        log("✅ Connected to database")

        # Get boat information from appropriate BoatOptions table
        table_name = get_table_name_from_hull(hull_number)
        log(f"Fetching boat info for {hull_number} from {table_name}...")
        boat_info = get_boat_info(cursor, hull_number, erp_order)

        if not boat_info:
            log(f"❌ Boat not found in {table_name}", "ERROR")
            log(f"   Hull Number: {hull_number}", "ERROR")
            log(f"   ERP Order: {erp_order}", "ERROR")
            sys.exit(1)

        log(f"✅ Boat found in {boat_info['table_name']}")
        log(f"   Model: {boat_info['model']} ({boat_info['description']})")
        log(f"   Series: {boat_info['series']}")
        log(f"   Model Year: 20{boat_info['model_year']}")
        log(f"   Invoice: {boat_info['invoice_no']}")
        log(f"   Invoice Date: {boat_info['invoice_date']}")

        # Fetch color and config fields from MSSQL
        log("Fetching color and configuration fields from MSSQL...")
        color_fields = get_color_fields_from_mssql(erp_order)
        boat_info.update(color_fields)
        
        if color_fields['PanelColor']:
            log(f"   PanelColor: {color_fields['PanelColor']}")
        if color_fields['AccentPanel']:
            log(f"   AccentPanel: {color_fields['AccentPanel']}")
        if color_fields['BaseVinyl']:
            log(f"   BaseVinyl: {color_fields['BaseVinyl']}")

        # Check if boat already exists
        log("Checking if boat already exists...")
        in_master, in_status = check_if_exists(cursor, hull_number)

        if in_master:
            log(f"⚠️  Boat already exists in SerialNumberMaster", "WARNING")
        if in_status:
            log(f"⚠️  Boat already exists in SerialNumberRegistrationStatus", "WARNING")

        if in_master and in_status:
            log("❌ Boat already exists in both tables. Exiting.", "ERROR")
            sys.exit(1)

        # Insert into SerialNumberMaster
        if not in_master:
            log("Adding boat to SerialNumberMaster...")
            if insert_serial_number_master(cursor, boat_info):
                log("✅ Added to SerialNumberMaster")
            else:
                log("❌ Failed to add to SerialNumberMaster", "ERROR")
                sys.exit(1)
        else:
            log("⏭️  Skipping SerialNumberMaster (already exists)")

        # Insert into SerialNumberRegistrationStatus
        if not in_status:
            log("Adding boat to SerialNumberRegistrationStatus...")
            if insert_serial_number_registration_status(cursor, boat_info):
                log("✅ Added to SerialNumberRegistrationStatus")
            else:
                log("❌ Failed to add to SerialNumberRegistrationStatus", "ERROR")
                sys.exit(1)
        else:
            log("⏭️  Skipping SerialNumberRegistrationStatus (already exists)")

        # Commit transaction
        log("Committing transaction...")
        conn.commit()
        log("✅ Transaction committed")

        # Verify insertion
        log("\nVerifying insertion...")
        cursor.execute(
            "SELECT Active FROM SerialNumberMaster WHERE Boat_SerialNo = %s",
            (hull_number,)
        )
        master_row = cursor.fetchone()

        cursor.execute(
            "SELECT Registered FROM SerialNumberRegistrationStatus WHERE Boat_SerialNo = %s",
            (hull_number,)
        )
        status_row = cursor.fetchone()

        print("\n" + "=" * 80)
        print("✅ BOAT SUCCESSFULLY ADDED")
        print("=" * 80)
        print(f"Hull Number:       {hull_number}")
        print(f"Model:             {boat_info['model']} ({boat_info['description']})")
        print(f"Series:            {boat_info['series']}")
        print(f"Invoice:           {boat_info['invoice_no']}")
        print(f"Dealer:            {TEST_DEALER['DealerNumber']} ({TEST_DEALER['DealerName']})")
        print(f"Active:            {master_row[0] if master_row else 'N/A'} (0 = unregistered)")
        print(f"Registered:        {status_row[0] if status_row else 'N/A'} (0 = not sold)")
        if boat_info.get('PanelColor') or boat_info.get('AccentPanel') or boat_info.get('BaseVinyl'):
            print("\nColor/Configuration Fields:")
            if boat_info.get('PanelColor'):
                print(f"  PanelColor:      {boat_info['PanelColor']}")
            if boat_info.get('AccentPanel'):
                print(f"  AccentPanel:     {boat_info['AccentPanel']}")
            if boat_info.get('BaseVinyl'):
                print(f"  BaseVinyl:       {boat_info['BaseVinyl']}")
            if boat_info.get('ColorPackage'):
                print(f"  ColorPackage:    {boat_info['ColorPackage']}")
            if boat_info.get('TrimAccent'):
                print(f"  TrimAccent:      {boat_info['TrimAccent']}")
        print("\nUnregistered Invoiced Boat Status:")
        print(f"  ✅ InvoiceNo IS NOT NULL: {boat_info['invoice_no']}")
        print(f"  ✅ Active = 0: {master_row[0] == 0 if master_row else False}")
        print(f"  ✅ Registered = 0: {status_row[0] == 0 if status_row else False}")
        print("=" * 80)

        # Close connection
        cursor.close()
        conn.close()
        log("✅ Database connection closed")

        sys.exit(0)

    except Error as e:
        log(f"Database error: {e}", "ERROR")
        sys.exit(1)
    except Exception as e:
        log(f"Unexpected error: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

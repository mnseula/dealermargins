#!/usr/bin/env python3
"""
Add Boat to SerialNumberMaster and SerialNumberRegistrationStatus

This script adds a boat from BoatOptions26 to the SerialNumberMaster and
SerialNumberRegistrationStatus tables using test dealer 50 (PONTOON BOAT, LLC).

Usage:
    python3 add_boat_to_serial_master.py <hull_number> <erp_order>

Example:
    python3 add_boat_to_serial_master.py ETWINVTEST0126 SO00936076

Author: Claude Code
Date: 2026-02-09
"""

import mysql.connector
from mysql.connector import Error
import sys
from datetime import datetime

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

# ==================== HELPER FUNCTIONS ====================

def log(message: str, level: str = "INFO"):
    """Print timestamped log message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def get_boat_info(cursor, hull_number: str, erp_order: str) -> dict:
    """
    Get boat information from BoatOptions26.
    Returns dict with boat details or None if not found.
    """
    query = """
        SELECT
            BoatSerialNo,
            ItemNo,
            ItemDesc1,
            Series,
            InvoiceNo,
            InvoiceDate,
            WebOrderNo
        FROM BoatOptions26
        WHERE BoatSerialNo = %s
          AND ERP_OrderNo = %s
          AND ItemMasterMCT = 'BOA'
        LIMIT 1
    """

    cursor.execute(query, (hull_number, erp_order))
    row = cursor.fetchone()

    if not row:
        return None

    # Extract model year from hull number (last 2 digits)
    model_year = hull_number[-2:] if len(hull_number) >= 2 else None

    return {
        'serial_number': row[0],
        'model': row[1],
        'description': row[2],
        'series': row[3],
        'invoice_no': row[4],
        'invoice_date': row[5],
        'web_order_no': row[6],
        'model_year': model_year,
        'erp_order': erp_order
    }

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
            Active
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
        0                                   # Active (0 = unregistered)
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
        cursor = conn.cursor()
        log("✅ Connected to database")

        # Get boat information from BoatOptions26
        log(f"Fetching boat info for {hull_number}...")
        boat_info = get_boat_info(cursor, hull_number, erp_order)

        if not boat_info:
            log(f"❌ Boat not found in BoatOptions26", "ERROR")
            log(f"   Hull Number: {hull_number}", "ERROR")
            log(f"   ERP Order: {erp_order}", "ERROR")
            sys.exit(1)

        log("✅ Boat found in BoatOptions26")
        log(f"   Model: {boat_info['model']} ({boat_info['description']})")
        log(f"   Series: {boat_info['series']}")
        log(f"   Model Year: 20{boat_info['model_year']}")
        log(f"   Invoice: {boat_info['invoice_no']}")
        log(f"   Invoice Date: {boat_info['invoice_date']}")

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

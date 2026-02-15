#!/usr/bin/env python3
"""Find recent invoiced boats for Short's Marine"""
import mysql.connector
from datetime import datetime, timedelta

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts'
}

def find_shorts_boats():
    """Find boats for Short's Marine dealer"""
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        print("\n" + "="*80)
        print("SEARCHING FOR SHORT'S MARINE BOATS")
        print("="*80 + "\n")

        # First, find Short's Marine serial numbers from SerialNumberMaster
        print("Step 1: Finding Short's Marine boats in SerialNumberMaster...")

        # Check if SerialNumberMaster table exists
        cursor.execute("SHOW TABLES LIKE 'PW_SerialNumberMaster'")
        if cursor.fetchone():
            cursor.execute("""
                SELECT Boat_SerialNo, DealerName, DealerNumber
                FROM PW_SerialNumberMaster
                WHERE DealerName LIKE '%SHORT%MARINE%'
                   OR DealerName LIKE '%PRICE MARINE%'
                ORDER BY Boat_SerialNo DESC
                LIMIT 50
            """)

            serial_results = cursor.fetchall()

            if serial_results:
                print(f"  Found {len(serial_results)} Short's Marine boats in SerialNumberMaster\n")
                shorts_serials = [r['Boat_SerialNo'] for r in serial_results]

                # Show first few
                for r in serial_results[:10]:
                    print(f"    {r['Boat_SerialNo']}: {r['DealerName']} (Dealer #{r['DealerNumber']})")
            else:
                print("  No Short's Marine boats found in SerialNumberMaster")
                shorts_serials = []
        else:
            print("  SerialNumberMaster table not found")
            shorts_serials = []

        print("\n" + "="*80)
        print("Step 2: Finding boats in BoatOptions tables")
        print("="*80)

        # Search in recent BoatOptions tables (23, 24, 25, 26)
        years = [23, 24, 25, 26]

        for year in years:
            table_name = f"BoatOptions{year}"

            print(f"\n{'='*80}")
            print(f"CHECKING {table_name}")
            print(f"{'='*80}")

            # Check if table exists
            cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
            if not cursor.fetchone():
                print(f"  ⚠️  Table {table_name} does not exist")
                continue

            if not shorts_serials:
                print(f"  Skipping {table_name} - no Short's Marine serials found")
                continue

            # Build query with serial numbers
            serial_list = "', '".join(shorts_serials[:50])  # Limit to 50 to avoid huge query

            query = f"""
                SELECT DISTINCT
                    b.BoatSerialNo,
                    b.BoatModelNo,
                    b.ItemDesc1 as BoatDescription,
                    b.InvoiceNo,
                    b.InvoiceDate,
                    b.ERP_OrderNo,
                    b.CfgName,
                    b.external_confirmation_ref,
                    b.MSRP,
                    b.ExtSalesAmount
                FROM {table_name} b
                WHERE b.BoatSerialNo IN ('{serial_list}')
                  AND b.ItemMasterMCT IN ('BOA', 'BOI')
                ORDER BY b.BoatSerialNo DESC
            """

            cursor.execute(query)
            boats = cursor.fetchall()

            if boats:
                print(f"\n  Found {len(boats)} Short's Marine boats in {table_name}:\n")

                for boat in boats:
                    print(f"  Serial: {boat['BoatSerialNo']}")
                    print(f"    Model: {boat['BoatModelNo']}")
                    print(f"    Description: {boat['BoatDescription']}")
                    print(f"    Invoice: {boat['InvoiceNo']} ({boat['InvoiceDate']})")
                    print(f"    ERP Order: {boat['ERP_OrderNo']}")
                    print(f"    External Ref: {boat['external_confirmation_ref']}")
                    print(f"    MSRP: ${boat['MSRP']}" if boat['MSRP'] else "    MSRP: None")
                    print(f"    Dealer Cost: ${boat['ExtSalesAmount']}" if boat['ExtSalesAmount'] else "    Dealer Cost: None")

                    # Determine if CPQ or legacy
                    has_cfg = boat['CfgName'] and boat['CfgName'] not in [None, '', 'NULL']
                    is_cpq_ref = boat['external_confirmation_ref'] and 'CPQ' in str(boat['external_confirmation_ref'])
                    boat_type = "CPQ BOAT" if (has_cfg or is_cpq_ref) else "LEGACY BOAT"
                    print(f"    CfgName: {boat['CfgName']}")
                    print(f"    Type: {boat_type}")
                    print()

            else:
                print(f"  No boats found in {table_name}")

        # Also check for specific models mentioned
        print("\n" + "="*80)
        print("SEARCHING FOR SPECIFIC MODELS (SSR, Mid Range)")
        print("="*80 + "\n")

        for year in years:
            table_name = f"BoatOptions{year}"

            # Check if table exists
            cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
            if not cursor.fetchone():
                continue

            if not shorts_serials:
                continue

            serial_list = "', '".join(shorts_serials[:50])

            query = f"""
                SELECT DISTINCT
                    BoatSerialNo,
                    BoatModelNo,
                    ItemDesc1,
                    CfgName,
                    external_confirmation_ref
                FROM {table_name}
                WHERE BoatSerialNo IN ('{serial_list}')
                  AND (BoatModelNo LIKE '%SSR%'
                   OR ItemDesc1 LIKE '%SSR%'
                   OR ItemDesc1 LIKE '%MID RANGE%'
                   OR ItemDesc1 LIKE '%FIGHTER%')
                  AND ItemMasterMCT IN ('BOA', 'BOI')
                ORDER BY BoatSerialNo DESC
                LIMIT 10
            """

            cursor.execute(query)
            specific_boats = cursor.fetchall()

            if specific_boats:
                print(f"\n{table_name} - Mid Range Fighter / SSR boats:")
                for boat in specific_boats:
                    print(f"  {boat['BoatSerialNo']}: {boat['BoatModelNo']} - {boat['ItemDesc1']}")
                    has_cfg = boat['CfgName'] and boat['CfgName'] not in [None, '', 'NULL']
                    print(f"    Type: {'CPQ' if has_cfg else 'LEGACY'}")

        cursor.close()
        connection.close()

    except mysql.connector.Error as e:
        print(f"❌ Database error: {e}")
        if connection and connection.is_connected():
            connection.close()

if __name__ == "__main__":
    find_shorts_boats()

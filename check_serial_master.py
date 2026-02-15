#!/usr/bin/env python3
"""Check if boats exist in PW_SerialNumberMaster table"""
import mysql.connector

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts'
}

def check_serial_master():
    """Check if boat exists in SerialNumberMaster"""
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        print("\n" + "="*80)
        print("CHECKING BOATS IN PW_SerialNumberMaster")
        print("="*80 + "\n")

        # Check if table exists
        cursor.execute("SHOW TABLES LIKE 'PW_SerialNumberMaster'")
        if not cursor.fetchone():
            print("❌ PW_SerialNumberMaster table does NOT exist!")
            print("\nSearching for similar tables...")
            cursor.execute("SHOW TABLES LIKE '%Serial%'")
            tables = cursor.fetchall()
            if tables:
                print("Found these tables with 'Serial' in name:")
                for table in tables:
                    print(f"  - {list(table.values())[0]}")
            else:
                print("No tables found with 'Serial' in name")
            return

        print("✅ PW_SerialNumberMaster table exists\n")

        # Check specific boat
        test_serial = 'ETWS0837A626'
        print(f"Looking for {test_serial}...")

        cursor.execute("""
            SELECT Boat_SerialNo, DealerName, DealerNumber, InvoiceDate
            FROM PW_SerialNumberMaster
            WHERE Boat_SerialNo = %s
        """, (test_serial,))

        result = cursor.fetchone()

        if result:
            print(f"✅ FOUND {test_serial} in SerialNumberMaster:")
            print(f"   Dealer: {result['DealerName']}")
            print(f"   Dealer #: {result['DealerNumber']}")
            print(f"   Invoice Date: {result['InvoiceDate']}")
        else:
            print(f"❌ {test_serial} NOT FOUND in SerialNumberMaster")
            print("\nThis is why you can't pull up the boat!")
            print("The boat exists in BoatOptions26 but not in SerialNumberMaster.")

        # Check all Short's Marine boats in SerialNumberMaster
        print("\n" + "="*80)
        print("ALL SHORT'S MARINE BOATS IN SerialNumberMaster")
        print("="*80 + "\n")

        cursor.execute("""
            SELECT Boat_SerialNo, DealerName, DealerNumber, InvoiceDate
            FROM PW_SerialNumberMaster
            WHERE DealerName LIKE '%SHORT%'
               OR DealerName LIKE '%PRICE MARINE%'
            ORDER BY Boat_SerialNo DESC
            LIMIT 50
        """)

        boats = cursor.fetchall()

        if boats:
            print(f"Found {len(boats)} Short's Marine boats:\n")

            # Group by model type
            ssr_boats = []
            other_boats = []

            for boat in boats:
                serial = boat['Boat_SerialNo']
                if serial:
                    # Check if it's a 23SSR by looking up in BoatOptions
                    cursor.execute("""
                        SELECT BoatModelNo, ItemDesc1
                        FROM BoatOptions26
                        WHERE BoatSerialNo = %s
                          AND ItemMasterMCT IN ('BOA', 'BOI')
                        LIMIT 1
                    """, (serial,))

                    boat_info = cursor.fetchone()
                    if boat_info and ('23SSR' in boat_info['BoatModelNo'] or '23 S STERN' in boat_info['ItemDesc1']):
                        ssr_boats.append({**boat, 'model': boat_info['BoatModelNo']})
                    else:
                        other_boats.append(boat)

            if ssr_boats:
                print(f"23SSR BOATS ({len(ssr_boats)}):")
                print("-" * 80)
                for boat in ssr_boats:
                    print(f"  {boat['Boat_SerialNo']}")
                    print(f"    Model: {boat['model']}")
                    print(f"    Dealer: {boat['DealerName']}")
                    print(f"    Invoice: {boat['InvoiceDate']}")
                    print()

            if other_boats:
                print(f"\nOTHER BOATS ({len(other_boats)}):")
                print("-" * 80)
                for boat in other_boats[:10]:  # Show first 10
                    print(f"  {boat['Boat_SerialNo']} - {boat['DealerName']}")

        else:
            print("❌ No Short's Marine boats found in SerialNumberMaster!")

        cursor.close()
        connection.close()

    except mysql.connector.Error as e:
        print(f"❌ Database error: {e}")
        if connection and connection.is_connected():
            connection.close()

if __name__ == "__main__":
    check_serial_master()

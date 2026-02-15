#!/usr/bin/env python3
"""Check if boats exist in SerialNumberMaster table"""
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
        print("CHECKING BOATS IN SerialNumberMaster")
        print("="*80 + "\n")

        # Check specific boat
        test_serial = 'ETWS0837A626'
        print(f"Looking for {test_serial}...")

        cursor.execute("""
            SELECT Boat_SerialNo, DealerName, DealerNumber
            FROM SerialNumberMaster
            WHERE Boat_SerialNo = %s
        """, (test_serial,))

        result = cursor.fetchone()

        if result:
            print(f"✅ FOUND {test_serial} in SerialNumberMaster:")
            print(f"   Dealer: {result['DealerName']}")
            print(f"   Dealer #: {result['DealerNumber']}")
        else:
            print(f"❌ {test_serial} NOT FOUND in SerialNumberMaster")
            print("\n🔍 This is likely why you can't pull up the boat!")
            print("   The boat exists in BoatOptions26 but not in SerialNumberMaster.")
            print("   The system probably uses SerialNumberMaster to list available boats.\n")

        # Check all Short's Marine 23SSR boats that ARE in SerialNumberMaster
        print("\n" + "="*80)
        print("CHECKING FOR 23SSR BOATS FROM SHORT'S MARINE IN SerialNumberMaster")
        print("="*80 + "\n")

        cursor.execute("""
            SELECT
                snm.Boat_SerialNo,
                snm.DealerName,
                snm.DealerNumber,
                bo.BoatModelNo,
                bo.ItemDesc1,
                bo.ExtSalesAmount,
                bo.MSRP
            FROM SerialNumberMaster snm
            LEFT JOIN BoatOptions26 bo
                ON snm.Boat_SerialNo = bo.BoatSerialNo
                AND bo.ItemMasterMCT IN ('BOA', 'BOI')
            WHERE (snm.DealerName LIKE '%SHORT%' OR snm.DealerName LIKE '%PRICE MARINE%')
              AND (bo.BoatModelNo LIKE '%23SSR%' OR bo.ItemDesc1 LIKE '%23 S STERN%')
            ORDER BY snm.Boat_SerialNo DESC
            LIMIT 20
        """)

        ssr_boats = cursor.fetchall()

        if ssr_boats:
            print(f"Found {len(ssr_boats)} 23SSR boats for Short's Marine:\n")

            for boat in ssr_boats:
                print(f"Hull #: {boat['Boat_SerialNo']}")
                print(f"  Model: {boat['BoatModelNo']}")
                print(f"  Dealer: {boat['DealerName']} (#{boat['DealerNumber']})")

                dealer_cost = float(boat['ExtSalesAmount']) if boat['ExtSalesAmount'] else 0
                msrp = float(boat['MSRP']) if boat['MSRP'] else 0

                if dealer_cost > 0:
                    print(f"  Dealer Cost: ${dealer_cost:,.2f}")
                    expected_msrp = dealer_cost / 0.70
                    print(f"  Expected MSRP (30% margin): ${expected_msrp:,.2f}")

                if msrp > 0:
                    print(f"  MSRP in DB: ${msrp:,.2f}")

                print(f"  ✅ THIS BOAT CAN BE PULLED UP!")
                print()
        else:
            print("❌ No 23SSR boats found for Short's Marine in SerialNumberMaster")
            print("\nLet me check what boats ARE accessible for Short's Marine...")

            # Get any boats for Short's Marine
            cursor.execute("""
                SELECT
                    snm.Boat_SerialNo,
                    bo.BoatModelNo,
                    bo.ItemDesc1
                FROM SerialNumberMaster snm
                LEFT JOIN BoatOptions26 bo
                    ON snm.Boat_SerialNo = bo.BoatSerialNo
                    AND bo.ItemMasterMCT IN ('BOA', 'BOI')
                WHERE (snm.DealerName LIKE '%SHORT%' OR snm.DealerName LIKE '%PRICE MARINE%')
                ORDER BY snm.Boat_SerialNo DESC
                LIMIT 20
            """)

            any_boats = cursor.fetchall()

            if any_boats:
                print(f"\nFound {len(any_boats)} boats that CAN be pulled up:\n")
                for boat in any_boats:
                    print(f"  {boat['Boat_SerialNo']}: {boat['BoatModelNo']} - {boat['ItemDesc1']}")

        cursor.close()
        connection.close()

    except mysql.connector.Error as e:
        print(f"❌ Database error: {e}")
        if connection and connection.is_connected():
            connection.close()

if __name__ == "__main__":
    check_serial_master()

#!/usr/bin/env python3
"""Find 23SSR boats for Short's Marine"""
import mysql.connector

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts'
}

def find_23ssr_boats():
    """Find 23 SSR boats"""
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        print("\n" + "="*80)
        print("SEARCHING FOR 23SSR / MID RANGE FIGHTER BOATS")
        print("="*80 + "\n")

        # Search in BoatOptions tables for 23 SSR boats
        for year in [23, 24, 25, 26]:
            table_name = f"BoatOptions{year}"

            print(f"\n{'='*80}")
            print(f"Checking {table_name}")
            print(f"{'='*80}")

            # Check if table exists
            cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
            if not cursor.fetchone():
                print(f"  Table {table_name} does not exist")
                continue

            query = f"""
                SELECT DISTINCT
                    BoatSerialNo,
                    BoatModelNo,
                    ItemDesc1 as BoatDescription,
                    InvoiceNo,
                    InvoiceDate,
                    ERP_OrderNo,
                    CfgName,
                    external_confirmation_ref,
                    MSRP,
                    ExtSalesAmount
                FROM {table_name}
                WHERE (BoatModelNo LIKE '%23SSR%'
                   OR BoatModelNo LIKE '23%SSR%'
                   OR ItemDesc1 LIKE '%23 S STERN RADIUS%'
                   OR (ItemDesc1 LIKE '%MID RANGE%' AND ItemDesc1 LIKE '%23%')
                   OR (ItemDesc1 LIKE '%FIGHTER%' AND ItemDesc1 LIKE '%23%'))
                  AND ItemMasterMCT IN ('BOA', 'BOI')
                ORDER BY InvoiceDate DESC
                LIMIT 20
            """

            cursor.execute(query)
            boats = cursor.fetchall()

            if boats:
                print(f"\n  Found {len(boats)} boats:\n")

                for boat in boats:
                    print(f"  Hull #: {boat['BoatSerialNo']}")
                    print(f"    Model: {boat['BoatModelNo']}")
                    print(f"    Description: {boat['BoatDescription']}")
                    print(f"    Invoice: {boat['InvoiceNo']} ({boat['InvoiceDate']})")
                    print(f"    ERP Order: {boat['ERP_OrderNo']}")
                    print(f"    External Ref: {boat['external_confirmation_ref']}")

                    msrp = float(boat['MSRP']) if boat['MSRP'] else 0
                    dealer_cost = float(boat['ExtSalesAmount']) if boat['ExtSalesAmount'] else 0

                    if msrp > 0:
                        print(f"    MSRP: ${msrp:,.2f}")
                    else:
                        print(f"    MSRP: NOT SET")

                    if dealer_cost > 0:
                        print(f"    Dealer Cost: ${dealer_cost:,.2f}")

                        # Calculate expected MSRP if using 30% margin
                        if msrp == 0:
                            expected_msrp = dealer_cost / 0.70  # 30% margin
                            print(f"    Expected MSRP (30% margin): ${expected_msrp:,.2f}")

                    has_cfg = boat['CfgName'] and boat['CfgName'] not in [None, '', 'NULL']
                    is_cpq_ref = boat['external_confirmation_ref'] and 'CPQ' in str(boat['external_confirmation_ref'])
                    boat_type = "CPQ BOAT" if (has_cfg or is_cpq_ref) else "LEGACY BOAT"
                    print(f"    CfgName: {boat['CfgName']}")
                    print(f"    Type: {boat_type}")

                    # Flag potential Mid Range Fighter
                    if msrp == 0 and dealer_cost > 0:
                        expected_msrp = dealer_cost / 0.70
                        if expected_msrp > 90000 and expected_msrp < 110000:
                            print(f"    ⚠️  POTENTIAL MATCH: Expected MSRP ~${expected_msrp:,.2f} (in ~$97k range)")

                    print()
            else:
                print(f"  No 23SSR boats found in {table_name}")

        # Also search for any boat with serial numbers from the user's list that might be 23' models
        print("\n" + "="*80)
        print("CHECKING SPECIFIC SERIALS FROM USER'S LIST (23' models)")
        print("="*80 + "\n")

        # Serial numbers that might be 23' models based on naming patterns
        potential_23_serials = [
            'ETWS0837A626',  # 23 S STERN RADIUS
            'ETWS2864L525',
            'ETWS2865L525',
            'ETWS2871L525',
            'ETWS2901L525',
            'ETWS2904L525'
        ]

        for serial in potential_23_serials:
            found = False
            for year in [23, 24, 25, 26]:
                table_name = f"BoatOptions{year}"

                cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
                if not cursor.fetchone():
                    continue

                query = f"""
                    SELECT DISTINCT
                        BoatSerialNo,
                        BoatModelNo,
                        ItemDesc1,
                        MSRP,
                        ExtSalesAmount,
                        CfgName
                    FROM {table_name}
                    WHERE BoatSerialNo = %s
                      AND ItemMasterMCT IN ('BOA', 'BOI')
                    LIMIT 1
                """

                cursor.execute(query, (serial,))
                result = cursor.fetchone()

                if result:
                    found = True
                    print(f"  {serial}: {result['BoatModelNo']} - {result['ItemDesc1']}")

                    msrp = float(result['MSRP']) if result['MSRP'] else 0
                    dealer_cost = float(result['ExtSalesAmount']) if result['ExtSalesAmount'] else 0

                    if msrp > 0:
                        print(f"    MSRP: ${msrp:,.2f}")
                    else:
                        print(f"    MSRP: NOT SET (Dealer Cost: ${dealer_cost:,.2f})")
                        if dealer_cost > 0:
                            expected_msrp = dealer_cost / 0.70
                            print(f"    Expected MSRP (30% margin): ${expected_msrp:,.2f}")
                            if expected_msrp > 90000 and expected_msrp < 110000:
                                print(f"    ⚠️  POTENTIAL MATCH FOR MID RANGE FIGHTER!")

                    print(f"    Table: {table_name}")
                    print()
                    break

            if not found:
                print(f"  {serial}: NOT FOUND in any BoatOptions table")

        cursor.close()
        connection.close()

    except mysql.connector.Error as e:
        print(f"❌ Database error: {e}")
        if connection and connection.is_connected():
            connection.close()

if __name__ == "__main__":
    find_23ssr_boats()

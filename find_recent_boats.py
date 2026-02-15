#!/usr/bin/env python3
"""Find recent boats in BoatOptions to identify dealer boats"""
import mysql.connector

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts'
}

def find_recent_boats():
    """Find recent boats"""
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        print("\n" + "="*80)
        print("RECENT BOATS IN BOATOPTIONS25 AND BOATOPTIONS26")
        print("="*80 + "\n")

        for year in [25, 26]:
            table_name = f"BoatOptions{year}"

            print(f"\n{'='*80}")
            print(f"{table_name} - Recent SSR/Mid Range Fighter Boats")
            print(f"{'='*80}")

            # Find SSR boats
            query = f"""
                SELECT DISTINCT
                    BoatSerialNo,
                    BoatModelNo,
                    ItemDesc1,
                    InvoiceNo,
                    InvoiceDate,
                    ERP_OrderNo,
                    external_confirmation_ref,
                    CfgName,
                    MSRP,
                    ExtSalesAmount
                FROM {table_name}
                WHERE (BoatModelNo LIKE '%SSR%'
                   OR ItemDesc1 LIKE '%SSR%'
                   OR ItemDesc1 LIKE '%MID RANGE%'
                   OR ItemDesc1 LIKE '%FIGHTER%')
                  AND ItemMasterMCT IN ('BOA', 'BOI')
                ORDER BY BoatSerialNo DESC
                LIMIT 20
            """

            cursor.execute(query)
            boats = cursor.fetchall()

            if boats:
                print(f"\nFound {len(boats)} SSR/Mid Range Fighter boats:\n")

                for boat in boats:
                    print(f"Serial: {boat['BoatSerialNo']}")
                    print(f"  Model: {boat['BoatModelNo']}")
                    print(f"  Description: {boat['ItemDesc1']}")
                    print(f"  Invoice: {boat['InvoiceNo']} (Date: {boat['InvoiceDate']})")
                    print(f"  ERP Order: {boat['ERP_OrderNo']}")
                    print(f"  External Ref: {boat['external_confirmation_ref']}")

                    # Check pricing
                    msrp = float(boat['MSRP']) if boat['MSRP'] else 0
                    dealer_cost = float(boat['ExtSalesAmount']) if boat['ExtSalesAmount'] else 0

                    if msrp > 0:
                        print(f"  MSRP: ${msrp:,.2f}")
                    if dealer_cost > 0:
                        print(f"  Dealer Cost: ${dealer_cost:,.2f}")

                    # Determine type
                    has_cfg = boat['CfgName'] and boat['CfgName'] not in [None, '', 'NULL']
                    is_cpq_ref = boat['external_confirmation_ref'] and 'CPQ' in str(boat['external_confirmation_ref'])

                    if has_cfg or is_cpq_ref:
                        print(f"  Type: CPQ BOAT (CfgName: {boat['CfgName']})")
                    else:
                        print(f"  Type: LEGACY BOAT")

                    print()

            else:
                print("  No SSR/Mid Range Fighter boats found")

        cursor.close()
        connection.close()

    except mysql.connector.Error as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    find_recent_boats()

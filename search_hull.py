#!/usr/bin/env python3
"""
Search for hull ETWTEST024 and dealer 00000050
"""

import mysql.connector

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts_test'
}

def search_hull():
    """Search for hull ETWTEST024"""
    print("=" * 80)
    print("SEARCHING FOR HULL: ETWTEST024")
    print("=" * 80)

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Search in BoatOptions26_test
    print("\n1. Searching BoatOptions26_test...")
    cursor.execute("""
        SELECT
            ERP_OrderNo,
            BoatSerialNo,
            BoatModelNo,
            COUNT(*) as line_items,
            SUM(ExtSalesAmount) as total_msrp
        FROM BoatOptions26_test
        WHERE BoatSerialNo = %s
        GROUP BY ERP_OrderNo, BoatSerialNo, BoatModelNo
    """, ('ETWTEST024',))

    results = cursor.fetchall()
    if results:
        print(f"   ✓ Found {len(results)} order(s)")
        for row in results:
            print(f"     Order: {row[0]}, Model: {row[2]}, Items: {row[3]}, MSRP: ${row[4]:,.2f}")
    else:
        print("   ✗ Not found in BoatOptions26_test")

    # Search for similar hulls (ETWTEST*)
    print("\n2. Searching for similar hulls (ETWTEST*)...")
    cursor.execute("""
        SELECT DISTINCT
            BoatSerialNo,
            BoatModelNo,
            COUNT(DISTINCT ERP_OrderNo) as orders
        FROM BoatOptions26_test
        WHERE BoatSerialNo LIKE 'ETWTEST%'
        GROUP BY BoatSerialNo, BoatModelNo
        ORDER BY BoatSerialNo
        LIMIT 20
    """)

    results = cursor.fetchall()
    if results:
        print(f"   ✓ Found {len(results)} similar hull(s)")
        for row in results:
            print(f"     Hull: {row[0]}, Model: {row[1]}, Orders: {row[2]}")
    else:
        print("   ✗ No similar hulls found")

    # Search in BoatOptions25_test
    print("\n3. Searching BoatOptions25_test...")
    cursor.execute("""
        SELECT
            ERP_OrderNo,
            BoatSerialNo,
            BoatModelNo,
            COUNT(*) as line_items,
            SUM(ExtSalesAmount) as total_msrp
        FROM BoatOptions25_test
        WHERE BoatSerialNo = %s
        GROUP BY ERP_OrderNo, BoatSerialNo, BoatModelNo
    """, ('ETWTEST024',))

    results = cursor.fetchall()
    if results:
        print(f"   ✓ Found {len(results)} order(s)")
        for row in results:
            print(f"     Order: {row[0]}, Model: {row[2]}, Items: {row[3]}, MSRP: ${row[4]:,.2f}")
    else:
        print("   ✗ Not found in BoatOptions25_test")

    # Search for dealer orders
    print("\n4. Searching for dealer 00000050 orders...")
    cursor.execute("""
        SELECT DISTINCT
            d.dealer_id,
            d.dealer_name,
            d.series_id
        FROM Dealers d
        WHERE d.dealer_id = %s
    """, ('00000050',))

    dealer = cursor.fetchone()
    if dealer:
        print(f"   ✓ Dealer found: {dealer[1]} (ID: {dealer[0]}, Series: {dealer[2]})")
    else:
        print("   ✗ Dealer 00000050 not found in Dealers table")

    # Check if there are any hulls in the format ETWTEST*
    print("\n5. Checking for ANY ETW test hulls...")
    cursor.execute("""
        SELECT
            BoatSerialNo,
            COUNT(*) as occurrences
        FROM BoatOptions26_test
        WHERE BoatSerialNo LIKE 'ETW%'
        GROUP BY BoatSerialNo
        ORDER BY BoatSerialNo
        LIMIT 10
    """)

    results = cursor.fetchall()
    if results:
        print(f"   ✓ Found {len(results)} ETW* hull(s)")
        for row in results:
            print(f"     Hull: {row[0]}, Occurrences: {row[1]}")
    else:
        print("   ✗ No ETW* hulls found in BoatOptions26_test")

    cursor.close()
    conn.close()

    print("\n" + "=" * 80)
    print("SEARCH COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    try:
        search_hull()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

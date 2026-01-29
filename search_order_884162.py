#!/usr/bin/env python3
"""
Search for order 884162 in different formats
"""

import mysql.connector

def search_order():
    # Try warrantyparts database
    conn = mysql.connector.connect(
        host='ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
        user='awsmaster',
        password='VWvHG9vfG23g7gD',
        database='warrantyparts'
    )

    cursor = conn.cursor()

    print("=" * 80)
    print("SEARCHING FOR ORDER 884162 (Various Formats)")
    print("=" * 80)

    # Try different order number formats
    order_formats = [
        '884162',
        'SO884162',
        'SO00884162',
        'SO0884162',
        'MO884162',
        'MO00884162'
    ]

    for order_no in order_formats:
        print(f"\n{order_no}:")
        cursor.execute('''
            SELECT COUNT(*)
            FROM BoatOptions26
            WHERE ERP_OrderNo = %s
        ''', (order_no,))

        count = cursor.fetchone()[0]
        if count > 0:
            print(f"  ✓ Found {count} line items!")

            # Get details
            cursor.execute('''
                SELECT
                    ERP_OrderNo,
                    BoatSerialNo,
                    ItemMasterProdCat,
                    SUM(ExtSalesAmount) as total
                FROM BoatOptions26
                WHERE ERP_OrderNo = %s
                GROUP BY ERP_OrderNo, BoatSerialNo, ItemMasterProdCat
            ''', (order_no,))

            results = cursor.fetchall()
            for row in results:
                print(f"    Order: {row[0]}, Hull: {row[1] or 'N/A'}, Category: {row[2]}, Total: ${row[3] or 0:,.2f}")
        else:
            print(f"  ✗ Not found")

    # Search for hull directly
    print("\n" + "=" * 80)
    print("SEARCHING BY HULL: ETWP6278J324")
    print("=" * 80)

    cursor.execute('''
        SELECT DISTINCT
            ERP_OrderNo,
            BoatSerialNo,
            BoatModelNo,
            COUNT(*) as items
        FROM BoatOptions26
        WHERE BoatSerialNo = %s
        GROUP BY ERP_OrderNo, BoatSerialNo, BoatModelNo
    ''', ('ETWP6278J324',))

    results = cursor.fetchall()
    if results:
        print(f"\n✓ Found {len(results)} order(s) for this hull:")
        for row in results:
            print(f"  Order: {row[0]}, Hull: {row[1]}, Model: {row[2] or 'N/A'}, Items: {row[3]}")
    else:
        print("\n✗ Hull not found in BoatOptions26")

    cursor.close()
    conn.close()

    # Try warrantyparts_test database
    print("\n" + "=" * 80)
    print("CHECKING warrantyparts_test.BoatOptions26_test")
    print("=" * 80)

    conn = mysql.connector.connect(
        host='ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
        user='awsmaster',
        password='VWvHG9vfG23g7gD',
        database='warrantyparts_test'
    )

    cursor = conn.cursor()

    cursor.execute('''
        SELECT DISTINCT
            ERP_OrderNo,
            BoatSerialNo,
            BoatModelNo,
            COUNT(*) as items
        FROM BoatOptions26_test
        WHERE BoatSerialNo = %s
        GROUP BY ERP_OrderNo, BoatSerialNo, BoatModelNo
    ''', ('ETWP6278J324',))

    results = cursor.fetchall()
    if results:
        print(f"\n✓ Found {len(results)} order(s) for this hull:")
        for row in results:
            print(f"  Order: {row[0]}, Hull: {row[1]}, Model: {row[2] or 'N/A'}, Items: {row[3]}")
    else:
        print("\n✗ Hull not found in BoatOptions26_test")

    cursor.close()
    conn.close()

    print("\n" + "=" * 80)

if __name__ == '__main__':
    search_order()

#!/usr/bin/env python3
"""
Search for ETWP6278J324 across all BoatOptions tables
"""

import mysql.connector

def search_all_years():
    conn = mysql.connector.connect(
        host='ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
        user='awsmaster',
        password='VWvHG9vfG23g7gD',
        database='warrantyparts'
    )

    cursor = conn.cursor()

    print("=" * 80)
    print("SEARCHING FOR ETWP6278J324 ACROSS ALL BoatOptions TABLES")
    print("=" * 80)

    # List of BoatOptions tables
    tables = [
        'BoatOptions24',
        'BoatOptions25',
        'BoatOptions26',
        'BoatOptions23',
        'BoatOptions22',
        'BoatOptions21',
        'BoatOptions20'
    ]

    hull_no = 'ETWP6278J324'

    for table in tables:
        print(f"\n{table}:")
        try:
            cursor.execute(f'''
                SELECT DISTINCT
                    ERP_OrderNo,
                    BoatSerialNo,
                    BoatModelNo,
                    COUNT(*) as items,
                    SUM(ExtSalesAmount) as total
                FROM {table}
                WHERE BoatSerialNo = %s
                GROUP BY ERP_OrderNo, BoatSerialNo, BoatModelNo
            ''', (hull_no,))

            results = cursor.fetchall()
            if results:
                print(f"  ✓ FOUND {len(results)} order(s)!")
                for row in results:
                    print(f"    Order: {row[0]}, Model: {row[2] or 'N/A'}, Items: {row[3]}, Total: ${row[4] or 0:,.2f}")

                # If found, get detailed line items
                cursor.execute(f'''
                    SELECT
                        LineNo,
                        ItemNo,
                        ItemDesc1,
                        ItemMasterProdCat,
                        QuantitySold,
                        ExtSalesAmount
                    FROM {table}
                    WHERE BoatSerialNo = %s
                    ORDER BY LineNo
                    LIMIT 20
                ''', (hull_no,))

                items = cursor.fetchall()
                print(f"\n    First {min(len(items), 20)} line items:")
                print(f"    {'Line':>5s} {'Item':20s} {'Cat':5s} {'Qty':>4s} {'Amount':>12s} {'Description':30s}")
                print(f"    {'-'*5} {'-'*20} {'-'*5} {'-'*4} {'-'*12} {'-'*30}")

                for item in items:
                    desc = (item[2] or '')[:30]
                    print(f"    {item[0]:5d} {item[1] or '':20s} {item[3] or '':5s} {item[4] or 0:4d} ${item[5] or 0:11,.2f} {desc:30s}")

            else:
                print(f"  ✗ Not found")
        except Exception as e:
            print(f"  ✗ Error: {e}")

    cursor.close()
    conn.close()

    print("\n" + "=" * 80)

if __name__ == '__main__':
    search_all_years()

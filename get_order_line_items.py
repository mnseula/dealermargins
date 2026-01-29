#!/usr/bin/env python3
"""
Get line items for order SO009999
"""

import mysql.connector

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts_test'
}

def get_line_items():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    print("=" * 80)
    print("SEARCHING FOR ORDER SO009999 LINE ITEMS")
    print("=" * 80)

    # Search BoatOptions26_test
    print("\n1. Searching BoatOptions26_test for SO009999:")
    cursor.execute('''
        SELECT
            ERP_OrderNo,
            LineNo,
            ItemNo,
            ItemDesc1,
            ItemMasterProdCat,
            QuantitySold,
            ExtSalesAmount
        FROM BoatOptions26_test
        WHERE ERP_OrderNo = %s
        ORDER BY LineNo
    ''', ('SO009999',))

    results = cursor.fetchall()
    if results:
        print(f'   ✓ Found {len(results)} line items')
        print(f'\n   {"Line":>5s} {"Item No":20s} {"Category":8s} {"Qty":>5s} {"Amount":>12s} {"Description":40s}')
        print(f'   {"-"*5} {"-"*20} {"-"*8} {"-"*5} {"-"*12} {"-"*40}')

        total = 0
        for row in results:
            amount = row[6] or 0
            total += amount
            print(f'   {row[1]:5d} {row[2] or "":20s} {row[4] or "":8s} {row[5] or 0:5.0f} ${amount:11,.2f} {(row[3] or "")[:40]:40s}')

        print(f'   {"":35s} {"TOTAL":>5s} ${total:11,.2f}')
    else:
        print('   ✗ Not found in BoatOptions26_test')

        # Try BoatOptions25_test
        print('\n2. Searching BoatOptions25_test for SO009999:')
        cursor.execute('''
            SELECT
                ERP_OrderNo,
                LineNo,
                ItemNo,
                ItemDesc1,
                ItemMasterProdCat,
                QuantitySold,
                ExtSalesAmount
            FROM BoatOptions25_test
            WHERE ERP_OrderNo = %s
            ORDER BY LineNo
        ''', ('SO009999',))

        results = cursor.fetchall()
        if results:
            print(f'   ✓ Found {len(results)} line items')
            print(f'\n   {"Line":>5s} {"Item No":20s} {"Category":8s} {"Qty":>5s} {"Amount":>12s} {"Description":40s}')
            print(f'   {"-"*5} {"-"*20} {"-"*8} {"-"*5} {"-"*12} {"-"*40}')

            total = 0
            for row in results:
                amount = row[6] or 0
                total += amount
                print(f'   {row[1]:5d} {row[2] or "":20s} {row[4] or "":8s} {row[5] or 0:5.0f} ${amount:11,.2f} {(row[3] or "")[:40]:40s}')

            print(f'   {"":35s} {"TOTAL":>5s} ${total:11,.2f}')
        else:
            print('   ✗ Not found in BoatOptions25_test either')

    cursor.close()
    conn.close()

    print("\n" + "=" * 80)

if __name__ == '__main__':
    get_line_items()

#!/usr/bin/env python3
"""
Check warrantyparts.BoatOptions26 for SO009999
"""

import mysql.connector

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts'
}

def check_production():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    print("=" * 80)
    print("SEARCHING warrantyparts.BoatOptions26 FOR ORDER SO009999")
    print("=" * 80)

    cursor.execute('''
        SELECT
            ERP_OrderNo,
            BoatSerialNo,
            BoatModelNo,
            LineNo,
            ItemNo,
            ItemDesc1,
            ItemMasterProdCat,
            QuantitySold,
            ExtSalesAmount
        FROM BoatOptions26
        WHERE ERP_OrderNo = %s
        ORDER BY LineNo
    ''', ('SO009999',))

    results = cursor.fetchall()

    if results:
        print(f'\n✓ Found {len(results)} line items for SO009999\n')
        print(f'{"Line":>5s} {"Item No":20s} {"Category":8s} {"Qty":>5s} {"Amount":>12s} {"Description":40s}')
        print('-' * 95)

        total = 0
        for row in results:
            amount = row[8] or 0
            total += amount
            print(f'{row[3]:5d} {row[4] or "":20s} {row[6] or "":8s} {row[7] or 0:5d} ${amount:11,.2f} {(row[5] or "")[:40]:40s}')

        print('-' * 95)
        print(f'{"":35s} {"TOTAL":>5s} ${total:11,.2f}')
    else:
        print('\n✗ Order SO009999 not found in warrantyparts.BoatOptions26')

    # Check what orders DO exist for ETWTEST024
    print('\n' + '=' * 80)
    print('SEARCHING FOR ANY ORDERS WITH HULL ETWTEST024')
    print('=' * 80)

    cursor.execute('''
        SELECT DISTINCT
            ERP_OrderNo,
            BoatSerialNo,
            BoatModelNo,
            COUNT(*) as line_items,
            SUM(ExtSalesAmount) as total_amount
        FROM BoatOptions26
        WHERE BoatSerialNo = %s
        GROUP BY ERP_OrderNo, BoatSerialNo, BoatModelNo
    ''', ('ETWTEST024',))

    results = cursor.fetchall()

    if results:
        print(f'\n✓ Found {len(results)} order(s) for ETWTEST024\n')
        for row in results:
            print(f'  Order: {row[0]}, Model: {row[2] or "N/A"}, Items: {row[3]}, Total: ${row[4] or 0:,.2f}')
    else:
        print('\n✗ No orders found with hull ETWTEST024 in BoatOptions26')

    # Show sample of what IS in BoatOptions26
    print('\n' + '=' * 80)
    print('SAMPLE OF RECENT ORDERS IN warrantyparts.BoatOptions26')
    print('=' * 80)

    cursor.execute('''
        SELECT DISTINCT
            ERP_OrderNo,
            BoatSerialNo,
            BoatModelNo,
            InvoiceDate
        FROM BoatOptions26
        WHERE InvoiceDate IS NOT NULL
        ORDER BY InvoiceDate DESC
        LIMIT 10
    ''')

    results = cursor.fetchall()
    if results:
        print(f'\nMost recent 10 orders:')
        print(f'{"Order":15s} {"Hull":20s} {"Model":20s} {"Date":12s}')
        print('-' * 70)
        for row in results:
            inv_date = str(row[3]) if row[3] else 'N/A'
            if inv_date != 'N/A' and len(inv_date) == 8:
                inv_date = f'{inv_date[:4]}-{inv_date[4:6]}-{inv_date[6:]}'
            print(f'{row[0] or "":15s} {row[1] or "N/A":20s} {row[2] or "N/A":20s} {inv_date:12s}')

    cursor.close()
    conn.close()

    print('\n' + '=' * 80)

if __name__ == '__main__':
    check_production()

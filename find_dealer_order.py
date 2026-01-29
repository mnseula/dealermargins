#!/usr/bin/env python3
"""
Find order containing dealer 00000050
"""

import mysql.connector

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts_test'
}

def find_order():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    print("=" * 80)
    print("ORDER CONTAINING 00000050")
    print("=" * 80)

    # Find the order
    cursor.execute('''
        SELECT DISTINCT
            ERP_OrderNo,
            BoatSerialNo,
            BoatModelNo,
            Series,
            InvoiceNo,
            InvoiceDate
        FROM BoatOptions26_test
        WHERE ERP_OrderNo LIKE %s
    ''', ('%00000050%',))

    results = cursor.fetchall()
    print(f'\nFound {len(results)} order(s):')

    for row in results:
        inv_date = str(row[5]) if row[5] else 'N/A'
        if inv_date != 'N/A' and len(inv_date) == 8:
            inv_date = f'{inv_date[:4]}-{inv_date[4:6]}-{inv_date[6:]}'

        print(f'\n  Order Number: {row[0]}')
        print(f'  Hull/Serial:  {row[1] or "N/A"}')
        print(f'  Model:        {row[2] or "N/A"}')
        print(f'  Series:       {row[3] or "N/A"}')
        print(f'  Invoice:      {row[4] or "N/A"}')
        print(f'  Date:         {inv_date}')

        # Get line items for this order
        cursor.execute('''
            SELECT
                LineNo,
                ItemNo,
                ItemDesc1,
                ItemMasterProdCat,
                QuantitySold,
                ExtSalesAmount
            FROM BoatOptions26_test
            WHERE ERP_OrderNo = %s
            ORDER BY LineNo
        ''', (row[0],))

        items = cursor.fetchall()
        print(f'\n  Line Items: {len(items)}')
        print(f'  {"Line":>5s} {"Item No":20s} {"Category":8s} {"Qty":>5s} {"Amount":>12s}')
        print(f'  {"-"*5} {"-"*20} {"-"*8} {"-"*5} {"-"*12}')

        total = 0
        for item in items[:20]:  # Show first 20 items
            amount = item[5] or 0
            total += amount
            print(f'  {item[0]:5d} {item[1] or "":<20s} {item[3] or "":<8s} {item[4] or 0:5.0f} ${amount:11,.2f}')

        if len(items) > 20:
            remaining = len(items) - 20
            remaining_total = sum(i[5] or 0 for i in items[20:])
            print(f'  ... and {remaining} more items (${remaining_total:,.2f})')

        print(f'  {"":35s} {"Total":>5s} ${total:11,.2f}')

    cursor.close()
    conn.close()

    print('\n' + '=' * 80)

if __name__ == '__main__':
    find_order()

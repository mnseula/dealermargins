#!/usr/bin/env python3
"""
Check how many CPQ orders exist since go-live date (2024-12-14)
"""
import pymssql
from datetime import datetime

MSSQL_CONFIG = {
    'server': 'MPL1STGSQL086.POLARISSTAGE.COM',
    'database': 'CSISTG',
    'user': 'svccsimarine',
    'password': 'CNKmoFxEsXs0D9egZQXH'
}

QUERY = """
SELECT
    co_num,
    cust_num,
    cust_po,
    order_date,
    external_confirmation_ref
FROM [dbo].[co_mst]
WHERE order_date >= '2024-12-14'      -- CPQ Go Live Date
  AND co_num LIKE 'SO%'
  AND [external_confirmation_ref] LIKE 'SO%'
ORDER BY order_date DESC
"""

def main():
    print("="*80)
    print("CPQ ORDERS SINCE GO-LIVE (2024-12-14)")
    print("="*80)

    try:
        print("\nConnecting to MSSQL...")
        conn = pymssql.connect(**MSSQL_CONFIG)
        cursor = conn.cursor(as_dict=True)
        print("✅ Connected\n")

        print("Executing query...")
        cursor.execute(QUERY)

        orders = cursor.fetchall()

        print(f"\n{'Order Number':<15} {'Customer':<12} {'PO':<15} {'Order Date':<12} {'Confirmation Ref':<20}")
        print("-"*80)

        for order in orders:
            co_num = order['co_num'] or ''
            cust_num = order['cust_num'] or ''
            cust_po = order['cust_po'] or ''
            order_date = order['order_date'].strftime('%Y-%m-%d') if order['order_date'] else ''
            conf_ref = order['external_confirmation_ref'] or ''

            print(f"{co_num:<15} {cust_num:<12} {cust_po:<15} {order_date:<12} {conf_ref:<20}")

        print("\n" + "="*80)
        print(f"TOTAL CPQ ORDERS: {len(orders)}")
        print("="*80)

        cursor.close()
        conn.close()

    except pymssql.Error as e:
        print(f"❌ MSSQL Error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    main()

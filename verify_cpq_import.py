#!/usr/bin/env python3
"""
Verify CPQ Import Data
Check the imported CPQ orders and configured items
"""
import mysql.connector
from datetime import date

MYSQL_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'warrantyparts_boatoptions_test',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD'
}

def main():
    print("="*120)
    print("CPQ IMPORT VERIFICATION")
    print("="*120)

    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()

    # Query 1: Recent CPQ orders summary
    print("\n" + "="*120)
    print("RECENT CPQ ORDERS (since 12/14/2025)")
    print("="*120)

    cursor.execute("""
        SELECT
            ERP_OrderNo,
            BoatSerialNo,
            WebOrderNo,
            order_date,
            external_confirmation_ref,
            COUNT(*) as line_items,
            SUM(ExtSalesAmount) as total_amount
        FROM BoatOptions26
        WHERE order_date >= '2025-12-14'
        GROUP BY ERP_OrderNo, BoatSerialNo, WebOrderNo, order_date, external_confirmation_ref
        ORDER BY order_date DESC
        LIMIT 10
    """)

    print(f"\n{'ERP Order':<15} {'Serial':<15} {'Web Order':<15} {'Order Date':<12} {'Ext Ref':<15} {'Lines':<6} {'Amount':<12}")
    print("-"*120)

    for row in cursor.fetchall():
        erp = row[0] or ''
        serial = row[1] or ''
        web = row[2] or ''
        order_dt = str(row[3]) if row[3] else ''
        ext_ref = row[4] or ''
        lines = row[5] or 0
        amount = f"${row[6]:,.2f}" if row[6] else '$0.00'
        print(f"{erp:<15} {serial:<15} {web:<15} {order_dt:<12} {ext_ref:<15} {lines:<6} {amount:<12}")

    # Query 2: Configured items (with ConfigID)
    print("\n" + "="*120)
    print("CONFIGURED ITEMS (CFG Table Data)")
    print("="*120)

    cursor.execute("""
        SELECT
            ERP_OrderNo,
            BoatSerialNo,
            ItemNo,
            ItemDesc1,
            ConfigID,
            ValueText,
            ExtSalesAmount
        FROM BoatOptions26
        WHERE ConfigID IS NOT NULL
          AND ConfigID != ''
          AND order_date >= '2025-12-14'
        ORDER BY order_date DESC, ERP_OrderNo, LineNo
        LIMIT 20
    """)

    print(f"\n{'ERP Order':<15} {'Serial':<15} {'Item':<15} {'Description':<30} {'Config ID':<15} {'Amount':<12}")
    print("-"*120)

    rows = cursor.fetchall()
    if rows:
        for row in rows:
            erp = row[0] or ''
            serial = row[1] or ''
            item = row[2] or ''
            desc = (row[3] or '')[:30]
            config = row[4] or ''
            amount = f"${row[6]:,.2f}" if row[6] else '$0.00'
            print(f"{erp:<15} {serial:<15} {item:<15} {desc:<30} {config:<15} {amount:<12}")
    else:
        print("No configured items found (ConfigID is empty for all rows)")

    # Query 3: Summary statistics
    print("\n" + "="*120)
    print("SUMMARY STATISTICS")
    print("="*120)

    cursor.execute("""
        SELECT
            COUNT(DISTINCT ERP_OrderNo) as order_count,
            COUNT(DISTINCT BoatSerialNo) as boat_count,
            COUNT(*) as total_lines,
            SUM(ExtSalesAmount) as total_amount,
            COUNT(CASE WHEN ConfigID IS NOT NULL AND ConfigID != '' THEN 1 END) as config_items
        FROM BoatOptions26
        WHERE order_date >= '2025-12-14'
    """)

    row = cursor.fetchone()
    print(f"\nOrders:           {row[0]:,}")
    print(f"Boats:            {row[1]:,}")
    print(f"Total Lines:      {row[2]:,}")
    print(f"Total Amount:     ${row[3]:,.2f}" if row[3] else "$0.00")
    print(f"Configured Items: {row[4]:,}")

    # Query 4: Sample of regular items vs configured items
    print("\n" + "="*120)
    print("ITEM TYPE BREAKDOWN")
    print("="*120)

    cursor.execute("""
        SELECT
            CASE
                WHEN ConfigID IS NOT NULL AND ConfigID != '' THEN 'Configured (CFG)'
                ELSE 'Regular (Physical)'
            END as item_type,
            COUNT(*) as item_count,
            SUM(ExtSalesAmount) as total_amount
        FROM BoatOptions26
        WHERE order_date >= '2025-12-14'
        GROUP BY item_type
    """)

    print(f"\n{'Item Type':<25} {'Count':<12} {'Total Amount':<15}")
    print("-"*60)
    for row in cursor.fetchall():
        item_type = row[0]
        count = f"{row[1]:,}"
        amount = f"${row[2]:,.2f}" if row[2] else "$0.00"
        print(f"{item_type:<25} {count:<12} {amount:<15}")

    cursor.close()
    conn.close()

    print("\n" + "="*120)
    print("✅ VERIFICATION COMPLETE")
    print("="*120)

if __name__ == '__main__':
    main()

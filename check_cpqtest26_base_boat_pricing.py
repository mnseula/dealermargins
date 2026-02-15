#!/usr/bin/env python3
"""Check base boat pricing for CPQTEST26"""

import mysql.connector

conn = mysql.connector.connect(
    host='ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    user='awsmaster',
    password='VWvHG9vfG23g7gD',
    database='warrantyparts'
)

cursor = conn.cursor(dictionary=True)

print("\n" + "=" * 100)
print("CPQTEST26 - Base Boat Items Pricing")
print("=" * 100)

# Get base boat items with pricing
cursor.execute("""
    SELECT
        LineNo,
        ItemNo,
        ItemDesc1,
        ItemMasterMCT,
        MCTDesc,
        MSRP,
        ExtSalesAmount,
        QuantitySold
    FROM BoatOptions26
    WHERE BoatSerialNo = 'CPQTEST26'
      AND ItemMasterMCT = 'BOA'
    ORDER BY LineNo
""")

items = cursor.fetchall()

print(f"\nBase boat items (ItemMasterMCT='BOA'):")
print("-" * 100)
print(f"{'ItemNo':<20} {'ItemDesc1':<25} {'MCTDesc':<25} {'Qty':<5} {'MSRP':<12} {'ExtSales':<12}")
print("-" * 100)

for item in items:
    itemno = item['ItemNo'] or ''
    desc = item['ItemDesc1'] or ''
    mctdesc = item['MCTDesc'] or ''
    qty = item['QuantitySold'] or 0
    msrp = item['MSRP'] or 0
    extsales = item['ExtSalesAmount'] or 0
    print(f"{itemno:<20} {desc:<25} {mctdesc:<25} {qty:<5} ${msrp:<11.2f} ${extsales:<11.2f}")

cursor.close()
conn.close()

#!/usr/bin/env python3
"""Check line items for CPQTEST26 boat to identify double-counting issue"""

import mysql.connector

conn = mysql.connector.connect(
    host='ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    user='awsmaster',
    password='VWvHG9vfG23g7gD',
    database='warrantyparts'
)
cursor = conn.cursor()

# Get line items for CPQTEST26
cursor.execute("""
    SELECT
        LineNo,
        ItemNo,
        ItemDesc1,
        ItemMasterProdCat,
        QuantitySold,
        ExtSalesAmount
    FROM BoatOptions26
    WHERE BoatSerialNo = 'CPQTEST26'
    ORDER BY LineNo
""")

print(f"{'LineNo':<8} {'ItemNo':<15} {'ProdCat':<10} {'Qty':<5} {'ExtSalesAmount':<15} Description")
print("-" * 120)

total = 0
boat_items = []
rows = cursor.fetchall()

for row in rows:
    line_no, item_no, desc, prod_cat, qty, ext_amt = row
    ext_amt = ext_amt or 0
    total += ext_amt

    # Track boat items (BOA category)
    if prod_cat == 'BOA':
        boat_items.append((line_no, item_no, desc, ext_amt))

    print(f"{line_no:<8} {item_no:<15} {prod_cat:<10} {qty:<5} ${ext_amt:>12,.2f}  {desc[:60]}")

print("-" * 120)
print(f"{'TOTAL':<41}${total:>12,.2f}\n")

# Check for duplicate boat lines
if len(boat_items) > 1:
    print(f"⚠️  FOUND {len(boat_items)} BOAT LINES (BOA category) - This is the double-counting issue!")
    for line_no, item_no, desc, amt in boat_items:
        print(f"   Line {line_no}: {item_no} - {desc} = ${amt:,.2f}")
    print()

cursor.close()
conn.close()

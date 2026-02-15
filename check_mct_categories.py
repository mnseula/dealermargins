#!/usr/bin/env python3
"""Check MCTDesc categories for CPQTEST26"""

import mysql.connector

conn = mysql.connector.connect(
    host='ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    user='awsmaster',
    password='VWvHG9vfG23g7gD',
    database='warrantyparts'
)
cursor = conn.cursor()

cursor.execute("""
    SELECT
        ItemNo,
        ItemDesc1,
        ItemMasterProdCat,
        MCTDesc,
        ExtSalesAmount
    FROM BoatOptions26
    WHERE BoatSerialNo = 'CPQTEST26'
      AND ExtSalesAmount > 0
    ORDER BY ExtSalesAmount DESC
""", ())

print(f"{'ItemNo':<20} {'ProdCat':<10} {'MCTDesc':<25} {'Amount':<15} Description")
print("-" * 120)

for row in cursor.fetchall():
    item_no, desc, prod_cat, mct_desc, amt = row
    print(f"{item_no:<20} {prod_cat:<10} {mct_desc:<25} ${amt:>12,.2f}  {desc[:50]}")

cursor.close()
conn.close()

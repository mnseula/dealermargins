#!/usr/bin/env python3
"""
Check Base Boat line for CPQTEST26
"""

import mysql.connector

conn = mysql.connector.connect(
    host='ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    user='awsmaster',
    password='VWvHG9vfG23g7gD',
    database='warrantyparts'
)

cursor = conn.cursor(dictionary=True)

# Get all BOA items
cursor.execute("""
    SELECT
        ItemNo,
        ItemDesc1,
        ItemMasterMCT,
        MSRP,
        ExtSalesAmount
    FROM BoatOptions26
    WHERE BoatSerialNo = 'CPQTEST26'
      AND ItemMasterMCT = 'BOA'
""")

boa_items = cursor.fetchall()

print(f"\nBOA items for CPQTEST26: {len(boa_items)}")
print("-" * 100)
for item in boa_items:
    desc = item['ItemDesc1'] or 'NULL'
    print(f"ItemNo: {item['ItemNo']:<20} MCT: {item['ItemMasterMCT']:<5} Desc: {desc[:60]}")
    print(f"  MSRP: ${float(item['MSRP'] or 0):,.2f}  Dealer: ${float(item['ExtSalesAmount'] or 0):,.2f}")

# Try LIKE search
cursor.execute("""
    SELECT *
    FROM BoatOptions26
    WHERE BoatSerialNo = 'CPQTEST26'
      AND ItemDesc1 LIKE '%Base Boat%'
""")

base_search = cursor.fetchall()
print(f"\n\nSearch for 'Base Boat' LIKE: {len(base_search)} results")

# Try case-insensitive search
cursor.execute("""
    SELECT *
    FROM BoatOptions26
    WHERE BoatSerialNo = 'CPQTEST26'
      AND LOWER(ItemDesc1) LIKE '%base boat%'
""")

base_search2 = cursor.fetchall()
print(f"Search for 'base boat' (lowercase): {len(base_search2)} results")

cursor.close()
conn.close()

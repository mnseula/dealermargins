#!/usr/bin/env python3
"""Check MCT values for CPQTEST26 to debug base boat display"""

import mysql.connector

conn = mysql.connector.connect(
    host='ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    user='awsmaster',
    password='VWvHG9vfG23g7gD',
    database='warrantyparts'
)

cursor = conn.cursor(dictionary=True)

print("\n" + "=" * 100)
print("CPQTEST26 - MCT Values Check")
print("=" * 100)

# Get all items with their MCT values
cursor.execute("""
    SELECT
        LineNo,
        ItemNo,
        ItemDesc1,
        ItemMasterMCT,
        MCTDesc,
        MSRP,
        ExtSalesAmount
    FROM BoatOptions26
    WHERE BoatSerialNo = 'CPQTEST26'
    ORDER BY LineNo
    LIMIT 10
""")

items = cursor.fetchall()

print(f"\nFirst 10 items for CPQTEST26:")
print("-" * 100)
print(f"{'Line':<6} {'ItemNo':<20} {'MCT':<8} {'MCTDesc':<25} {'ItemDesc1':<40}")
print("-" * 100)

for item in items:
    line = item['LineNo'] or ''
    itemno = item['ItemNo'] or ''
    mct = item['ItemMasterMCT'] or ''
    mct_desc = item['MCTDesc'] or ''
    desc = item['ItemDesc1'] or ''
    print(f"{str(line):<6} {itemno:<20} {mct:<8} {mct_desc:<25} {desc:<40}")

# Check specifically for BOA items
cursor.execute("""
    SELECT COUNT(*) as count
    FROM BoatOptions26
    WHERE BoatSerialNo = 'CPQTEST26'
      AND ItemMasterMCT = 'BOA'
""")

boa_count = cursor.fetchone()['count']
print(f"\n\n✓ Items with MCT='BOA': {boa_count}")

# Check what MCT values exist for this boat
cursor.execute("""
    SELECT 
        ItemMasterMCT,
        COUNT(*) as count
    FROM BoatOptions26
    WHERE BoatSerialNo = 'CPQTEST26'
    GROUP BY ItemMasterMCT
    ORDER BY ItemMasterMCT
""")

mct_summary = cursor.fetchall()
print(f"\n\nMCT Summary:")
print("-" * 50)
for row in mct_summary:
    mct = row['ItemMasterMCT'] or 'NULL'
    count = row['count']
    print(f"  {mct:<20} : {count:>3} items")

cursor.close()
conn.close()

#!/usr/bin/env python3
"""
Check if ETWSTICKTEST26 has an engine (needed for pre-rig to display)
"""

import mysql.connector

# Database connection
conn = mysql.connector.connect(
    host='ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    user='awsmaster',
    password='VWvHG9vfG23g7gD',
    database='warrantyparts'
)

cursor = conn.cursor(dictionary=True)

print("\n" + "="*80)
print("Checking Engine Status for ETWSTICKTEST26")
print("="*80)

# Query for engine items
cursor.execute("""
    SELECT
        ItemNo,
        ItemDesc1,
        ItemMasterMCT,
        MCTDesc,
        ExtSalesAmount
    FROM BoatOptions26
    WHERE BoatSerialNo = 'ETWSTICKTEST26'
      AND (MCTDesc = 'ENGINES' OR MCTDesc = 'Engine' OR ItemMasterMCT = 'ENG')
    LIMIT 10
""")

engines = cursor.fetchall()

if engines:
    print(f"\n✅ Found {len(engines)} engine items:\n")
    for row in engines:
        print(f"ItemNo:      {row['ItemNo']}")
        print(f"ItemDesc1:   {row['ItemDesc1']}")
        print(f"ItemMasterMCT: {row['ItemMasterMCT']}")
        print(f"MCTDesc:     {row['MCTDesc']}")
        print(f"Cost:        ${row['ExtSalesAmount']}")
        print("-" * 80)
else:
    print("\n❌ NO ENGINE FOUND!")
    print("\nThis explains why pre-rig is not showing on window sticker.")
    print("The Calculate2021.js code requires hasengine === '1' for pre-rig to display.")
    print("\nCondition at line 416:")
    print("  if (hasengine === '1' && hasprerig === '1' && removeengine === '0') {")
    print("      var showpkgline = 1;  // Allows PRE-RIG to be pushed to boattable")
    print("  }")

cursor.close()
conn.close()

print("="*80 + "\n")

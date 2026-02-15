#!/usr/bin/env python3
"""
Check the MCTDesc value for the pre-rig item on ETWSTICKTEST26
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
print("Checking MCTDesc for Pre-Rig Item on ETWSTICKTEST26")
print("="*80)

# Query for pre-rig item
cursor.execute("""
    SELECT
        ItemNo,
        ItemDesc1,
        ItemMasterMCT,
        MCTDesc,
        ExtSalesAmount,
        ItemMasterProdCat
    FROM BoatOptions26
    WHERE BoatSerialNo = 'ETWSTICKTEST26'
      AND (ItemMasterMCT = 'PRE' OR MCTDesc LIKE '%PRE%' OR MCTDesc LIKE '%PRERIG%')
    LIMIT 10
""")

results = cursor.fetchall()

if results:
    print(f"\nFound {len(results)} pre-rig items:\n")
    for row in results:
        print(f"ItemNo:            {row['ItemNo']}")
        print(f"ItemDesc1:         {row['ItemDesc1']}")
        print(f"ItemMasterMCT:     {row['ItemMasterMCT']}")
        print(f"MCTDesc:           {row['MCTDesc']}")  # <-- This is the key field
        print(f"ItemMasterProdCat: {row['ItemMasterProdCat']}")
        print(f"ExtSalesAmount:    ${row['ExtSalesAmount']}")
        print("-" * 80)
else:
    print("\nNo pre-rig items found!")

cursor.close()
conn.close()

print("="*80 + "\n")

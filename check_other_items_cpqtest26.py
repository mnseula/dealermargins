#!/usr/bin/env python3
"""
Check what items are in the "Other" category for CPQTEST26
"""

import mysql.connector

conn = mysql.connector.connect(
    host='ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    user='awsmaster',
    password='VWvHG9vfG23g7gD',
    database='warrantyparts'
)

cursor = conn.cursor(dictionary=True)

print("\n" + "="*100)
print("CPQTEST26 - 'Other' Category Items (Not BOA, PRE, or ACC)")
print("="*100)

cursor.execute("""
    SELECT
        ItemNo,
        ItemDesc1,
        ItemMasterMCT,
        MCTDesc,
        ItemMasterProdCat,
        ExtSalesAmount,
        MSRP
    FROM BoatOptions26
    WHERE BoatSerialNo = 'CPQTEST26'
      AND ItemMasterMCT NOT IN ('BOA', 'BOI', 'PRE', 'ENG')
      AND (ItemMasterProdCat != 'ACC' OR ItemMasterProdCat IS NULL)
      AND (ExtSalesAmount > 0 OR MSRP > 0)
    ORDER BY ExtSalesAmount DESC
""")

items = cursor.fetchall()

print(f"\nFound {len(items)} items with non-zero costs:\n")
print(f"{'Description':<50} {'MCT':>6} {'ProdCat':>10} {'Dealer Cost':>15} {'MSRP':>15}")
print("-" * 100)

for item in items:
    print(f"{item['ItemDesc1'][:50]:<50} {item['ItemMasterMCT']:>6} {item['ItemMasterProdCat'] or 'NULL':>10} ${float(item['ExtSalesAmount'] or 0):>14,.2f} ${float(item['MSRP'] or 0):>14,.2f}")

print("\n" + "="*100)
print("Should these items appear on the window sticker?")
print("="*100)

cursor.close()
conn.close()

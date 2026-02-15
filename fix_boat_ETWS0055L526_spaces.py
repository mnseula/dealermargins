#!/usr/bin/env python3
"""
Fix boat ETWS0055L526 by removing spaces from the problematic ItemDesc1
that's breaking the jQuery selector in the flyer generation
"""
import mysql.connector

conn = mysql.connector.connect(
    host='ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    user='awsmaster',
    password='VWvHG9vfG23g7gD',
    database='warrantyparts'
)

cursor = conn.cursor(dictionary=True)

print("\n" + "=" * 100)
print("FIXING BOAT ETWS0055L526 - jQuery Selector Issue")
print("=" * 100)

# Check current state
cursor.execute("""
    SELECT
        ItemNo,
        ItemDesc1,
        ItemMasterMCT,
        MSRP,
        ExtSalesAmount
    FROM BoatOptions26
    WHERE BoatSerialNo = 'ETWS0055L526'
      AND ItemNo = '25RXFBASF'
""")

item = cursor.fetchone()

if not item:
    print("\n❌ Item 25RXFBASF not found for boat ETWS0055L526")
    cursor.close()
    conn.close()
    exit(1)

print(f"\n📋 Current State:")
print(f"   ItemNo: {item['ItemNo']}")
print(f"   ItemDesc1: '{item['ItemDesc1']}'")
print(f"   MCT: {item['ItemMasterMCT']}")

old_desc = item['ItemDesc1']
new_desc = old_desc.replace(' ', '-')  # Replace spaces with hyphens

print(f"\n🔄 Proposed Change:")
print(f"   OLD: '{old_desc}'")
print(f"   NEW: '{new_desc}'")

# Update the description
cursor.execute("""
    UPDATE BoatOptions26
    SET ItemDesc1 = %s
    WHERE BoatSerialNo = 'ETWS0055L526'
      AND ItemNo = '25RXFBASF'
""", (new_desc,))

rows_affected = cursor.rowcount
conn.commit()

print(f"\n✅ Updated {rows_affected} row(s)")

# Verify the change
cursor.execute("""
    SELECT ItemDesc1
    FROM BoatOptions26
    WHERE BoatSerialNo = 'ETWS0055L526'
      AND ItemNo = '25RXFBASF'
""")

updated = cursor.fetchone()
print(f"\n✔️  Verified New Value: '{updated['ItemDesc1']}'")

print("\n" + "=" * 100)
print("DONE - Try generating the flyer again")
print("=" * 100 + "\n")

cursor.close()
conn.close()

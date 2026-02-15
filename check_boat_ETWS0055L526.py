#!/usr/bin/env python3
"""
Check boat ETWS0055L526 for items that might cause jQuery selector issues
"""
import mysql.connector

conn = mysql.connector.connect(
    host='ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    user='awsmaster',
    password='VWvHG9vfG23g7gD',
    database='warrantyparts'
)

cursor = conn.cursor(dictionary=True)

print("\nBoat ETWS0055L526 - Items that could cause selector issues:")
print("=" * 100)

# Check for Base Boat line
cursor.execute("""
    SELECT
        ItemNo,
        ItemDesc1,
        BoatModelNo,
        MSRP,
        ExtSalesAmount
    FROM BoatOptions26
    WHERE BoatSerialNo = 'ETWS0055L526'
      AND ItemNo = 'Base Boat'
""")

base_boat = cursor.fetchone()
if base_boat:
    print("\n✅ Base Boat Line:")
    print(f"   ItemNo: {base_boat['ItemNo']}")
    print(f"   ItemDesc1: {base_boat['ItemDesc1']}")
    print(f"   Model: {base_boat['BoatModelNo']}")
    print(f"   MSRP: ${base_boat['MSRP']:,.2f}" if base_boat['MSRP'] else "   MSRP: None")
else:
    print("\n❌ No Base Boat line found")

# Check all items with spaces in ItemDesc1
cursor.execute("""
    SELECT
        ItemNo,
        ItemDesc1,
        ItemMasterMCT,
        LENGTH(ItemDesc1) - LENGTH(REPLACE(ItemDesc1, ' ', '')) as space_count
    FROM BoatOptions26
    WHERE BoatSerialNo = 'ETWS0055L526'
      AND ItemDesc1 LIKE '% %'
    ORDER BY space_count DESC
    LIMIT 20
""")

items_with_spaces = cursor.fetchall()
print(f"\n\nItems with spaces in description ({len(items_with_spaces)} found):")
print("-" * 100)
print(f"{'ItemNo':<20} {'Spaces':<8} {'ItemDesc1':<60}")
print("-" * 100)

for item in items_with_spaces[:10]:
    print(f"{item['ItemNo']:<20} {item['space_count']:<8} {item['ItemDesc1']:<60}")

# Check for items that might be used as IDs in the sortable list
cursor.execute("""
    SELECT DISTINCT
        ItemNo,
        ItemDesc1,
        ItemMasterMCT,
        MCTDesc
    FROM BoatOptions26
    WHERE BoatSerialNo = 'ETWS0055L526'
      AND (ItemDesc1 LIKE '%ARCH%'
           OR ItemDesc1 LIKE '%FASTBACK%'
           OR ItemDesc1 LIKE '%RX%')
    ORDER BY LineNo
""")

problematic_items = cursor.fetchall()
if problematic_items:
    print(f"\n\n🔍 Potentially problematic items (ARCH/FASTBACK/RX):")
    print("-" * 100)
    for item in problematic_items:
        print(f"   ItemNo: {item['ItemNo']}")
        print(f"   ItemDesc1: {item['ItemDesc1']}")
        print(f"   MCT: {item['ItemMasterMCT']} ({item['MCTDesc']})")
        print()

cursor.close()
conn.close()

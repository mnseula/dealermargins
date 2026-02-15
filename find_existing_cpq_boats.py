#!/usr/bin/env python3
"""
Find all boats in BoatOptions26 that have CPQ indicators
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
print("Finding CPQ Boats in BoatOptions26")
print("="*100)

# Check for boats with "Base Boat" description
print("\n1. Boats with 'Base Boat' line item:")
cursor.execute("""
    SELECT DISTINCT
        BoatSerialNo,
        BoatModelNo,
        ItemDesc1,
        MSRP,
        ExtSalesAmount
    FROM BoatOptions26
    WHERE ItemDesc1 LIKE '%Base Boat%'
       OR ItemDesc1 LIKE '%base boat%'
    ORDER BY BoatSerialNo
    LIMIT 20
""")

base_boat_boats = cursor.fetchall()
print(f"Found {len(base_boat_boats)} boats with 'Base Boat' line:")
for boat in base_boat_boats[:10]:
    print(f"  {boat['BoatSerialNo']:<20} {boat['BoatModelNo']:<15} {boat['ItemDesc1']:<30} MSRP: ${float(boat['MSRP'] or 0):,.2f}")

# Check for boats with CfgName (CPQ indicator)
print("\n2. Boats with CfgName field (CPQ indicator):")
cursor.execute("""
    SELECT DISTINCT
        BoatSerialNo,
        BoatModelNo,
        COUNT(DISTINCT CASE WHEN CfgName IS NOT NULL AND CfgName != '' THEN ItemNo END) as cpq_items,
        COUNT(DISTINCT ItemNo) as total_items
    FROM BoatOptions26
    WHERE BoatSerialNo IS NOT NULL
      AND BoatSerialNo != ''
    GROUP BY BoatSerialNo, BoatModelNo
    HAVING cpq_items > 0
    ORDER BY cpq_items DESC
    LIMIT 20
""")

cfg_boats = cursor.fetchall()
print(f"Found {len(cfg_boats)} boats with CfgName:")
for boat in cfg_boats[:10]:
    print(f"  {boat['BoatSerialNo']:<20} {boat['BoatModelNo']:<15} CPQ items: {boat['cpq_items']:>3} / Total: {boat['total_items']:>3}")

# Check all unique boats
print("\n3. All unique boats in BoatOptions26:")
cursor.execute("""
    SELECT
        LEFT(BoatSerialNo, 2) as year_prefix,
        COUNT(DISTINCT BoatSerialNo) as boat_count
    FROM BoatOptions26
    WHERE BoatSerialNo IS NOT NULL
      AND BoatSerialNo != ''
    GROUP BY LEFT(BoatSerialNo, 2)
    ORDER BY year_prefix DESC
""")

year_counts = cursor.fetchall()
total_boats = sum(row['boat_count'] for row in year_counts)
print(f"Total unique boats: {total_boats}")
print("\nBy year prefix:")
for row in year_counts:
    print(f"  {row['year_prefix']}: {row['boat_count']} boats")

# Check specific test boats
print("\n4. Checking our test boats:")
test_serials = ['CPQTEST26', 'ETWSTICKTEST26']
for serial in test_serials:
    cursor.execute("""
        SELECT COUNT(DISTINCT ItemNo) as items
        FROM BoatOptions26
        WHERE BoatSerialNo = %s
    """, (serial,))

    result = cursor.fetchone()
    if result and result['items'] > 0:
        print(f"  ✅ {serial}: {result['items']} items found")

        # Check for Base Boat line
        cursor.execute("""
            SELECT ItemDesc1, MSRP, ExtSalesAmount
            FROM BoatOptions26
            WHERE BoatSerialNo = %s
              AND (ItemDesc1 LIKE '%Base Boat%' OR ItemDesc1 LIKE '%base boat%')
            LIMIT 1
        """, (serial,))

        base = cursor.fetchone()
        if base:
            print(f"     Has Base Boat: {base['ItemDesc1']}, MSRP: ${float(base['MSRP'] or 0):,.2f}")
        else:
            print(f"     ❌ No Base Boat line found")
    else:
        print(f"  ❌ {serial}: Not found")

cursor.close()
conn.close()

print("\n" + "="*100)

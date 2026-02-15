#!/usr/bin/env python3
"""
Check how many CPQ boats (model year 2026) are in BoatOptions26 vs SerialNumberMaster
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
print("CPQ Boat Registration Analysis")
print("="*100)

# Count unique boats in BoatOptions26
cursor.execute("""
    SELECT COUNT(DISTINCT BoatSerialNo) as total_boats
    FROM BoatOptions26
    WHERE BoatSerialNo IS NOT NULL
      AND BoatSerialNo != ''
""")
total_in_boatoptions = cursor.fetchone()['total_boats']

print(f"\n1. Total boats in BoatOptions26: {total_in_boatoptions}")

# Count boats in SerialNumberMaster ending in '26'
cursor.execute("""
    SELECT COUNT(*) as total_boats
    FROM `serialnumbermaster - from eos`
    WHERE SerialNumber LIKE '%26'
""")
total_in_serial_master = cursor.fetchone()['total_boats']

print(f"2. Total boats in SerialNumberMaster (ending in '26'): {total_in_serial_master}")

# Find boats in BoatOptions26 but NOT in SerialNumberMaster
cursor.execute("""
    SELECT DISTINCT bo.BoatSerialNo, bo.BoatModelNo, bo.InvoiceNo
    FROM BoatOptions26 bo
    LEFT JOIN `serialnumbermaster - from eos` sm ON bo.BoatSerialNo = sm.SerialNumber
    WHERE bo.BoatSerialNo IS NOT NULL
      AND bo.BoatSerialNo != ''
      AND sm.SerialNumber IS NULL
    ORDER BY bo.BoatSerialNo
    LIMIT 20
""")

unregistered_boats = cursor.fetchall()

print(f"\n3. Boats in BoatOptions26 but NOT in SerialNumberMaster: {len(unregistered_boats)} (showing first 20)")
print("-" * 100)
print(f"{'Serial Number':<20} {'Model':<15} {'Invoice':<15}")
print("-" * 100)

for boat in unregistered_boats:
    print(f"{boat['BoatSerialNo']:<20} {boat['BoatModelNo']:<15} {boat['InvoiceNo'] or 'N/A':<15}")

# Check if these unregistered boats look like CPQ boats
print("\n" + "="*100)
print("CPQ Boat Indicators (checking first 5 unregistered boats):")
print("="*100)

if unregistered_boats:
    for boat in unregistered_boats[:5]:
        serial = boat['BoatSerialNo']

        # Check for "Base Boat" line (CPQ indicator)
        cursor.execute("""
            SELECT ItemDesc1, ItemMasterMCT, ExtSalesAmount, MSRP
            FROM BoatOptions26
            WHERE BoatSerialNo = %s
              AND (ItemDesc1 LIKE '%Base Boat%' OR ItemDesc1 LIKE 'base boat')
            LIMIT 1
        """, (serial,))

        base_boat = cursor.fetchone()

        if base_boat:
            print(f"\n✅ {serial} - CPQ BOAT (has 'Base Boat' line)")
            print(f"   MSRP: ${base_boat['MSRP']:,.2f}, Dealer Cost: ${base_boat['ExtSalesAmount']:,.2f}")
        else:
            print(f"\n❌ {serial} - LEGACY BOAT (no 'Base Boat' line)")

print("\n" + "="*100)
print("RECOMMENDATION:")
print("="*100)
print("""
To register CPQ boats automatically, we can:

1. Create a bulk registration script that:
   - Finds boats in BoatOptions26 with "Base Boat" line (CPQ indicator)
   - Checks if they're already in SerialNumberMaster
   - Registers missing boats with appropriate dealer/invoice info

2. Set up a scheduled job to run this script regularly
   - Daily or weekly to catch new CPQ boats
   - Ensures all CPQ boats are available for window stickers

Would you like me to create the bulk registration script?
""")

cursor.close()
conn.close()

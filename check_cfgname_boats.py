#!/usr/bin/env python3
"""
Check which boats have CfgName field populated
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
print("Checking for boats with CfgName field populated")
print("="*100)

# Check if CfgName column exists
cursor.execute("""
    SHOW COLUMNS FROM BoatOptions26 LIKE 'CfgName'
""")

col_check = cursor.fetchone()
if col_check:
    print(f"\n✅ CfgName column exists in BoatOptions26")
else:
    print(f"\n❌ CfgName column does NOT exist in BoatOptions26")
    cursor.close()
    conn.close()
    exit(1)

# Check for any rows with CfgName
cursor.execute("""
    SELECT COUNT(*) as total_rows,
           COUNT(CASE WHEN CfgName IS NOT NULL AND CfgName != '' THEN 1 END) as rows_with_cfgname
    FROM BoatOptions26
""")

totals = cursor.fetchone()
print(f"\nTotal rows in BoatOptions26: {totals['total_rows']:,}")
print(f"Rows with CfgName populated: {totals['rows_with_cfgname']:,}")

# Get sample boats with CfgName
cursor.execute("""
    SELECT DISTINCT
        BoatSerialNo,
        BoatModelNo,
        COUNT(*) as items_with_cfgname
    FROM BoatOptions26
    WHERE CfgName IS NOT NULL
      AND CfgName != ''
    GROUP BY BoatSerialNo, BoatModelNo
    ORDER BY items_with_cfgname DESC
    LIMIT 10
""")

boats = cursor.fetchall()

if len(boats) > 0:
    print(f"\n✅ Found {len(boats)} boats with CfgName:")
    print(f"\n{'Serial':<20} {'Model':<15} {'Items with CfgName':>20}")
    print("-" * 100)
    for boat in boats:
        model = boat['BoatModelNo'] or 'NULL'
        print(f"{boat['BoatSerialNo']:<20} {model:<15} {boat['items_with_cfgname']:>20}")
else:
    print(f"\n❌ No boats found with CfgName populated")

# Check our test boats specifically
print("\n" + "="*100)
print("Checking specific test boats:")
print("="*100)

test_boats = ['CPQTEST26', 'ETWSTICKTEST26', 'ETWTEST26', 'TESTCPQ26', 'ETWINVTEST0226']

for serial in test_boats:
    cursor.execute("""
        SELECT COUNT(*) as total_items,
               COUNT(CASE WHEN CfgName IS NOT NULL AND CfgName != '' THEN 1 END) as cfgname_items
        FROM BoatOptions26
        WHERE BoatSerialNo = %s
    """, (serial,))

    result = cursor.fetchone()
    if result['total_items'] > 0:
        print(f"\n{serial}:")
        print(f"  Total items: {result['total_items']}")
        print(f"  Items with CfgName: {result['cfgname_items']}")

        # Get a sample CfgName value
        cursor.execute("""
            SELECT ItemDesc1, CfgName
            FROM BoatOptions26
            WHERE BoatSerialNo = %s
              AND CfgName IS NOT NULL
              AND CfgName != ''
            LIMIT 1
        """, (serial,))

        sample = cursor.fetchone()
        if sample:
            print(f"  Sample CfgName: {sample['CfgName']}")
            print(f"  Sample Item: {sample['ItemDesc1']}")
    else:
        print(f"\n{serial}: ❌ Not found")

cursor.close()
conn.close()
print("\n" + "="*100)

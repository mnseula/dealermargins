#!/usr/bin/env python3
"""Verify ETWINVTEST0122 is in BoatOptions22"""
import mysql.connector

conn = mysql.connector.connect(
    host='ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    port=3306,
    database='warrantyparts',
    user='awsmaster',
    password='VWvHG9vfG23g7gD'
)

cursor = conn.cursor(dictionary=True)

print('='*80)
print('VERIFY ETWINVTEST0122 IMPORT')
print('='*80)
print()

# Check BoatOptions22
cursor.execute('''
    SELECT
        COUNT(*) as cnt,
        MIN(BoatModelNo) as model,
        MIN(ERP_OrderNo) as order_no
    FROM BoatOptions22
    WHERE BoatSerialNo = 'ETWINVTEST0122'
''')

result = cursor.fetchone()

if result['cnt'] > 0:
    print(f'✅ Found in BoatOptions22: {result["cnt"]} rows')
    print(f'   Model: {result["model"]}')
    print(f'   Order: {result["order_no"]}')
    print()
    print('SUCCESS! Boat is now in the correct table.')
    print()
    print('Next step:')
    print('  - Refresh browser and search for ETWINVTEST0122 (new serial)')
    print('  - Should load correctly from BoatOptions22')
else:
    print('❌ NOT found in BoatOptions22')
    print()
    print('Did you run the import?')
    print('  python3 import_boatoptions_production.py')

# Check if still in old table
cursor.execute("SELECT COUNT(*) as cnt FROM BoatOptions99_04 WHERE BoatSerialNo = 'ETWINVTEST01'")
old_count = cursor.fetchone()['cnt']
if old_count > 0:
    print(f'⚠️  WARNING: Still {old_count} rows in BoatOptions99_04 with old serial')

cursor.close()
conn.close()

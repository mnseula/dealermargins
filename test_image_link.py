#!/usr/bin/env python3
"""
Test script to verify image_link is being returned in window sticker data
"""

import mysql.connector

# Database connection
conn = mysql.connector.connect(
    host='ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    user='awsmaster',
    password='VWvHG9vfG23g7gD',
    database='warrantyparts_test'
)

cursor = conn.cursor(dictionary=True)

print("\n" + "="*80)
print("Testing Image Link in Models Table")
print("="*80)

# Test 1: Check image links in Models table
print("\n1. Checking image_link field in Models table:")
cursor.execute("""
    SELECT model_id, series_id, model_name, image_link
    FROM Models
    WHERE image_link IS NOT NULL
    AND image_link != ''
    LIMIT 10
""")
results = cursor.fetchall()
print(f"   Found {len(results)} models with image links:")
for row in results:
    print(f"   - {row['model_id']}: {row['image_link'][:60]}...")

# Test 2: Check GetModelFullDetails procedure
print("\n2. Testing GetModelFullDetails('25QXFBWA', '00333836'):")
cursor.callproc('GetModelFullDetails', ['25QXFBWA', '00333836'])
for result in cursor.stored_results():
    data = result.fetchall()
    if data and 'image_link' in data[0]:
        print(f"   ✅ image_link field returned: {data[0]['image_link']}")
    elif data and 'model_id' in data[0]:
        print(f"   First result set (model info):")
        if 'image_link' in data[0]:
            print(f"      image_link: {data[0].get('image_link', 'NOT FOUND')}")
        else:
            print(f"      Available fields: {', '.join(data[0].keys())}")

# Test 3: Check specific test boats
print("\n3. Checking test boats (CPQTEST26, ETWTEST26):")
for boat_id in ['CPQTEST26', 'ETWTEST26', '25QXFBWA']:
    cursor.execute("""
        SELECT model_id, image_link
        FROM Models
        WHERE model_id = %s
    """, (boat_id,))
    result = cursor.fetchone()
    if result:
        img = result['image_link'] if result['image_link'] else '(empty)'
        print(f"   - {boat_id}: {img}")
    else:
        print(f"   - {boat_id}: (not found in Models table)")

cursor.close()
conn.close()

print("\n" + "="*80)
print("Test Complete")
print("="*80 + "\n")

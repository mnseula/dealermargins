#!/usr/bin/env python3
"""
Query ModelStandardFeatures table directly to check for duplicates
"""

import mysql.connector

conn = mysql.connector.connect(
    host='ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    user='awsmaster',
    password='VWvHG9vfG23g7gD',
    database='warrantyparts_test'
)

cursor = conn.cursor(dictionary=True)

model_id = '22MSB'
year = 2026

print("\n" + "="*100)
print(f"Checking ModelStandardFeatures for model {model_id}, year {year}")
print("="*100)

# Query the junction table
cursor.execute("""
    SELECT
        msf.model_id,
        sf.feature_id,
        sf.area,
        sf.description
    FROM ModelStandardFeatures msf
    JOIN StandardFeatures sf ON msf.feature_id = sf.feature_id
    WHERE msf.model_id = %s
    ORDER BY sf.area, sf.description
""", (model_id,))

features = cursor.fetchall()

print(f"\nTotal features returned: {len(features)}")

# Check for duplicates
seen = {}
duplicates = []

for feature in features:
    key = f"{feature['area']}:{feature['description']}"
    if key in seen:
        duplicates.append(feature)
        seen[key] += 1
    else:
        seen[key] = 1

if duplicates:
    print("\n❌ DUPLICATES FOUND:")
    print("-" * 100)
    print(f"{'Description':<60} {'Area':<20} {'Count':>8}")
    print("-" * 100)

    for key, count in seen.items():
        if count > 1:
            area, desc = key.split(':', 1)
            print(f"{desc[:60]:<60} {area:<20} {count:>8}x")

    print(f"\n{len(duplicates)} duplicate entries found!")
else:
    print("\n✅ No duplicates found in database")

# Group by area
areas = {}
for feature in features:
    area = feature['area']
    areas[area] = areas.get(area, 0) + 1

print("\n" + "="*100)
print("Features by Area:")
print("-" * 100)
for area, count in sorted(areas.items()):
    print(f"{area:<30} {count:>8}")

print("\n" + "="*100)

cursor.close()
conn.close()

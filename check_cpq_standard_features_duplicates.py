#!/usr/bin/env python3
"""
Check if GET_CPQ_STANDARD_FEATURES is returning duplicate features
"""

import mysql.connector

conn = mysql.connector.connect(
    host='ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    user='awsmaster',
    password='VWvHG9vfG23g7gD',
    database='warrantyparts_test'
)

cursor = conn.cursor(buffered=True)

# Call the stored procedure (same as sStatement does)
model_id = '22MSB'
year = 2026

print("\n" + "="*100)
print(f"Checking GET_CPQ_STANDARD_FEATURES for model {model_id}, year {year}")
print("="*100)

cursor.callproc('GET_CPQ_STANDARD_FEATURES', [model_id, year])

# Fetch results
features = []
for result in cursor.stored_results():
    features = result.fetchall()

print(f"\nTotal features returned: {len(features)}")

# Get column names
cursor.execute("SHOW COLUMNS FROM ModelStandardFeatures")
columns = [col[0] for col in cursor.fetchall()]

print(f"Columns: {columns}\n")

# Check for duplicates
feature_descriptions = {}
duplicates = []

print("Checking for duplicates...")
print("-" * 100)
print(f"{'Description':<60} {'Area':<20} {'Count':>8}")
print("-" * 100)

for feature in features:
    # Assuming feature is tuple: (model_id, feature_id, area, description, ...)
    if len(feature) >= 3:
        area = feature[2] if len(feature) > 2 else 'Unknown'
        desc = feature[3] if len(feature) > 3 else str(feature)

        key = f"{area}:{desc}"
        if key in feature_descriptions:
            feature_descriptions[key] += 1
            if feature_descriptions[key] == 2:  # First duplicate
                duplicates.append((area, desc))
        else:
            feature_descriptions[key] = 1

# Show duplicates
if duplicates:
    print("\n❌ DUPLICATES FOUND:")
    print("-" * 100)
    for area, desc in duplicates:
        count = feature_descriptions[f"{area}:{desc}"]
        print(f"{desc[:60]:<60} {area:<20} {count:>8}x")
else:
    print("\n✅ No duplicates found in database query")

# Group by area to see counts
areas = {}
for feature in features:
    if len(feature) >= 3:
        area = feature[2] if len(feature) > 2 else 'Unknown'
        areas[area] = areas.get(area, 0) + 1

print("\n" + "="*100)
print("Features by Area:")
print("-" * 100)
for area, count in sorted(areas.items()):
    print(f"{area:<30} {count:>8}")

cursor.close()
conn.close()

print("\n" + "="*100)

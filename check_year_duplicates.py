#!/usr/bin/env python3
"""
Check if ModelStandardFeatures has duplicate (model_id, feature_id, year) entries
"""

import mysql.connector

conn = mysql.connector.connect(
    host='ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    user='awsmaster',
    password='VWvHG9vfG23g7gD',
    database='warrantyparts_test'
)

cursor = conn.cursor(dictionary=True)

print("\n" + "="*100)
print("Checking ModelStandardFeatures for duplicate (model_id, feature_id, year) combinations")
print("="*100)

# Check schema first
cursor.execute("SHOW COLUMNS FROM ModelStandardFeatures")
columns = cursor.fetchall()

print("\nModelStandardFeatures columns:")
for col in columns:
    print(f"  - {col['Field']} ({col['Type']})")

# Check for duplicates with year
model_id = '22MSB'
year = 2026

print(f"\nChecking for duplicates: model_id='{model_id}', year={year}")
print("-" * 100)

cursor.execute("""
    SELECT model_id, feature_id, year, COUNT(*) as cnt
    FROM ModelStandardFeatures
    WHERE model_id = %s
      AND year = %s
    GROUP BY model_id, feature_id, year
    HAVING cnt > 1
    ORDER BY cnt DESC
""", (model_id, year))

duplicates = cursor.fetchall()

if duplicates:
    print(f"\n❌ Found {len(duplicates)} duplicate (model_id, feature_id, year) combinations:")
    print("-" * 100)
    print(f"{'Model ID':<15} {'Feature ID':<15} {'Year':>6} {'Count':>8}")
    print("-" * 100)

    for dup in duplicates[:20]:  # Show first 20
        print(f"{dup['model_id']:<15} {dup['feature_id']:<15} {dup['year']:>6} {dup['cnt']:>8}x")

    if len(duplicates) > 20:
        print(f"... and {len(duplicates) - 20} more")
else:
    print("\n✅ No duplicate (model_id, feature_id, year) combinations found")

# Check total count for this model/year
cursor.execute("""
    SELECT COUNT(*) as total
    FROM ModelStandardFeatures
    WHERE model_id = %s
      AND year = %s
""", (model_id, year))

total = cursor.fetchone()['total']
print(f"\nTotal entries for {model_id} / {year}: {total}")

# Execute the same query as the sStatement
print("\n" + "="*100)
print("Executing sStatement query:")
print("="*100)

cursor.execute("""
    SELECT
        sf.feature_id,
        sf.feature_code,
        sf.area,
        sf.description,
        sf.sort_order
    FROM warrantyparts_test.StandardFeatures sf
    JOIN warrantyparts_test.ModelStandardFeatures msf
        ON sf.feature_id = msf.feature_id
    WHERE msf.model_id = %s
      AND msf.year = %s
      AND sf.active = 1
    ORDER BY
        CASE sf.area
            WHEN 'Interior Features' THEN 1
            WHEN 'Exterior Features' THEN 2
            WHEN 'Console Features' THEN 3
            WHEN 'Warranty' THEN 4
            ELSE 5
        END,
        sf.sort_order
""", (model_id, year))

features = cursor.fetchall()
print(f"\nQuery returned {len(features)} features")

# Check for duplicates in result
seen = {}
result_duplicates = []

for feat in features:
    key = f"{feat['area']}:{feat['description']}"
    if key in seen:
        result_duplicates.append(feat)
        seen[key] += 1
    else:
        seen[key] = 1

if result_duplicates:
    print(f"\n❌ Query results contain {len(result_duplicates)} duplicate features")
    print("This means ModelStandardFeatures has duplicate rows!")
else:
    print("\n✅ Query results are unique")

cursor.close()
conn.close()

print("\n" + "="*100)

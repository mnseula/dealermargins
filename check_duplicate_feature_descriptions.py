#!/usr/bin/env python3
"""
Check if StandardFeatures table has duplicate descriptions
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
print("Checking StandardFeatures for duplicate descriptions")
print("="*100)

# Find features with duplicate descriptions
cursor.execute("""
    SELECT description, area, COUNT(*) as cnt, GROUP_CONCAT(feature_id) as feature_ids
    FROM StandardFeatures
    WHERE active = 1
    GROUP BY description, area
    HAVING cnt > 1
    ORDER BY cnt DESC, area, description
""")

duplicates = cursor.fetchall()

if duplicates:
    print(f"\n❌ Found {len(duplicates)} descriptions with multiple feature_ids:")
    print("-" * 100)
    print(f"{'Description':<50} {'Area':<20} {'Count':>8} {'Feature IDs':<30}")
    print("-" * 100)

    for dup in duplicates[:30]:
        print(f"{dup['description'][:50]:<50} {dup['area']:<20} {dup['cnt']:>8} {dup['feature_ids'][:30]}")

    if len(duplicates) > 30:
        print(f"... and {len(duplicates) - 30} more")
else:
    print("\n✅ No duplicate descriptions found")

# Now check specifically for 22MSB features
print("\n" + "="*100)
print("Checking features used by model 22MSB:")
print("="*100)

cursor.execute("""
    SELECT
        sf.feature_id,
        sf.description,
        sf.area,
        COUNT(*) OVER (PARTITION BY sf.description, sf.area) as description_count
    FROM StandardFeatures sf
    JOIN ModelStandardFeatures msf ON sf.feature_id = msf.feature_id
    WHERE msf.model_id = '22MSB'
      AND msf.year = 2026
      AND sf.active = 1
    ORDER BY description_count DESC, sf.area, sf.description
""")

features = cursor.fetchall()

duplicates_in_model = [f for f in features if f['description_count'] > 1]

if duplicates_in_model:
    print(f"\n❌ Model 22MSB has {len(duplicates_in_model)} features with duplicate descriptions:")
    print("-" * 100)
    print(f"{'Feature ID':<12} {'Description':<50} {'Area':<20} {'Count':>8}")
    print("-" * 100)

    # Group by description to show clearly
    seen_desc = set()
    for feat in duplicates_in_model:
        key = f"{feat['area']}:{feat['description']}"
        if key not in seen_desc:
            seen_desc.add(key)
            print(f"\n{feat['description'][:50]} [{feat['area']}] - appears {feat['description_count']}x:")

        print(f"  {feat['feature_id']:<12} {feat['description'][:50]:<50}")
else:
    print("\n✅ No features with duplicate descriptions for this model")

cursor.close()
conn.close()

print("\n" + "="*100)

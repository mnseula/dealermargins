#!/usr/bin/env python3
"""
Remove duplicate entries from ModelStandardFeatures table
Keeps only one unique combination of (model_id, feature_id)
"""

import mysql.connector

conn = mysql.connector.connect(
    host='ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    user='awsmaster',
    password='VWvHG9vfG23g7gD',
    database='warrantyparts_test'
)

cursor = conn.cursor()

print("\n" + "="*100)
print("Removing Duplicate Standard Features from ModelStandardFeatures")
print("="*100)

# Count before
cursor.execute("SELECT COUNT(*) FROM ModelStandardFeatures")
before_count = cursor.fetchone()[0]
print(f"\nBefore: {before_count} total entries")

# Find duplicates
cursor.execute("""
    SELECT model_id, feature_id, COUNT(*) as cnt
    FROM ModelStandardFeatures
    GROUP BY model_id, feature_id
    HAVING cnt > 1
""")

duplicates = cursor.fetchall()
print(f"Found {len(duplicates)} unique combinations with duplicates")

# Delete duplicates, keeping only the first occurrence
# Using a temporary table approach for safety
print("\nRemoving duplicates...")

cursor.execute("""
    CREATE TEMPORARY TABLE ModelStandardFeatures_unique AS
    SELECT DISTINCT model_id, feature_id
    FROM ModelStandardFeatures
""")

# Clear the original table
cursor.execute("DELETE FROM ModelStandardFeatures")

# Re-insert unique entries
cursor.execute("""
    INSERT INTO ModelStandardFeatures (model_id, feature_id)
    SELECT model_id, feature_id
    FROM ModelStandardFeatures_unique
""")

conn.commit()

# Count after
cursor.execute("SELECT COUNT(*) FROM ModelStandardFeatures")
after_count = cursor.fetchone()[0]
print(f"After: {after_count} total entries")
print(f"Removed: {before_count - after_count} duplicate entries")

print("\n" + "="*100)
print("✅ Duplicates removed successfully!")
print("="*100)

cursor.close()
conn.close()

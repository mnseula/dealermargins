#!/usr/bin/env python3
"""
Deep search for EOS list registry - where loadByListName gets its list definitions.
"""
import mysql.connector

db_config = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'Eos'
}

conn = mysql.connector.connect(**db_config)
cursor = conn.cursor(dictionary=True)

print("=" * 80)
print("SEARCHING FOR LIST REGISTRY IN EOS")
print("=" * 80)

# Get all tables
cursor.execute("SHOW TABLES")
all_tables = [list(t.values())[0] for t in cursor.fetchall()]

print(f"\nFound {len(all_tables)} tables in Eos database")

# Search for tables that might contain list definitions or configurations
search_patterns = ['list', 'config', 'registry', 'meta', 'schema', 'column', 'field', 'table', 'view']

candidate_tables = []
for table in all_tables:
    table_lower = table.lower()
    if any(pattern in table_lower for pattern in search_patterns):
        candidate_tables.append(table)

print(f"\nFound {len(candidate_tables)} candidate tables:")
for table in candidate_tables:
    print(f"  - {table}")

# Check each candidate table for anything related to BoatOptions
print("\n" + "=" * 80)
print("CHECKING CANDIDATE TABLES FOR BOATOPTIONS REFERENCES")
print("=" * 80)

for table in candidate_tables:
    try:
        # Get table structure
        cursor.execute(f"DESCRIBE {table}")
        columns = cursor.fetchall()
        col_names = [c['Field'] for c in columns]

        # Look for columns that might contain list names or table names
        relevant_cols = [c for c in col_names if any(keyword in c.lower() for keyword in ['name', 'table', 'list', 'id', 'key'])]

        if relevant_cols:
            print(f"\n📋 Table: {table}")
            print(f"   Relevant columns: {', '.join(relevant_cols)}")

            # Try to find BoatOptions mentions
            for col in relevant_cols:
                try:
                    cursor.execute(f"SELECT * FROM {table} WHERE {col} LIKE '%Boat%' OR {col} LIKE '%boat%' OR {col} LIKE '%26%' LIMIT 5")
                    results = cursor.fetchall()
                    if results:
                        print(f"   ✅ Found matches in {col}:")
                        for row in results:
                            print(f"      {row}")
                except:
                    pass

            # Also show first few rows to understand table structure
            try:
                cursor.execute(f"SELECT * FROM {table} LIMIT 3")
                sample = cursor.fetchall()
                if sample:
                    print(f"   Sample rows:")
                    for row in sample[:2]:
                        print(f"      {row}")
            except:
                pass

    except Exception as e:
        pass

# Also search for any tables with 'ID' column that might be the registry
print("\n" + "=" * 80)
print("SEARCHING FOR TABLES WITH 'ID' COLUMN (from error message)")
print("=" * 80)

for table in all_tables:
    try:
        cursor.execute(f"DESCRIBE {table}")
        columns = cursor.fetchall()
        col_names = [c['Field'] for c in columns]

        if 'ID' in col_names or 'id' in col_names:
            # Check if this table might contain list definitions
            cursor.execute(f"SELECT * FROM {table} LIMIT 1")
            sample = cursor.fetchone()
            if sample and any('list' in str(v).lower() or 'boat' in str(v).lower() for v in sample.values() if v):
                print(f"\n📌 {table} has ID column and might be relevant:")
                print(f"   Columns: {', '.join(col_names)}")
                print(f"   Sample: {sample}")
    except:
        pass

cursor.close()
conn.close()

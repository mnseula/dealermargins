#!/usr/bin/env python3
"""
Find where the BoatOptions26 query is defined in the EOS database.
The query explicitly lists columns - we need to find and update it.
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
print("SEARCHING FOR BOATOPTIONS26 QUERY DEFINITION")
print("=" * 80)

# Search for text containing parts of the query
search_patterns = [
    'BoatOptions26',
    'ExtSalesAmount',
    'QuantitySold',
    'ItemMasterProdCat',
    'BoatSerialNo',
    'warrantyparts.BoatOptions'
]

# Get all tables
cursor.execute("SHOW TABLES")
all_tables = [list(t.values())[0] for t in cursor.fetchall()]

print(f"\nSearching {len(all_tables)} tables for query definitions...\n")

found_matches = []

for table in all_tables:
    try:
        # Get table structure
        cursor.execute(f"DESCRIBE {table}")
        columns = cursor.fetchall()

        # Look for TEXT or VARCHAR columns that might contain SQL
        text_columns = [c['Field'] for c in columns if 'text' in c['Type'].lower() or 'varchar' in c['Type'].lower() or 'char' in c['Type'].lower()]

        if text_columns:
            for col in text_columns:
                # Search for any of our patterns
                for pattern in search_patterns:
                    try:
                        cursor.execute(f"SELECT * FROM {table} WHERE {col} LIKE '%{pattern}%' LIMIT 5")
                        results = cursor.fetchall()

                        if results:
                            for row in results:
                                # Check if this row contains SQL-like content
                                col_value = str(row[col])
                                if 'SELECT' in col_value.upper() and 'FROM' in col_value.upper():
                                    found_matches.append({
                                        'table': table,
                                        'column': col,
                                        'row': row,
                                        'pattern': pattern
                                    })
                                    print(f"✅ Found in {table}.{col}:")
                                    print(f"   Pattern: {pattern}")
                                    print(f"   SQL Content: {col_value[:200]}...")
                                    print()
                    except Exception as e:
                        pass
    except Exception as e:
        pass

if found_matches:
    print("=" * 80)
    print(f"FOUND {len(found_matches)} MATCHES")
    print("=" * 80)
    for match in found_matches:
        print(f"\nTable: {match['table']}")
        print(f"Column: {match['column']}")
        print(f"Row keys: {list(match['row'].keys())}")
else:
    print("=" * 80)
    print("NO QUERY DEFINITIONS FOUND IN DATABASE")
    print("=" * 80)
    print("\nThe query might be:")
    print("1. Hardcoded in EOS application code (not in database)")
    print("2. Stored in a configuration file")
    print("3. In a different database")
    print("4. Cached in memory/Redis")

cursor.close()
conn.close()

print("\n" + "=" * 80)
print("RECOMMENDED: Search EOS application files for 'BoatOptions26' query definition")
print("=" * 80)

#!/usr/bin/env python3
"""
Find EOS list configuration - how loadByListName knows which columns to return.
"""
import mysql.connector

# Database configuration
db_config = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'Eos'
}

def find_list_config():
    """Find where list columns are configured."""
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    print("=" * 80)
    print("SEARCHING FOR EOS LIST CONFIGURATION")
    print("=" * 80)

    # Get all tables
    cursor.execute("SHOW TABLES")
    all_tables = [list(t.values())[0] for t in cursor.fetchall()]

    # Look for tables that might contain list definitions
    candidate_tables = [t for t in all_tables if any(keyword in t.lower() for keyword in ['list', 'field', 'column', 'def', 'config'])]

    print(f"\nFound {len(candidate_tables)} candidate tables:")
    for table in candidate_tables[:20]:  # Limit to first 20
        print(f"  - {table}")

    # Check specific common EOS table names
    print("\n" + "=" * 80)
    print("CHECKING COMMON EOS TABLES")
    print("=" * 80)

    common_tables = [
        'LIST_FIELD_DEF',
        'list_field_def',
        'cfg_list_field_def',
        'CFG_LIST_FIELD_DEF',
        'listFieldDef',
        'ListFieldDef'
    ]

    for table in common_tables:
        if table in all_tables:
            print(f"\n✅ Found table: {table}")
            try:
                cursor.execute(f"SELECT * FROM {table} WHERE LIST_NAME LIKE '%BoatOptions%' OR LIST_NAME LIKE '%boat%' LIMIT 10")
                results = cursor.fetchall()
                if results:
                    print(f"  Contains BoatOptions definitions:")
                    for row in results:
                        print(f"    {row}")
                else:
                    print(f"  Table exists but no BoatOptions definitions found")
                    # Show structure
                    cursor.execute(f"DESCRIBE {table}")
                    cols = cursor.fetchall()
                    print(f"  Columns: {[c['Field'] for c in cols]}")
            except Exception as e:
                print(f"  Error querying: {e}")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    find_list_config()

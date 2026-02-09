#!/usr/bin/env python3
"""
Find the BoatOptions26 list definition - where columns are defined.
"""
import mysql.connector

# Database configuration
db_config = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'Eos'
}

def search_for_list_def():
    """Search for BoatOptions list definition."""
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    # Common EOS list definition table names
    possible_tables = [
        'cfg_list',
        'cfg_list_def',
        'list_def',
        'list_config',
        'list_columns',
        'cfg_list_columns',
        'list_field_def',
        'list_fields'
    ]

    print("=" * 80)
    print("SEARCHING FOR LIST DEFINITION TABLES")
    print("=" * 80)

    for table in possible_tables:
        try:
            cursor.execute(f"SELECT * FROM {table} WHERE LIST_NAME LIKE '%BoatOptions%' LIMIT 5")
            results = cursor.fetchall()
            if results:
                print(f"\n✅ FOUND in table '{table}':")
                for row in results:
                    print(f"  {row}")
        except Exception as e:
            # Table doesn't exist, try next one
            pass

    # Try with different column name patterns
    print("\n" + "=" * 80)
    print("TRYING DIFFERENT COLUMN PATTERNS")
    print("=" * 80)

    cursor.execute("SHOW TABLES")
    all_tables = [list(t.values())[0] for t in cursor.fetchall()]

    for table in all_tables:
        if 'list' in table.lower():
            try:
                cursor.execute(f"DESCRIBE {table}")
                columns = cursor.fetchall()
                col_names = [c['Field'] for c in columns]

                # Look for name-like columns
                name_cols = [c for c in col_names if 'name' in c.lower() or 'id' in c.lower()]

                if name_cols:
                    for col in name_cols:
                        try:
                            cursor.execute(f"SELECT * FROM {table} WHERE {col} LIKE '%BoatOptions%' LIMIT 3")
                            results = cursor.fetchall()
                            if results:
                                print(f"\n✅ Found in {table}.{col}:")
                                for row in results:
                                    print(f"  {row}")
                        except:
                            pass
            except:
                pass

    cursor.close()
    conn.close()

if __name__ == '__main__':
    search_for_list_def()

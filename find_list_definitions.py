#!/usr/bin/env python3
"""
Find where list definitions are stored in the database.
"""
import mysql.connector

# Database configuration - using Eos database which likely has list definitions
db_config = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'Eos'
}

def find_list_tables():
    """Find tables related to list definitions."""
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    print("=" * 80)
    print("SEARCHING FOR LIST-RELATED TABLES")
    print("=" * 80)

    # Find tables with 'list' in the name
    cursor.execute("SHOW TABLES LIKE '%list%'")
    tables = cursor.fetchall()
    print(f"\nTables with 'list' in name:")
    for table in tables:
        table_name = list(table.values())[0]
        print(f"  - {table_name}")

    # Find tables with 'cfg' in the name
    cursor.execute("SHOW TABLES LIKE '%cfg%'")
    tables = cursor.fetchall()
    print(f"\nTables with 'cfg' in name:")
    for table in tables:
        table_name = list(table.values())[0]
        print(f"  - {table_name}")

    # Search for BoatOptions in any table
    print("\n" + "=" * 80)
    print("SEARCHING FOR 'BoatOptions' REFERENCES")
    print("=" * 80)

    cursor.execute("SHOW TABLES")
    all_tables = cursor.fetchall()

    for table in all_tables:
        table_name = list(table.values())[0]
        try:
            # Check if table has columns that might contain 'BoatOptions'
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()

            # Look for columns that might contain list names
            name_columns = [c['Field'] for c in columns if 'name' in c['Field'].lower() or 'list' in c['Field'].lower() or 'table' in c['Field'].lower()]

            if name_columns:
                # Search for BoatOptions in these columns
                for col in name_columns:
                    try:
                        cursor.execute(f"SELECT * FROM {table_name} WHERE {col} LIKE '%BoatOptions%' LIMIT 5")
                        results = cursor.fetchall()
                        if results:
                            print(f"\nFound in table '{table_name}', column '{col}':")
                            for row in results:
                                print(f"  {row}")
                    except Exception as e:
                        pass  # Skip on error
        except Exception as e:
            pass  # Skip on error

    cursor.close()
    conn.close()

if __name__ == '__main__':
    find_list_tables()

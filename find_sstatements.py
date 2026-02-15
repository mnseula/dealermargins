#!/usr/bin/env python3
"""
Find sStatements Storage

Looks for where sStatements are stored (database table or file).

Usage:
    python3 find_sstatements.py

Author: Claude Code
Date: 2026-02-09
"""

import mysql.connector

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'warrantyparts',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD'
}

def main():
    print("="*80)
    print("SEARCHING FOR SSTATEMENTS STORAGE")
    print("="*80)
    print()

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        # Look for tables that might store sStatements
        print("Searching for tables with 'statement' or 'sql' in name...")
        cursor.execute("""
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = 'warrantyparts'
              AND (TABLE_NAME LIKE '%statement%'
                   OR TABLE_NAME LIKE '%sql%'
                   OR TABLE_NAME LIKE '%query%')
            ORDER BY TABLE_NAME
        """)

        tables = cursor.fetchall()
        if tables:
            print(f"Found {len(tables)} potential tables:")
            for row in tables:
                print(f"  - {row['TABLE_NAME']}")

                # Check if table has GET_CPQ entries
                try:
                    cursor.execute(f"SELECT * FROM {row['TABLE_NAME']} WHERE sStatement LIKE '%CPQ%' OR name LIKE '%CPQ%' LIMIT 1")
                    results = cursor.fetchall()
                    if results:
                        print(f"    ✅ Contains CPQ-related entries!")
                except:
                    pass
            print()
        else:
            print("No tables found with 'statement', 'sql', or 'query' in name")
            print()

        # Search all tables for columns named 'sStatement'
        print("Searching for columns named 'sStatement'...")
        cursor.execute("""
            SELECT TABLE_NAME, COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'warrantyparts'
              AND COLUMN_NAME LIKE '%statement%'
            ORDER BY TABLE_NAME
        """)

        columns = cursor.fetchall()
        if columns:
            print(f"Found {len(columns)} tables with statement-related columns:")
            for row in columns:
                print(f"  - {row['TABLE_NAME']}.{row['COLUMN_NAME']}")

                # Try to find CPQ entries
                try:
                    cursor.execute(f"SELECT * FROM {row['TABLE_NAME']} WHERE {row['COLUMN_NAME']} LIKE '%CPQ%' LIMIT 5")
                    results = cursor.fetchall()
                    if results:
                        print(f"    ✅ Contains {len(results)} CPQ entries")
                        for r in results:
                            print(f"       {r}")
                except Exception as e:
                    print(f"    (Could not query: {e})")
            print()
        else:
            print("No columns found with 'statement' in name")
            print()

        print("="*80)

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == '__main__':
    exit(main())

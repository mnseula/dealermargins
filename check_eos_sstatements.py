#!/usr/bin/env python3
"""
Check Eos Database for sStatements

Author: Claude Code
Date: 2026-02-09
"""

import mysql.connector

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'Eos',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD'
}

def main():
    print("="*80)
    print("CHECKING EOS DATABASE FOR SSTATEMENTS")
    print("="*80)
    print()

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        # Look for sStatement-related tables
        print("Looking for tables...")
        cursor.execute("""
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = 'Eos'
            ORDER BY TABLE_NAME
        """)

        tables = cursor.fetchall()
        print(f"Found {len(tables)} tables in Eos database")

        # Look for tables with statement/query in name
        statement_tables = [t for t in tables if 'statement' in t['TABLE_NAME'].lower() or 'query' in t['TABLE_NAME'].lower() or 'sql' in t['TABLE_NAME'].lower()]

        if statement_tables:
            print(f"\nTables with 'statement/query/sql' in name:")
            for t in statement_tables:
                print(f"  - {t['TABLE_NAME']}")

        # Check for sStatement column
        print("\nLooking for sStatement columns...")
        cursor.execute("""
            SELECT TABLE_NAME, COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'Eos'
              AND (COLUMN_NAME = 'sStatement' OR COLUMN_NAME LIKE '%statement%')
        """)

        cols = cursor.fetchall()
        if cols:
            print(f"Found {len(cols)} columns:")
            for c in cols:
                print(f"  - {c['TABLE_NAME']}.{c['COLUMN_NAME']}")

                # Try to find GET_CPQ entries
                try:
                    query = f"SELECT * FROM {c['TABLE_NAME']} WHERE {c['COLUMN_NAME']} = 'GET_CPQ_LHS_DATA' OR {c['COLUMN_NAME']} = 'GET_CPQ_STANDARD_FEATURES' LIMIT 1"
                    cursor.execute(query)
                    results = cursor.fetchall()
                    if results:
                        print(f"    ✅ FOUND CPQ ENTRIES!")
                        for r in results:
                            print(f"       {r}")
                    else:
                        # Try LIKE
                        query = f"SELECT * FROM {c['TABLE_NAME']} WHERE {c['COLUMN_NAME']} LIKE '%CPQ%' LIMIT 3"
                        cursor.execute(query)
                        results = cursor.fetchall()
                        if results:
                            print(f"    ✅ Found {len(results)} CPQ-related entries")
                except Exception as e:
                    print(f"    Error checking: {e}")
        else:
            print("No sStatement columns found")

        print("\n" + "="*80)

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

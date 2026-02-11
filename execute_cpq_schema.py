#!/usr/bin/env python3
"""
Execute create_cpq_database.sql to create the cpq database with empty tables

Author: Claude Code
Date: 2026-02-11
"""

import mysql.connector

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD'
}

def main():
    print("=" * 80)
    print("CREATING CPQ DATABASE")
    print("=" * 80)
    print()

    # Read SQL file
    print("Reading create_cpq_database.sql...")
    with open('create_cpq_database.sql', 'r') as f:
        lines = f.readlines()

    # Parse SQL into statements
    statements = []
    current_statement = []

    for line in lines:
        # Skip pure comment lines (but keep inline comments in SQL)
        stripped = line.strip()
        if not stripped or stripped.startswith('--'):
            continue

        current_statement.append(line)

        # Check if line ends with semicolon (end of statement)
        if ';' in line:
            stmt = ''.join(current_statement).strip()
            if stmt:
                statements.append(stmt)
            current_statement = []

    print(f"Found {len(statements)} SQL statements")
    print()

    # Connect without specifying database initially
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        for i, statement in enumerate(statements, 1):
            # Get first meaningful line for display
            display_line = statement.split('\n')[0]
            if display_line.startswith('--'):
                display_line = [l for l in statement.split('\n') if l.strip() and not l.strip().startswith('--')][0]
            display_line = display_line[:70]

            print(f"[{i}/{len(statements)}] {display_line}...")

            # Execute statement
            cursor.execute(statement)

        # Commit all changes
        conn.commit()

        print()
        print("=" * 80)
        print("✅ CPQ DATABASE CREATED SUCCESSFULLY")
        print("=" * 80)
        print()

        # Verify tables were created
        cursor.execute("USE cpq")
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]

        print(f"Created {len(tables)} tables in cpq database:")
        for table in sorted(tables):
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  ✓ {table} ({count} rows)")

        print()
        print("Next steps:")
        print("1. Update load_cpq_data.py to target 'cpq' database")
        print("2. Update import_boatoptions_production.py to route CPQ boats to cpq.BoatOptions")
        print("3. Update CPQ sStatements in EOS to query cpq database tables")
        print("4. Update EOS list mapping (BoatOptions26 → cpq.BoatOptions)")
        print()

    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
        return 1
    finally:
        cursor.close()
        conn.close()

    return 0

if __name__ == '__main__':
    exit(main())

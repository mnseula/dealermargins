#!/usr/bin/env python3
"""
Execute Schema Fix for BoatOptions Tables

Runs the fix_boatoptions_schema.sql script to add missing CPQ columns.

Usage:
    python3 run_schema_fix.py

Author: Claude Code
Date: 2026-02-09
"""

import mysql.connector
from mysql.connector import Error

# Database configuration
DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'warrantyparts',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD'
}

def main():
    print("="*80)
    print("APPLYING SCHEMA FIX TO BOATOPTIONS TABLES (2015-2025)")
    print("="*80)
    print()

    try:
        # Read SQL file
        print("Reading fix_boatoptions_schema.sql...")
        with open('fix_boatoptions_schema.sql', 'r') as f:
            sql_content = f.read()

        # Connect to database
        print("Connecting to database...")
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print("✅ Connected to database")
        print()

        # Split into individual statements and clean up
        # Remove comments and blank lines first
        lines = []
        for line in sql_content.split('\n'):
            stripped = line.strip()
            # Skip empty lines and comment-only lines
            if not stripped or stripped.startswith('--'):
                continue
            # Remove inline comments
            if '--' in stripped:
                stripped = stripped[:stripped.index('--')].strip()
            if stripped:
                lines.append(stripped)

        # Join lines and split by semicolon
        cleaned_sql = ' '.join(lines)
        statements = [s.strip() for s in cleaned_sql.split(';') if s.strip()]

        # Filter out USE statements
        statements = [s for s in statements if not s.upper().startswith('USE')]

        total_statements = len(statements)
        print(f"Found {total_statements} SQL statements to execute")
        print()

        # Execute each statement
        success_count = 0
        error_count = 0

        for i, statement in enumerate(statements, 1):
            # Skip comments and USE statements
            if statement.startswith('--') or statement.upper().startswith('USE'):
                continue

            # Get table name from ALTER TABLE statement
            if 'ALTER TABLE' in statement.upper():
                table_name = statement.split()[2]
                print(f"[{i}/{total_statements}] Updating {table_name}...", end=' ')
            else:
                print(f"[{i}/{total_statements}] Executing query...", end=' ')

            try:
                cursor.execute(statement)
                conn.commit()
                print("✅")
                success_count += 1
            except Error as e:
                # Check if error is about duplicate column (already exists)
                if 'Duplicate column name' in str(e):
                    print("⏭️  (columns already exist)")
                    success_count += 1
                else:
                    print(f"❌")
                    print(f"   Error: {e}")
                    error_count += 1

        print()
        print("="*80)
        print("RESULTS")
        print("="*80)
        print(f"Successful: {success_count}/{total_statements}")
        print(f"Errors: {error_count}/{total_statements}")
        print()

        # Verify final schema
        print("Verifying final schema...")
        cursor.execute("""
            SELECT
                TABLE_NAME,
                COUNT(*) as column_count
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'warrantyparts'
              AND TABLE_NAME REGEXP '^BoatOptions[0-9]{2}$'
            GROUP BY TABLE_NAME
            ORDER BY TABLE_NAME
        """)

        results = cursor.fetchall()
        all_correct = True

        for table_name, column_count in results:
            if column_count == 31:
                print(f"  ✅ {table_name}: {column_count} columns")
            else:
                print(f"  ❌ {table_name}: {column_count} columns (expected 31)")
                all_correct = False

        print()
        if all_correct:
            print("✅ All tables now have 31 columns!")
            print("✅ Schema fix completed successfully!")
        else:
            print("⚠️  Some tables still don't have the correct column count")

        print("="*80)

        cursor.close()
        conn.close()

    except FileNotFoundError:
        print("❌ Error: fix_boatoptions_schema.sql not found")
        print("   Make sure you're running this from the correct directory")
        return 1
    except Error as e:
        print(f"❌ Database error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == '__main__':
    exit(main())

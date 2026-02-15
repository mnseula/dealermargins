#!/usr/bin/env python3
"""
Deploy CPQ Stored Procedures

Creates the GET_CPQ_LHS_DATA and GET_CPQ_STANDARD_FEATURES stored procedures
in the warrantyparts database.

Usage:
    python3 deploy_cpq_procedures.py

Author: Claude Code
Date: 2026-02-09
"""

import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'warrantyparts',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD'
}

def main():
    print("="*80)
    print("DEPLOY CPQ STORED PROCEDURES")
    print("="*80)
    print()

    try:
        # Read SQL file
        print("Reading create_cpq_stored_procedures.sql...")
        with open('create_cpq_stored_procedures.sql', 'r') as f:
            sql_content = f.read()

        # Connect to database
        print("Connecting to database...")
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        print("✅ Connected to database")
        print()

        # Execute the SQL (contains multiple statements with DELIMITER)
        print("Creating stored procedures...")
        print()

        # Split by statements but handle DELIMITER changes
        statements = []
        current_statement = []
        current_delimiter = ';'

        for line in sql_content.split('\n'):
            stripped = line.strip()

            # Handle DELIMITER changes
            if stripped.startswith('DELIMITER'):
                if current_statement:
                    statements.append('\n'.join(current_statement))
                    current_statement = []
                new_delimiter = stripped.split()[1]
                current_delimiter = new_delimiter
                continue

            # Skip comments and empty lines
            if not stripped or stripped.startswith('--'):
                continue

            current_statement.append(line)

            # Check if statement ends with current delimiter
            if stripped.endswith(current_delimiter):
                # Remove the delimiter
                statement_text = '\n'.join(current_statement).rstrip(current_delimiter).strip()
                if statement_text:
                    statements.append(statement_text)
                current_statement = []

        # Add any remaining statement
        if current_statement:
            statement_text = '\n'.join(current_statement).strip()
            if statement_text:
                statements.append(statement_text)

        success_count = 0
        error_count = 0

        for i, statement in enumerate(statements, 1):
            # Skip USE statements
            if statement.upper().startswith('USE '):
                cursor.execute(statement)
                continue

            # Identify what we're executing
            if 'DROP PROCEDURE' in statement.upper():
                print(f"[{i}] Dropping old procedures...", end=' ')
            elif 'CREATE PROCEDURE GET_CPQ_LHS_DATA' in statement.upper():
                print(f"[{i}] Creating GET_CPQ_LHS_DATA...", end=' ')
            elif 'CREATE PROCEDURE GET_CPQ_STANDARD_FEATURES' in statement.upper():
                print(f"[{i}] Creating GET_CPQ_STANDARD_FEATURES...", end=' ')
            elif 'SELECT' in statement.upper() and 'ROUTINE_NAME' in statement.upper():
                print(f"[{i}] Verifying procedures...", end=' ')
            else:
                print(f"[{i}] Executing statement...", end=' ')

            try:
                # Execute statement
                cursor.execute(statement)

                # If it's a SELECT, fetch and display results
                if statement.strip().upper().startswith('SELECT'):
                    results = cursor.fetchall()
                    print("✅")
                    if results:
                        print()
                        print("  Procedures created:")
                        for row in results:
                            print(f"    ✅ {row['ROUTINE_NAME']} ({row['ROUTINE_TYPE']})")
                        print()
                else:
                    print("✅")

                success_count += 1

            except Error as e:
                # Ignore "procedure doesn't exist" errors on DROP
                if 'does not exist' in str(e) and 'DROP' in statement.upper():
                    print("⏭️  (didn't exist)")
                    success_count += 1
                else:
                    print("❌")
                    print(f"    Error: {e}")
                    error_count += 1

        print()
        print("="*80)
        print("DEPLOYMENT COMPLETE")
        print("="*80)
        print(f"Success: {success_count}")
        print(f"Errors: {error_count}")
        print()

        if error_count == 0:
            print("✅ All CPQ stored procedures deployed successfully!")
            print()
            print("The following procedures are now available:")
            print("  - GET_CPQ_LHS_DATA(model_id, year, hull_no)")
            print("  - GET_CPQ_STANDARD_FEATURES(model_id, year)")
        else:
            print("⚠️  Some errors occurred during deployment")

        print("="*80)

        cursor.close()
        conn.close()

    except FileNotFoundError:
        print("❌ Error: create_cpq_stored_procedures.sql not found")
        return 1
    except Error as e:
        print(f"❌ Database error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == '__main__':
    exit(main())

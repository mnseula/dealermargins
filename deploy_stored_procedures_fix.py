#!/usr/bin/env python3
"""Deploy updated stored procedures with boat item exclusion fix"""

import mysql.connector
import sys

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts_test'
}

def deploy_stored_procedures():
    """Deploy stored procedures from file"""

    print("Connecting to database...")
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Read the SQL file
    print("Reading stored_procedures.sql...")
    with open('stored_procedures.sql', 'r') as f:
        sql_content = f.read()

    # Split into individual statements (excluding comments and empty lines)
    print("Deploying stored procedures...")

    # Execute the file content
    # Need to handle delimiter changes
    for result in cursor.execute(sql_content, multi=True):
        if result.with_rows:
            result.fetchall()

    conn.commit()
    print("✅ Stored procedures deployed successfully!")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    try:
        deploy_stored_procedures()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

#!/usr/bin/env python3
import mysql.connector
import sys
import os

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts_test'
}

def run_sql_script(sql_file_path):
    """
    Connects to the database and executes the SQL script.
    Assumes SQL script might use 'DELIMITER $$' syntax.
    """
    if not os.path.exists(sql_file_path):
        print(f"Error: SQL file not found at {sql_file_path}")
        return

    print(f"Executing SQL script: {sql_file_path}")

    try:
        with open(sql_file_path, 'r') as f:
            sql_content = f.read()

        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Split by delimiter changes and execute
        # This handles SQL files that define stored procedures/functions
        commands = sql_content.split('$$')
        for command in commands:
            command = command.strip()
            if command and not command.startswith('--') and command != 'DELIMITER':
                try:
                    cursor.execute(command)
                except mysql.connector.Error as err:
                    # Ignore "Commands out of sync" which can happen with DELIMITER changes
                    if "Commands out of sync" not in str(err):
                        print(f"SQL Error during execution: {err}")
                        print(f"Failing SQL: {command[:200]}...") # Print first 200 chars of failing SQL
                    else:
                        print(f"Warning: Ignored 'Commands out of sync' error for a DELIMITER block.")
                except Exception as e:
                    print(f"An unexpected error occurred: {e}")
                    print(f"Failing SQL: {command[:200]}...")
        conn.commit()
        print(f"✓ Successfully executed {sql_file_path}")

    except mysql.connector.Error as err:
        print(f"Database connection or execution error: {err}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("Database connection closed.")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 run_sql_script.py <path_to_sql_file>")
        sys.exit(1)

    sql_file = sys.argv[1]
    run_sql_script(sql_file)

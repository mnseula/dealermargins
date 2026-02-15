#!/usr/bin/env python3
"""Search for CPQ-related tables in both databases"""
import mysql.connector

def search_cpq_tables(database_name):
    """Search for CPQ tables in specified database"""
    DB_CONFIG = {
        'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
        'user': 'awsmaster',
        'password': 'VWvHG9vfG23g7gD',
        'database': database_name
    }

    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        print(f"\n{'='*80}")
        print(f"DATABASE: {database_name}")
        print(f"{'='*80}")

        # Get all tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        table_names = [list(t.values())[0] for t in tables]

        # Find tables with CPQ in the name
        cpq_tables = [t for t in table_names if 'cpq' in t.lower() or 'dealer' in t.lower() and 'margin' in t.lower()]

        if cpq_tables:
            print(f"\nFound {len(cpq_tables)} CPQ/Margin-related tables:")
            for table in cpq_tables:
                print(f"\n  Table: {table}")

                # Get row count
                cursor.execute(f"SELECT COUNT(*) as count FROM `{table}`")
                count = cursor.fetchone()['count']
                print(f"    Rows: {count}")

                # Get column names
                cursor.execute(f"DESCRIBE `{table}`")
                columns = cursor.fetchall()
                column_names = [col['Field'] for col in columns]
                print(f"    Columns ({len(column_names)}): {', '.join(column_names[:10])}{'...' if len(column_names) > 10 else ''}")

        else:
            print("\nNo CPQ/Margin-related tables found")

        cursor.close()
        connection.close()

    except mysql.connector.Error as e:
        print(f"❌ Database error: {e}")
        if connection and connection.is_connected():
            connection.close()

def main():
    """Search both databases"""
    print("\n" + "="*80)
    print("SEARCHING FOR CPQ AND DEALER MARGIN TABLES")
    print("="*80)

    search_cpq_tables('warrantyparts')
    search_cpq_tables('warrantyparts_test')

if __name__ == "__main__":
    main()

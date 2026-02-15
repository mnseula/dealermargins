#!/usr/bin/env python3
"""Search for freight and prep values across the database"""
import mysql.connector

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts'
}

def search_all_tables():
    """Search all tables for freight=1500 and prep=1000"""
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        print("\n" + "="*80)
        print("SEARCHING ALL TABLES IN warrantyparts DATABASE")
        print("="*80)

        # Get all tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        table_names = [list(t.values())[0] for t in tables]

        print(f"\nFound {len(table_names)} tables in database\n")

        results_found = []

        for table_name in table_names:
            try:
                # Get column names
                cursor.execute(f"DESCRIBE `{table_name}`")
                columns = cursor.fetchall()
                column_names = [col['Field'] for col in columns]

                # Look for freight or prep related columns
                freight_cols = [col for col in column_names if 'freight' in col.lower()]
                prep_cols = [col for col in column_names if 'prep' in col.lower()]

                if freight_cols or prep_cols:
                    print(f"\n{'='*80}")
                    print(f"Table: {table_name}")
                    print(f"{'='*80}")
                    print(f"  Freight columns: {', '.join(freight_cols) if freight_cols else 'None'}")
                    print(f"  Prep columns: {', '.join(prep_cols) if prep_cols else 'None'}")

                    # Search for 1500 in freight columns
                    if freight_cols:
                        for col in freight_cols:
                            query = f"SELECT * FROM `{table_name}` WHERE `{col}` = 1500 LIMIT 5"
                            cursor.execute(query)
                            freight_results = cursor.fetchall()
                            if freight_results:
                                print(f"\n  ✓ Found {len(freight_results)} rows with {col}=1500")
                                for row in freight_results[:3]:
                                    print(f"    Row: {row}")
                                results_found.append((table_name, col, 1500, len(freight_results)))

                    # Search for 1000 in prep columns
                    if prep_cols:
                        for col in prep_cols:
                            query = f"SELECT * FROM `{table_name}` WHERE `{col}` = 1000 LIMIT 5"
                            cursor.execute(query)
                            prep_results = cursor.fetchall()
                            if prep_results:
                                print(f"\n  ✓ Found {len(prep_results)} rows with {col}=1000")
                                for row in prep_results[:3]:
                                    print(f"    Row: {row}")
                                results_found.append((table_name, col, 1000, len(prep_results)))

            except mysql.connector.Error as e:
                print(f"  ⚠️  Error querying {table_name}: {e}")

        # Summary
        print("\n" + "="*80)
        print("SEARCH SUMMARY")
        print("="*80)
        if results_found:
            print(f"Found {len(results_found)} matches:\n")
            for table, col, val, count in results_found:
                print(f"  • {table}.{col} = {val} ({count} rows)")
        else:
            print("No tables found with Freight=1500 or Prep=1000")

        # Also check for any default configuration tables
        print("\n" + "="*80)
        print("CHECKING FOR CONFIGURATION TABLES")
        print("="*80)
        config_keywords = ['config', 'setting', 'default', 'constant', 'param']
        config_tables = [t for t in table_names if any(keyword in t.lower() for keyword in config_keywords)]

        if config_tables:
            print(f"\nFound {len(config_tables)} potential configuration tables:")
            for table in config_tables:
                print(f"  • {table}")
                cursor.execute(f"SELECT * FROM `{table}` LIMIT 10")
                rows = cursor.fetchall()
                if rows:
                    print(f"    Sample data: {rows[0]}")
        else:
            print("\nNo obvious configuration tables found")

        cursor.close()
        connection.close()

    except mysql.connector.Error as e:
        print(f"❌ Database error: {e}")
        if connection and connection.is_connected():
            connection.close()

if __name__ == "__main__":
    search_all_tables()

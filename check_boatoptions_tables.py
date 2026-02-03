#!/usr/bin/env python3
"""
Check what BoatOptions tables exist in warrantyparts database
"""
import mysql.connector

MYSQL_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'warrantyparts',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD'
}

def main():
    print("="*70)
    print("CHECKING BOATOPTIONS TABLES IN WARRANTYPARTS DATABASE")
    print("="*70)

    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()

        # Get all tables that start with BoatOptions
        cursor.execute("SHOW TABLES LIKE 'BoatOptions%'")
        tables = cursor.fetchall()

        print(f"\nFound {len(tables)} BoatOptions tables:\n")
        for table in tables:
            table_name = table[0]

            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]

            # Get sample serial numbers to see year pattern
            cursor.execute(f"""
                SELECT DISTINCT BoatSerialNo
                FROM {table_name}
                WHERE BoatSerialNo IS NOT NULL
                LIMIT 3
            """)
            serials = cursor.fetchall()

            print(f"  {table_name:30s} - {count:8,d} rows")
            if serials:
                print(f"    Sample serials: {', '.join([s[0] for s in serials if s[0]])}")
            print()

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    main()

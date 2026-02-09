#!/usr/bin/env python3
"""
Check if BoatOptions26 exists in both databases and how it's defined.
"""
import mysql.connector

configs = [
    {'name': 'warrantyparts', 'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com', 'user': 'awsmaster', 'password': 'VWvHG9vfG23g7gD', 'database': 'warrantyparts'},
    {'name': 'Eos', 'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com', 'user': 'awsmaster', 'password': 'VWvHG9vfG23g7gD', 'database': 'Eos'}
]

for config in configs:
    print("=" * 80)
    print(f"DATABASE: {config['name']}")
    print("=" * 80)

    try:
        conn = mysql.connector.connect(
            host=config['host'],
            user=config['user'],
            password=config['password'],
            database=config['database']
        )
        cursor = conn.cursor(dictionary=True)

        # Check if BoatOptions26 exists
        cursor.execute("SHOW FULL TABLES LIKE 'BoatOptions26'")
        result = cursor.fetchone()

        if result:
            table_type = result['Table_type']
            print(f"\n✅ BoatOptions26 exists as: {table_type}")

            if table_type == 'VIEW':
                print("\nVIEW DEFINITION:")
                cursor.execute("SHOW CREATE VIEW BoatOptions26")
                view_def = cursor.fetchone()
                print(view_def.get('Create View', ''))
            else:
                print("\nTABLE DEFINITION (columns only):")
                cursor.execute("DESCRIBE BoatOptions26")
                columns = cursor.fetchall()
                for col in columns:
                    print(f"  {col['Field']:30s} {col['Type']:20s}")

                # Check if MSRP exists
                msrp_cols = [c for c in columns if c['Field'] == 'MSRP']
                if msrp_cols:
                    print(f"\n✅ MSRP column EXISTS")
                else:
                    print(f"\n❌ MSRP column DOES NOT EXIST")
        else:
            print(f"\n❌ BoatOptions26 does NOT exist in {config['name']}")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error accessing {config['name']}: {e}")

    print()

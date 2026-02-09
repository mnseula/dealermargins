#!/usr/bin/env python3
"""
Check for stored procedures or views that might control BoatOptions26 queries.
"""
import mysql.connector

# Check both databases
configs = [
    {'name': 'warrantyparts', 'database': 'warrantyparts'},
    {'name': 'Eos', 'database': 'Eos'}
]

for config in configs:
    print("=" * 80)
    print(f"DATABASE: {config['name']}")
    print("=" * 80)

    conn = mysql.connector.connect(
        host='ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
        user='awsmaster',
        password='VWvHG9vfG23g7gD',
        database=config['database']
    )
    cursor = conn.cursor(dictionary=True)

    # Find all stored procedures
    print("\n📋 STORED PROCEDURES:")
    cursor.execute(f"SELECT ROUTINE_NAME FROM INFORMATION_SCHEMA.ROUTINES WHERE ROUTINE_SCHEMA = '{config['database']}' AND ROUTINE_TYPE = 'PROCEDURE' AND ROUTINE_NAME LIKE '%Boat%'")
    procs = cursor.fetchall()
    if procs:
        for proc in procs:
            print(f"  - {proc['ROUTINE_NAME']}")
            # Try to show definition
            try:
                cursor.execute(f"SHOW CREATE PROCEDURE {proc['ROUTINE_NAME']}")
                result = cursor.fetchone()
                if result and 'BoatOptions26' in result.get('Create Procedure', ''):
                    print(f"    ✅ Contains 'BoatOptions26'")
            except:
                pass
    else:
        print("  (none found)")

    # Find all views
    print("\n👁️  VIEWS:")
    cursor.execute(f"SELECT TABLE_NAME FROM INFORMATION_SCHEMA.VIEWS WHERE TABLE_SCHEMA = '{config['database']}' AND TABLE_NAME LIKE '%Boat%'")
    views = cursor.fetchall()
    if views:
        for view in views:
            print(f"  - {view['TABLE_NAME']}")
            # Check if it references BoatOptions26
            try:
                cursor.execute(f"SHOW CREATE VIEW {view['TABLE_NAME']}")
                result = cursor.fetchone()
                if result and 'BoatOptions26' in result.get('Create View', ''):
                    print(f"    ✅ Contains 'BoatOptions26'")
            except:
                pass
    else:
        print("  (none found)")

    # Look for any list configuration tables
    print("\n📝 LOOKING FOR LIST CONFIG:")
    cursor.execute("SHOW TABLES LIKE '%list%'")
    list_tables = cursor.fetchall()
    if list_tables:
        for table in list_tables:
            table_name = list(table.values())[0]
            print(f"  - {table_name}")

            # Check if it contains BoatOptions references
            cursor.execute(f"DESCRIBE {table_name}")
            cols = cursor.fetchall()
            name_cols = [c['Field'] for c in cols if 'name' in c['Field'].lower()]

            if name_cols:
                for col in name_cols:
                    try:
                        cursor.execute(f"SELECT * FROM {table_name} WHERE {col} LIKE '%BoatOptions%' LIMIT 3")
                        results = cursor.fetchall()
                        if results:
                            print(f"    ✅ Found BoatOptions in {col}:")
                            for row in results:
                                print(f"       {row}")
                    except:
                        pass
    else:
        print("  (none found)")

    cursor.close()
    conn.close()
    print()

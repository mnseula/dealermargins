#!/usr/bin/env python3
"""
Fix ERP_OrderNo Column Type

Changes ERP_OrderNo from INT to VARCHAR(30) in old BoatOptions tables.

Usage:
    python3 run_erp_orderno_fix.py

Author: Claude Code
Date: 2026-02-10
"""

import mysql.connector

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'warrantyparts',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD'
}

def main():
    print("="*80)
    print("FIX ERP_OrderNo COLUMN TYPE")
    print("="*80)
    print("Changing ERP_OrderNo from INT to VARCHAR(30) in old tables")
    print("This allows CPQ order numbers like 'SO00936074' to be stored correctly")
    print("="*80)
    print()

    tables_to_fix = [
        'BoatOptionsBefore_05',
        'BoatOptions99_04',
        'BoatOptions05_07',
        'BoatOptions08_10',
        'BoatOptions11_14',
        'BoatOptions15',
        'BoatOptions16',
        'BoatOptions17',
        'BoatOptions18',
        'BoatOptions19',
        'BoatOptions20',
        'BoatOptions21'
    ]

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        success_count = 0
        error_count = 0

        for table in tables_to_fix:
            print(f"Fixing {table}...", end=' ')
            try:
                cursor.execute(f"ALTER TABLE {table} MODIFY COLUMN ERP_OrderNo VARCHAR(30)")
                conn.commit()
                print("✅")
                success_count += 1
            except Exception as e:
                print(f"❌ {e}")
                error_count += 1

        print()
        print("="*80)
        print("RESULTS")
        print("="*80)
        print(f"Success: {success_count}/{len(tables_to_fix)}")
        print(f"Errors: {error_count}/{len(tables_to_fix)}")
        print()

        if success_count == len(tables_to_fix):
            print("✅ All tables fixed successfully!")
            print()
            print("Next steps:")
            print("1. Delete ETWINVTEST01 from BoatOptions99_04")
            print("2. Re-import to get correct ERP_OrderNo")
            print()
            print("Commands:")
            print("  DELETE FROM warrantyparts.BoatOptions99_04 WHERE BoatSerialNo = 'ETWINVTEST01';")
            print("  python3 import_boatoptions_production.py")
        else:
            print("⚠️  Some tables failed to update")

        print("="*80)

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == '__main__':
    exit(main())

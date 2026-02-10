#!/usr/bin/env python3
"""
Update ETWINVTEST01 to ETWINVTEST0122 in ERP Database

The serial needs to be updated in the ERP (CSI) database so that
future imports pull the correct serial number.

Author: Claude Code
Date: 2026-02-10
"""

import pymssql

MSSQL_CONFIG = {
    'server': 'MPL1STGSQL086.POLARISSTAGE.COM',
    'port': 1433,
    'database': 'BENNCSI',
    'user': 'CREImport',
    'password': 'BennCRE2023'
}

OLD_SERIAL = 'ETWINVTEST01'
NEW_SERIAL = 'ETWINVTEST0122'

def main():
    print("="*80)
    print("UPDATE ERP SERIAL NUMBER")
    print("="*80)
    print(f"Old: {OLD_SERIAL}")
    print(f"New: {NEW_SERIAL}")
    print("="*80)
    print()

    try:
        conn = pymssql.connect(**MSSQL_CONFIG)
        cursor = conn.cursor(as_dict=True)
        print("✅ Connected to ERP database")
        print()

        # Check current state
        print("1. Checking serial_mst...")
        cursor.execute("""
            SELECT ser_num, item, stat
            FROM serial_mst
            WHERE ser_num = %s
        """, (OLD_SERIAL,))

        row = cursor.fetchone()
        if row:
            print(f"   Found: {row['ser_num']}")
            print(f"   Item: {row['item']}")
            print(f"   Status: {row['stat']}")
            print()
        else:
            print(f"   ❌ Serial {OLD_SERIAL} not found in serial_mst")
            return 1

        # Update serial_mst
        print(f"2. Updating serial_mst...")
        cursor.execute("""
            UPDATE serial_mst
            SET ser_num = %s
            WHERE ser_num = %s
        """, (NEW_SERIAL, OLD_SERIAL))
        print(f"   ✅ Updated {cursor.rowcount} rows")
        print()

        # Check if serial exists in other tables (coitem, etc.)
        print("3. Checking coitem for Uf_BENN_BoatSerialNumber...")
        cursor.execute("""
            SELECT co_num, co_line, Uf_BENN_BoatSerialNumber
            FROM coitem_mst
            WHERE Uf_BENN_BoatSerialNumber = %s
        """, (OLD_SERIAL,))

        coitem_rows = cursor.fetchall()
        if coitem_rows:
            print(f"   Found {len(coitem_rows)} rows in coitem")
            for row in coitem_rows:
                print(f"     Order: {row['co_num']}, Line: {row['co_line']}")
            print()

            print("   Updating coitem_mst...")
            cursor.execute("""
                UPDATE coitem_mst
                SET Uf_BENN_BoatSerialNumber = %s
                WHERE Uf_BENN_BoatSerialNumber = %s
            """, (NEW_SERIAL, OLD_SERIAL))
            print(f"   ✅ Updated {cursor.rowcount} rows")
            print()
        else:
            print("   No rows in coitem (serial stored in serial_mst only)")
            print()

        # Commit
        conn.commit()
        print("="*80)
        print("✅ ERP DATABASE UPDATED")
        print("="*80)
        print()
        print("Next steps:")
        print("1. Run import: python3 import_boatoptions_production.py")
        print("2. Verify: python3 verify_etwinvtest0122.py")
        print()

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

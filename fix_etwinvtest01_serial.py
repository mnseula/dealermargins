#!/usr/bin/env python3
"""
Fix ETWINVTEST01 Serial Number

The boat is a 2022 model (22SFC) but has serial ending in "01" which routes
it to BoatOptions99_04 (1999-2004 table). Change serial to ETWINVTEST0122
so it routes correctly to BoatOptions22.

Steps:
1. Delete from BoatOptions99_04
2. Update SerialNumberMaster and SerialNumberRegistrationStatus
3. Re-import (will go to BoatOptions22)

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

OLD_SERIAL = 'ETWINVTEST01'
NEW_SERIAL = 'ETWINVTEST0122'

def main():
    print("="*80)
    print("FIX ETWINVTEST01 SERIAL NUMBER")
    print("="*80)
    print(f"Old Serial: {OLD_SERIAL} (routes to BoatOptions99_04)")
    print(f"New Serial: {NEW_SERIAL} (will route to BoatOptions22)")
    print("="*80)
    print()

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    try:
        # 1. Check current state
        print("1. Checking current state...")

        cursor.execute("SELECT COUNT(*) as cnt FROM BoatOptions99_04 WHERE BoatSerialNo = %s", (OLD_SERIAL,))
        old_table_count = cursor.fetchone()['cnt']
        print(f"   BoatOptions99_04: {old_table_count} rows")

        cursor.execute("SELECT COUNT(*) as cnt FROM SerialNumberMaster WHERE Boat_SerialNo = %s", (OLD_SERIAL,))
        snm_count = cursor.fetchone()['cnt']
        print(f"   SerialNumberMaster: {snm_count} rows")

        cursor.execute("SELECT COUNT(*) as cnt FROM SerialNumberRegistrationStatus WHERE Boat_SerialNo = %s", (OLD_SERIAL,))
        snr_count = cursor.fetchone()['cnt']
        print(f"   SerialNumberRegistrationStatus: {snr_count} rows")
        print()

        if old_table_count == 0 and snm_count == 0 and snr_count == 0:
            print("❌ No data found for", OLD_SERIAL)
            return 1

        # 2. Delete from BoatOptions99_04
        print(f"2. Deleting from BoatOptions99_04...")
        cursor.execute("DELETE FROM BoatOptions99_04 WHERE BoatSerialNo = %s", (OLD_SERIAL,))
        print(f"   ✅ Deleted {cursor.rowcount} rows")
        print()

        # 3. Update SerialNumberMaster
        if snm_count > 0:
            print(f"3. Updating SerialNumberMaster...")
            cursor.execute("""
                UPDATE SerialNumberMaster
                SET Boat_SerialNo = %s
                WHERE Boat_SerialNo = %s
            """, (NEW_SERIAL, OLD_SERIAL))
            print(f"   ✅ Updated {cursor.rowcount} rows")
            print()
        else:
            print("3. Skipping SerialNumberMaster (no rows)")
            print()

        # 4. Update SerialNumberRegistrationStatus
        if snr_count > 0:
            print(f"4. Updating SerialNumberRegistrationStatus...")
            cursor.execute("""
                UPDATE SerialNumberRegistrationStatus
                SET Boat_SerialNo = %s
                WHERE Boat_SerialNo = %s
            """, (NEW_SERIAL, OLD_SERIAL))
            print(f"   ✅ Updated {cursor.rowcount} rows")
            print()
        else:
            print("4. Skipping SerialNumberRegistrationStatus (no rows)")
            print()

        # Commit changes
        conn.commit()

        print("="*80)
        print("✅ SUCCESS")
        print("="*80)
        print()
        print("Next steps:")
        print(f"1. Re-import to populate BoatOptions22:")
        print(f"   python3 import_boatoptions_production.py")
        print()
        print(f"2. Verify in application:")
        print(f"   - Boat will now appear as {NEW_SERIAL}")
        print(f"   - Should load from BoatOptions22 (not 99_04)")
        print()

    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        import traceback
        traceback.print_exc()
        return 1
    finally:
        cursor.close()
        conn.close()

    return 0

if __name__ == '__main__':
    exit(main())

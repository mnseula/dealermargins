#!/usr/bin/env python3
"""
Remove One Boat from SerialNumberMaster/SerialNumberRegistrationStatus

Usage:
    python3 remove_one_boat.py <hull_number> [--confirm]

Example:
    python3 remove_one_boat.py ETWINVTEST0126
    python3 remove_one_boat.py ETWINVTEST0126 --confirm

Without --confirm, shows what would be deleted (dry run)
With --confirm, actually deletes the boat

Author: Claude Code
Date: 2026-02-10
"""

import mysql.connector
import sys

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'warrantyparts',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD'
}

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 remove_one_boat.py <hull_number> [--confirm]")
        print("Example: python3 remove_one_boat.py ETWINVTEST0126 --confirm")
        return 1

    hull_number = sys.argv[1]
    confirm = '--confirm' in sys.argv

    print("="*80)
    print("REMOVE BOAT FROM REGISTRATION")
    print("="*80)
    print(f"Hull Number: {hull_number}")
    if confirm:
        print("⚠️  DELETION MODE - Will actually delete!")
    else:
        print("DRY RUN MODE - Showing what would be deleted")
        print("Run with --confirm to actually delete")
    print("="*80)
    print()

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        # Check SerialNumberMaster
        cursor.execute("""
            SELECT *
            FROM SerialNumberMaster
            WHERE Boat_SerialNo = %s
        """, (hull_number,))

        master = cursor.fetchone()

        # Check SerialNumberRegistrationStatus
        cursor.execute("""
            SELECT *
            FROM SerialNumberRegistrationStatus
            WHERE Boat_SerialNo = %s
        """, (hull_number,))

        status = cursor.fetchone()

        if not master and not status:
            print(f"❌ Boat {hull_number} NOT found in SerialNumberMaster or SerialNumberRegistrationStatus")
            return 1

        print("Found boat:")
        print()

        if master:
            print("SerialNumberMaster:")
            for key, val in master.items():
                if val is not None:
                    print(f"  {key}: {val}")
            print()

        if status:
            print("SerialNumberRegistrationStatus:")
            for key, val in status.items():
                if val is not None:
                    print(f"  {key}: {val}")
            print()

        if not confirm:
            print("="*80)
            print("DRY RUN - No changes made")
            print("="*80)
            print()
            print("To actually delete this boat, run:")
            print(f"  python3 remove_one_boat.py {hull_number} --confirm")
            return 0

        # Actually delete
        print("="*80)
        print(f"⚠️  DELETING boat {hull_number}")
        print("="*80)
        print()

        # Delete from SerialNumberRegistrationStatus first (if exists)
        if status:
            cursor.execute("""
                DELETE FROM SerialNumberRegistrationStatus
                WHERE Boat_SerialNo = %s
            """, (hull_number,))
            print(f"✅ Deleted from SerialNumberRegistrationStatus ({cursor.rowcount} row)")

        # Delete from SerialNumberMaster
        if master:
            cursor.execute("""
                DELETE FROM SerialNumberMaster
                WHERE Boat_SerialNo = %s
            """, (hull_number,))
            print(f"✅ Deleted from SerialNumberMaster ({cursor.rowcount} row)")

        conn.commit()

        print()
        print("="*80)
        print("✅ DELETION COMPLETE")
        print("="*80)
        print(f"Boat {hull_number} removed successfully")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        if 'conn' in locals():
            conn.rollback()
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == '__main__':
    exit(main())

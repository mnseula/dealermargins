#!/usr/bin/env python3
"""
Remove Boats from Test Dealer

Removes boats from dealer 50 (PONTOON BOAT, LLC) - the test dealer.
Shows what will be removed before deleting.

Usage:
    python3 remove_dealer_boats.py [--confirm]

Without --confirm, shows what would be deleted (dry run)
With --confirm, actually deletes the boats

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
    confirm = '--confirm' in sys.argv
    dealer_id = 50  # PONTOON BOAT, LLC (test dealer)

    print("="*80)
    print("REMOVE BOATS FROM TEST DEALER")
    print("="*80)
    print(f"Dealer ID: {dealer_id} (PONTOON BOAT, LLC)")
    if confirm:
        print("⚠️  DELETION MODE - Will actually delete boats!")
    else:
        print("DRY RUN MODE - Showing what would be deleted")
        print("Run with --confirm to actually delete")
    print("="*80)
    print()

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        # Get boats for this dealer
        cursor.execute("""
            SELECT
                sm.Boat_SerialNo,
                sm.BoatModel,
                sm.InvoiceNo,
                sm.InvoiceDate,
                srs.Registered,
                srs.Active
            FROM SerialNumberMaster sm
            LEFT JOIN SerialNumberRegistrationStatus srs
                ON sm.Boat_SerialNo = srs.Boat_SerialNo
            WHERE sm.DealerID = %s
            ORDER BY sm.Boat_SerialNo
        """, (dealer_id,))

        boats = cursor.fetchall()

        if not boats:
            print(f"✅ No boats found for dealer {dealer_id}")
            print("Nothing to delete.")
            return 0

        print(f"Found {len(boats)} boat(s) registered to dealer {dealer_id}:")
        print()

        for boat in boats:
            print(f"  Hull: {boat['Boat_SerialNo']}")
            print(f"    Model: {boat['BoatModel']}")
            print(f"    Invoice: {boat['InvoiceNo']}")
            print(f"    Invoice Date: {boat['InvoiceDate']}")
            print(f"    Registered: {boat['Registered']}")
            print(f"    Active: {boat['Active']}")
            print()

        if not confirm:
            print("="*80)
            print("DRY RUN - No changes made")
            print("="*80)
            print()
            print("To actually delete these boats, run:")
            print("  python3 remove_dealer_boats.py --confirm")
            return 0

        # Confirm deletion
        print("="*80)
        print(f"⚠️  WARNING: About to DELETE {len(boats)} boat(s)")
        print("="*80)
        print()

        # Delete from SerialNumberRegistrationStatus first (foreign key constraint)
        hull_numbers = [boat['Boat_SerialNo'] for boat in boats]

        if hull_numbers:
            placeholders = ', '.join(['%s'] * len(hull_numbers))

            # Delete from SerialNumberRegistrationStatus
            cursor.execute(f"""
                DELETE FROM SerialNumberRegistrationStatus
                WHERE Boat_SerialNo IN ({placeholders})
            """, hull_numbers)

            srs_deleted = cursor.rowcount
            print(f"✅ Deleted {srs_deleted} row(s) from SerialNumberRegistrationStatus")

            # Delete from SerialNumberMaster
            cursor.execute(f"""
                DELETE FROM SerialNumberMaster
                WHERE DealerID = %s
                AND Boat_SerialNo IN ({placeholders})
            """, [dealer_id] + hull_numbers)

            sm_deleted = cursor.rowcount
            print(f"✅ Deleted {sm_deleted} row(s) from SerialNumberMaster")

            # Commit changes
            conn.commit()

            print()
            print("="*80)
            print("✅ DELETION COMPLETE")
            print("="*80)
            print(f"Removed {len(boats)} boat(s) from dealer {dealer_id}")

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

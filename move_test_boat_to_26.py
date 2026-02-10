#!/usr/bin/env python3
"""
Move ETWINVTEST0122 from BoatOptions22 to BoatOptions26

BoatOptions26 is the catchall for ALL CPQ boats regardless of year.
Move the test boat to the correct table.

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

SERIAL = 'ETWINVTEST0122'

def main():
    print("="*80)
    print("MOVE TEST BOAT TO BoatOptions26 (CPQ CATCHALL)")
    print("="*80)
    print(f"Serial: {SERIAL}")
    print(f"From: BoatOptions22")
    print(f"To: BoatOptions26")
    print("="*80)
    print()

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    try:
        # 1. Check source
        print("1. Checking BoatOptions22...")
        cursor.execute("SELECT COUNT(*) as cnt FROM BoatOptions22 WHERE BoatSerialNo = %s", (SERIAL,))
        source_count = cursor.fetchone()['cnt']
        print(f"   Found {source_count} rows")

        if source_count == 0:
            print("   ❌ Boat not found in BoatOptions22")
            return 1

        # 2. Check destination
        print()
        print("2. Checking BoatOptions26...")
        cursor.execute("SELECT COUNT(*) as cnt FROM BoatOptions26 WHERE BoatSerialNo = %s", (SERIAL,))
        dest_count = cursor.fetchone()['cnt']
        print(f"   Currently has {dest_count} rows")

        if dest_count > 0:
            print(f"   ⚠️  Boat already exists in BoatOptions26! Deleting old rows first...")
            cursor.execute("DELETE FROM BoatOptions26 WHERE BoatSerialNo = %s", (SERIAL,))
            print(f"   ✅ Deleted {cursor.rowcount} old rows")

        # 3. Get column list
        print()
        print("3. Getting BoatOptions26 schema...")
        cursor.execute("SHOW COLUMNS FROM BoatOptions26")
        columns = [row['Field'] for row in cursor.fetchall()]
        column_list = ', '.join(columns)
        print(f"   BoatOptions26 has {len(columns)} columns")

        # 4. Copy data
        print()
        print("4. Copying data to BoatOptions26...")
        insert_sql = f"""
            INSERT INTO BoatOptions26 ({column_list})
            SELECT {column_list}
            FROM BoatOptions22
            WHERE BoatSerialNo = '{SERIAL}'
        """
        cursor.execute(insert_sql)
        inserted = cursor.rowcount
        print(f"   ✅ Inserted {inserted} rows")

        # 5. Delete from source
        print()
        print("5. Deleting from BoatOptions22...")
        cursor.execute("DELETE FROM BoatOptions22 WHERE BoatSerialNo = %s", (SERIAL,))
        deleted = cursor.rowcount
        print(f"   ✅ Deleted {deleted} rows")

        # 6. Verify
        print()
        print("6. Verifying...")
        cursor.execute("SELECT COUNT(*) as cnt FROM BoatOptions26 WHERE BoatSerialNo = %s", (SERIAL,))
        final_count = cursor.fetchone()['cnt']

        cursor.execute("SELECT COUNT(*) as cnt FROM BoatOptions22 WHERE BoatSerialNo = %s", (SERIAL,))
        remaining = cursor.fetchone()['cnt']

        if final_count == source_count and remaining == 0:
            print(f"   ✅ SUCCESS:")
            print(f"      BoatOptions26: {final_count} rows")
            print(f"      BoatOptions22: {remaining} rows")
        else:
            print(f"   ⚠️  Unexpected counts:")
            print(f"      Expected {source_count} in BoatOptions26, got {final_count}")
            print(f"      Expected 0 in BoatOptions22, got {remaining}")

        # Commit
        conn.commit()

        print()
        print("="*80)
        print("✅ BOAT MOVED TO CPQ CATCHALL TABLE")
        print("="*80)
        print()
        print("Next steps:")
        print("1. Configure CPQ sStatements in EOS (CONFIGURE_CPQ_SSTATEMENTS.md)")
        print("2. Hard refresh browser")
        print("3. Load ETWINVTEST0122")
        print("4. LHS data should now load from BoatOptions26")
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

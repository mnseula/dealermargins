#!/usr/bin/env python3
"""
Manually Copy Test Boat from BoatOptions99_04 to BoatOptions22

Since we can't update ERP, manually copy the boat data with the new serial.

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
    print("MANUALLY COPY TEST BOAT TO BoatOptions22")
    print("="*80)
    print(f"Source: BoatOptions99_04 with serial {OLD_SERIAL}")
    print(f"Dest: BoatOptions22 with serial {NEW_SERIAL}")
    print("="*80)
    print()

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    try:
        # 1. Check source data
        print("1. Checking source data in BoatOptions99_04...")
        cursor.execute("""
            SELECT COUNT(*) as cnt
            FROM BoatOptions99_04
            WHERE BoatSerialNo = %s
        """, (OLD_SERIAL,))

        source_count = cursor.fetchone()['cnt']
        print(f"   Found {source_count} rows with {OLD_SERIAL}")

        if source_count == 0:
            print("   ❌ No source data found!")
            return 1
        print()

        # 2. Get column list from BoatOptions22
        print("2. Getting BoatOptions22 schema...")
        cursor.execute("SHOW COLUMNS FROM BoatOptions22")
        columns = [row['Field'] for row in cursor.fetchall()]
        print(f"   BoatOptions22 has {len(columns)} columns")
        print()

        # 3. Copy data with new serial
        print(f"3. Copying data to BoatOptions22...")
        column_list = ', '.join(columns)

        # Build INSERT ... SELECT with CASE to replace serial
        insert_sql = f"""
            INSERT INTO BoatOptions22 ({column_list})
            SELECT {', '.join([
                f"CASE WHEN '{col}' = 'BoatSerialNo' THEN %s ELSE {col} END" if col == 'BoatSerialNo'
                else col
                for col in columns
            ])}
            FROM BoatOptions99_04
            WHERE BoatSerialNo = %s
        """

        # Simpler approach: use REPLACE in SELECT
        select_columns = ', '.join([
            f"'{NEW_SERIAL}' AS BoatSerialNo" if col == 'BoatSerialNo'
            else col
            for col in columns
        ])

        insert_sql = f"""
            INSERT INTO BoatOptions22 ({column_list})
            SELECT {select_columns}
            FROM BoatOptions99_04
            WHERE BoatSerialNo = '{OLD_SERIAL}'
        """

        cursor.execute(insert_sql)
        inserted = cursor.rowcount
        print(f"   ✅ Inserted {inserted} rows into BoatOptions22")
        print()

        # 4. Delete from old table
        print("4. Deleting from BoatOptions99_04...")
        cursor.execute("DELETE FROM BoatOptions99_04 WHERE BoatSerialNo = %s", (OLD_SERIAL,))
        deleted = cursor.rowcount
        print(f"   ✅ Deleted {deleted} rows")
        print()

        # 5. Verify
        print("5. Verifying...")
        cursor.execute("SELECT COUNT(*) as cnt FROM BoatOptions22 WHERE BoatSerialNo = %s", (NEW_SERIAL,))
        final_count = cursor.fetchone()['cnt']

        if final_count == source_count:
            print(f"   ✅ SUCCESS: {final_count} rows in BoatOptions22")
        else:
            print(f"   ⚠️  Count mismatch: expected {source_count}, got {final_count}")
        print()

        # Commit
        conn.commit()

        print("="*80)
        print("✅ TEST BOAT READY")
        print("="*80)
        print()
        print("Next steps:")
        print("1. Hard refresh browser (Ctrl+Shift+R / Cmd+Shift+R)")
        print(f"2. Search for {NEW_SERIAL}")
        print("3. Boat should load from BoatOptions22")
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

#!/usr/bin/env python3
"""
Check Pre-2015 Boat Issue

Checks what's happening with ETWINVTEST01 / SO00936074

Usage:
    python3 check_pre2015_boat.py

Author: Claude Code
Date: 2026-02-10
"""

import pymssql
import mysql.connector

# MSSQL (ERP)
MSSQL_CONFIG = {
    'server': 'MPL1STGSQL086.POLARISSTAGE.COM',
    'database': 'CSISTG',
    'user': 'svccsimarine',
    'password': 'CNKmoFxEsXs0D9egZQXH',
    'timeout': 300,
    'login_timeout': 60
}

# MySQL
MYSQL_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'warrantyparts',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD'
}

def main():
    hull_no = 'ETWINVTEST01'
    order_no = 'SO00936074'

    print("="*80)
    print("PRE-2015 BOAT ISSUE CHECK")
    print("="*80)
    print(f"Hull Number: {hull_no}")
    print(f"Order Number: {order_no}")
    print("="*80)
    print()

    # Detect year from serial number
    year_suffix = hull_no[-2:]
    print(f"Serial number suffix: {year_suffix}")

    try:
        year_num = int(year_suffix)
        if year_num <= 50:
            full_year = 2000 + year_num
        else:
            full_year = 1900 + year_num
        print(f"Detected year: {full_year}")

        if full_year < 2015:
            print(f"⚠️  This is a PRE-2015 boat (year {full_year})")
            print("    The import script filters these out (line 208 & 306)")
            print()
    except:
        print("Could not parse year from serial number")
        print()

    # Check if boat exists in ERP
    print("Checking ERP system...")
    try:
        conn = pymssql.connect(**MSSQL_CONFIG)
        cursor = conn.cursor(as_dict=True)

        # Check for boat in coitem_mst
        cursor.execute("""
            SELECT TOP 5
                co_num,
                co_line,
                item,
                description,
                Uf_BENN_BoatSerialNumber,
                Uf_BENN_BoatModel,
                config_id,
                qty_ordered,
                qty_invoiced
            FROM coitem_mst
            WHERE co_num = %s
              AND site_ref = 'BENN'
        """, (order_no,))

        items = cursor.fetchall()

        if items:
            print(f"✅ Found {len(items)} line items in ERP for order {order_no}")
            print()
            for item in items:
                print(f"  Line {item['co_line']}: {item['item']} - {item['description']}")
                print(f"    Serial: {item['Uf_BENN_BoatSerialNumber']}")
                print(f"    Model: {item['Uf_BENN_BoatModel']}")
                print(f"    Config ID: {item['config_id']}")
                print(f"    Qty Ordered: {item['qty_ordered']}, Qty Invoiced: {item['qty_invoiced']}")
                print()
        else:
            print(f"❌ No items found in ERP for order {order_no}")
            print()

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ ERP error: {e}")
        print()

    # Check if boat exists in BoatOptions tables
    print("Checking MySQL BoatOptions tables...")
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor(dictionary=True)

        # Check all BoatOptions tables for this hull
        tables_to_check = [
            'BoatOptions99_04', 'BoatOptions05_07', 'BoatOptions08_10', 'BoatOptions11_14'
        ] + [f'BoatOptions{i:02d}' for i in range(15, 27)]

        found_in = []
        for table in tables_to_check:
            # Check if table exists
            cursor.execute("""
                SELECT COUNT(*)
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = 'warrantyparts'
                  AND TABLE_NAME = %s
            """, (table,))

            if cursor.fetchone()[0] == 0:
                continue

            # Check for boat
            cursor.execute(f"""
                SELECT COUNT(*) as cnt
                FROM {table}
                WHERE BoatSerialNo = %s
            """, (hull_no,))

            count = cursor.fetchone()['cnt']
            if count > 0:
                found_in.append((table, count))

        if found_in:
            print(f"✅ Boat found in MySQL:")
            for table, count in found_in:
                print(f"   {table}: {count} rows")
        else:
            print(f"❌ Boat NOT found in any BoatOptions table")

        print()

        # Check what table it SHOULD go to
        if full_year < 2015:
            if 1999 <= full_year <= 2004:
                target_table = 'BoatOptions99_04'
            elif 2005 <= full_year <= 2007:
                target_table = 'BoatOptions05_07'
            elif 2008 <= full_year <= 2010:
                target_table = 'BoatOptions08_10'
            elif 2011 <= full_year <= 2014:
                target_table = 'BoatOptions11_14'
            else:
                target_table = 'BoatOptionsBefore_05'

            print(f"Target table: {target_table}")

            # Check if target table has CPQ columns
            cursor.execute("""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = 'warrantyparts'
                  AND TABLE_NAME = %s
                  AND COLUMN_NAME IN ('ConfigID', 'CfgName', 'CfgValue', 'MSRP')
            """, (target_table,))

            cpq_cols = cursor.fetchall()
            if cpq_cols:
                print(f"✅ {target_table} has {len(cpq_cols)} CPQ columns")
            else:
                print(f"❌ {target_table} MISSING CPQ columns!")
                print("   This table needs to be updated with CPQ columns before importing CPQ boats")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ MySQL error: {e}")
        import traceback
        traceback.print_exc()

    print("="*80)

if __name__ == '__main__':
    main()

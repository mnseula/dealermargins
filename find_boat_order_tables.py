#!/usr/bin/env python3
"""
Find source tables in MSSQL that contain boat order/sales data
"""
import pymssql

MSSQL_CONFIG = {
    'server': 'MPL1STGSQL086.POLARISSTAGE.COM',
    'database': 'CSISTG',
    'user': 'svccsimarine',
    'password': 'CNKmoFxEsXs0D9egZQXH'
}

def main():
    print("="*80)
    print("FINDING BOAT ORDER/SALES SOURCE TABLES IN MSSQL")
    print("="*80)

    try:
        conn = pymssql.connect(**MSSQL_CONFIG)
        cursor = conn.cursor()
        print("✅ Connected to MSSQL\n")

        # 1. Search for tables with "serial" in the name
        print("="*80)
        print("TABLES WITH 'SERIAL' OR 'BOAT' IN NAME:")
        print("="*80)
        cursor.execute("""
            SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE
            FROM INFORMATION_SCHEMA.TABLES
            WHERE (TABLE_NAME LIKE '%serial%'
                   OR TABLE_NAME LIKE '%boat%'
                   OR TABLE_NAME LIKE '%order%'
                   OR TABLE_NAME LIKE '%coitem%')
              AND TABLE_TYPE IN ('BASE TABLE', 'VIEW')
            ORDER BY TABLE_NAME
        """)

        tables = cursor.fetchall()
        if tables:
            print(f"\n{'Schema':<20} {'Table Name':<50} {'Type':<15}")
            print("-"*85)
            for table in tables:
                print(f"{table[0]:<20} {table[1]:<50} {table[2]:<15}")
        else:
            print("  No tables found")

        # 2. Look at coitem_mst structure (order line items)
        print("\n" + "="*80)
        print("COITEM_MST COLUMNS (Customer Order Line Items):")
        print("="*80)
        cursor.execute("""
            SELECT
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'coitem_mst'
              AND TABLE_SCHEMA = 'dbo'
            ORDER BY ORDINAL_POSITION
        """)

        cols = cursor.fetchall()
        print(f"\n{'Column Name':<40} {'Type':<20} {'Length':<10} {'Nullable':<10}")
        print("-"*80)
        for col in cols:
            col_name = col[0]
            # Highlight important columns
            if any(x in col_name.lower() for x in ['serial', 'item', 'qty', 'price', 'co_num', 'line']):
                marker = ">>> "
            else:
                marker = "    "
            data_type = col[1]
            max_len = col[2] if col[2] else ''
            nullable = col[3]
            print(f"{marker}{col_name:<40} {data_type:<20} {str(max_len):<10} {nullable:<10}")

        # 3. Sample order data
        print("\n" + "="*80)
        print("SAMPLE ORDER LINE ITEMS (coitem_mst):")
        print("="*80)
        cursor.execute("""
            SELECT TOP 5
                coi.co_num,
                coi.co_line,
                coi.item,
                coi.qty_ordered,
                coi.price,
                itm.product_code,
                itm.description,
                itm.Uf_BENN_ProductCategory
            FROM coitem_mst coi
            JOIN item_mst itm ON coi.item = itm.item AND coi.site_ref = itm.site_ref
            WHERE coi.site_ref = 'BENN'
              AND itm.product_code = 'BOA'
            ORDER BY coi.co_num DESC
        """)

        print(f"\n{'CO#':<15} {'Line':<8} {'Item':<20} {'Qty':<8} {'Price':<12} {'ProdCode':<10} {'Description':<30}")
        print("-"*110)
        for row in cursor.fetchall():
            co_num = row[0] or ''
            line = row[1] or ''
            item = (row[2] or '')[:20]
            qty = row[3] or 0
            price = row[4] or 0
            prod = row[5] or ''
            desc = (row[6] or '')[:30]
            print(f"{co_num:<15} {line:<8} {item:<20} {qty:<8.2f} ${price:<11.2f} {prod:<10} {desc:<30}")

        # 4. Look for serial number fields
        print("\n" + "="*80)
        print("SEARCHING FOR SERIAL NUMBER FIELDS:")
        print("="*80)
        cursor.execute("""
            SELECT
                TABLE_NAME,
                COLUMN_NAME,
                DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'dbo'
              AND (COLUMN_NAME LIKE '%serial%' OR COLUMN_NAME LIKE '%ser_num%')
            ORDER BY TABLE_NAME, COLUMN_NAME
        """)

        serial_cols = cursor.fetchall()
        if serial_cols:
            print(f"\n{'Table Name':<50} {'Column Name':<40} {'Type':<20}")
            print("-"*110)
            for col in serial_cols:
                print(f"{col[0]:<50} {col[1]:<40} {col[2]:<20}")
        else:
            print("  No serial number columns found")

        # 5. Check serials_mst table
        print("\n" + "="*80)
        print("SERIALS_MST TABLE (if exists):")
        print("="*80)
        try:
            cursor.execute("""
                SELECT TOP 5
                    ser_num,
                    item,
                    site_ref,
                    ref_num,
                    ref_line
                FROM serials_mst
                WHERE site_ref = 'BENN'
                ORDER BY ser_num DESC
            """)

            print(f"\n{'Serial Number':<20} {'Item':<20} {'Site':<10} {'Ref#':<15} {'Line':<8}")
            print("-"*80)
            for row in cursor.fetchall():
                serial = row[0] or ''
                item = (row[1] or '')[:20]
                site = row[2] or ''
                ref = row[3] or ''
                line = row[4] or ''
                print(f"{serial:<20} {item:<20} {site:<10} {ref:<15} {line:<8}")
        except Exception as e:
            print(f"  Error: {e}")

        # 6. Find a real serial number for testing
        print("\n" + "="*80)
        print("FINDING REAL SERIAL NUMBER FOR TESTING:")
        print("="*80)
        cursor.execute("""
            SELECT TOP 5
                ser_num,
                item
            FROM serials_mst
            WHERE site_ref = 'BENN'
              AND ser_num LIKE 'ETWC%'
            ORDER BY ser_num DESC
        """)

        serials = cursor.fetchall()
        if serials:
            print(f"\n{'Serial Number':<20} {'Item':<30}")
            print("-"*50)
            for row in serials:
                print(f"{row[0]:<20} {row[1]:<30}")
        else:
            print("  No serials starting with ETWC found")

        cursor.close()
        conn.close()

        print("\n" + "="*80)
        print("INVESTIGATION COMPLETE")
        print("="*80)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

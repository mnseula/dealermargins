#!/usr/bin/env python3
"""
Investigate MSSQL Schema to Find MCTDesc and ItemMasterMCT Source Fields
"""
import pymssql

# MSSQL Configuration
MSSQL_CONFIG = {
    'server': 'MPL1STGSQL086.POLARISSTAGE.COM',
    'database': 'CSISTG',
    'user': 'svccsimarine',
    'password': 'CNKmoFxEsXs0D9egZQXH'
}

def main():
    print("="*80)
    print("INVESTIGATING MSSQL SCHEMA FOR MCT FIELDS")
    print("="*80)

    try:
        print("\nConnecting to MSSQL...")
        conn = pymssql.connect(**MSSQL_CONFIG)
        cursor = conn.cursor()
        print("✅ Connected")

        # 1. Get item_mst table schema
        print("\n" + "="*80)
        print("ITEM_MST TABLE COLUMNS:")
        print("="*80)
        cursor.execute("""
            SELECT
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'item_mst'
              AND TABLE_SCHEMA = 'dbo'
            ORDER BY ORDINAL_POSITION
        """)

        columns = cursor.fetchall()
        print(f"\n{'Column Name':<40} {'Type':<20} {'Length':<10} {'Nullable':<10}")
        print("-"*80)
        for col in columns:
            col_name = col[0]
            data_type = col[1]
            max_len = col[2] if col[2] else ''
            nullable = col[3]
            print(f"{col_name:<40} {data_type:<20} {str(max_len):<10} {nullable:<10}")

        # 2. Look for MCT-like fields
        print("\n" + "="*80)
        print("SEARCHING FOR MCT-RELATED FIELDS:")
        print("="*80)
        mct_fields = [col for col in columns if 'MCT' in col[0].upper() or 'PRODUCT' in col[0].upper() or 'CATEGORY' in col[0].upper()]
        if mct_fields:
            print("\nFound MCT/Product/Category related fields:")
            for col in mct_fields:
                print(f"  - {col[0]} ({col[1]})")
        else:
            print("  No MCT-related fields found in item_mst")

        # 3. Sample data from item_mst for a known item
        print("\n" + "="*80)
        print("SAMPLE DATA FROM ITEM_MST:")
        print("="*80)
        cursor.execute("""
            SELECT TOP 5
                item,
                description,
                product_code,
                Uf_BENN_Series
            FROM item_mst
            WHERE site_ref = 'BENN'
              AND item LIKE '90%'
            ORDER BY item
        """)

        print(f"\n{'Item':<20} {'Description':<40} {'ProdCode':<15} {'Series':<10}")
        print("-"*90)
        for row in cursor.fetchall():
            item = row[0] or ''
            desc = (row[1] or '')[:40]
            prod = row[2] or ''
            series = row[3] or ''
            print(f"{item:<20} {desc:<40} {prod:<15} {series:<10}")

        # 4. Check if there's a separate product code table
        print("\n" + "="*80)
        print("SEARCHING FOR PRODUCT CODE LOOKUP TABLES:")
        print("="*80)
        cursor.execute("""
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = 'dbo'
              AND (TABLE_NAME LIKE '%product%'
                   OR TABLE_NAME LIKE '%mct%'
                   OR TABLE_NAME LIKE '%category%')
            ORDER BY TABLE_NAME
        """)

        tables = cursor.fetchall()
        if tables:
            print("\nFound related tables:")
            for table in tables:
                print(f"  - {table[0]}")

                # Get row count
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                    count = cursor.fetchone()[0]
                    print(f"    Rows: {count:,}")
                except:
                    pass
        else:
            print("  No product/MCT/category tables found")

        # 5. Check coitem_mst for MCT fields
        print("\n" + "="*80)
        print("COITEM_MST TABLE COLUMNS (Order Line Items):")
        print("="*80)
        cursor.execute("""
            SELECT
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'coitem_mst'
              AND TABLE_SCHEMA = 'dbo'
              AND (COLUMN_NAME LIKE '%mct%' OR COLUMN_NAME LIKE '%product%' OR COLUMN_NAME LIKE '%category%')
            ORDER BY ORDINAL_POSITION
        """)

        coitem_cols = cursor.fetchall()
        if coitem_cols:
            print("\nFound MCT/Product related fields in coitem_mst:")
            for col in coitem_cols:
                print(f"  - {col[0]} ({col[1]})")
        else:
            print("  No MCT-related fields in coitem_mst")

        cursor.close()
        conn.close()

        print("\n" + "="*80)
        print("INVESTIGATION COMPLETE")
        print("="*80)

    except pymssql.Error as e:
        print(f"❌ MSSQL Error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    main()

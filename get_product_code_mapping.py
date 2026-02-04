#!/usr/bin/env python3
"""
Get Product Code Mapping and Sample BoatOptions25 Data
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
    print("PRODUCT CODE MAPPING AND BOATOPTIONS25 INVESTIGATION")
    print("="*80)

    try:
        conn = pymssql.connect(**MSSQL_CONFIG)
        cursor = conn.cursor()
        print("✅ Connected to MSSQL\n")

        # 1. Get unique product codes with descriptions
        print("="*80)
        print("PRODUCT CODES IN ITEM_MST:")
        print("="*80)
        cursor.execute("""
            SELECT DISTINCT
                product_code,
                COUNT(*) as item_count
            FROM item_mst
            WHERE site_ref = 'BENN'
              AND product_code IS NOT NULL
              AND product_code != ''
            GROUP BY product_code
            ORDER BY product_code
        """)

        print(f"\n{'Product Code':<15} {'Item Count':<15}")
        print("-"*30)
        for row in cursor.fetchall():
            print(f"{row[0]:<15} {row[1]:<15,}")

        # 2. Check if there's a product code master table
        print("\n" + "="*80)
        print("LOOKING FOR PRODUCT CODE MASTER TABLE:")
        print("="*80)

        # Check prodcode table
        cursor.execute("""
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_NAME LIKE '%prodcode%' OR TABLE_NAME LIKE '%prod_code%'
            ORDER BY TABLE_NAME
        """)
        tables = cursor.fetchall()
        if tables:
            print("\nFound prodcode tables:")
            for table in tables:
                print(f"  - {table[0]}")

                # Try to query it
                try:
                    cursor.execute(f"SELECT TOP 5 * FROM {table[0]}")
                    cols = [desc[0] for desc in cursor.description]
                    print(f"    Columns: {', '.join(cols)}")
                    rows = cursor.fetchall()
                    if rows:
                        print(f"    Sample rows: {len(rows)}")
                except Exception as e:
                    print(f"    Error querying: {e}")
        else:
            print("  No prodcode tables found")

        # 3. Sample items from each major product code
        print("\n" + "="*80)
        print("SAMPLE ITEMS BY PRODUCT CODE:")
        print("="*80)
        cursor.execute("""
            SELECT TOP 3
                product_code,
                item,
                description,
                Uf_BENN_ProductCategory
            FROM item_mst
            WHERE site_ref = 'BENN'
              AND product_code IN ('ACY', 'DIS', 'ENZ', 'VOD', 'DIC', 'DIF')
            ORDER BY product_code, item
        """)

        print(f"\n{'ProdCode':<10} {'Item':<20} {'Description':<40} {'BENN_Cat':<10}")
        print("-"*80)
        for row in cursor.fetchall():
            prod = row[0] or ''
            item = row[1] or ''
            desc = (row[2] or '')[:40]
            cat = row[3] or ''
            print(f"{prod:<10} {item:<20} {desc:<40} {cat:<10}")

        # 4. Check warrantyparts database for BoatOptions25
        print("\n" + "="*80)
        print("CHECKING WARRANTYPARTS.BOATOPTIONS25:")
        print("="*80)

        cursor.execute("""
            SELECT TOP 1 TABLE_CATALOG, TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE
            FROM warrantyparts.INFORMATION_SCHEMA.TABLES
            WHERE TABLE_NAME = 'BoatOptions25'
        """)
        table_info = cursor.fetchone()
        if table_info:
            print(f"  Found: {table_info[0]}.{table_info[1]}.{table_info[2]} ({table_info[3]})")

            # Get columns
            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
                FROM warrantyparts.INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'BoatOptions25'
                  AND TABLE_SCHEMA = 'dbo'
                ORDER BY ORDINAL_POSITION
            """)

            print(f"\n  Columns in BoatOptions25:")
            for col in cursor.fetchall():
                col_name = col[0]
                if 'MCT' in col_name.upper() or 'PRODUCT' in col_name.upper() or 'CATEGORY' in col_name.upper():
                    print(f"    *** {col_name} ({col[1]}) ***")
                else:
                    print(f"    {col_name} ({col[1]})")
        else:
            print("  BoatOptions25 not found!")

        # 5. Sample actual data from BoatOptions25
        print("\n" + "="*80)
        print("SAMPLE DATA FROM BOATOPTIONS25:")
        print("="*80)
        cursor.execute("""
            SELECT TOP 10
                ItemNo,
                ItemDesc1,
                MCTDesc,
                ItemMasterMCT,
                ItemMasterProdCat,
                ExtSalesAmount
            FROM warrantyparts.BoatOptions25
            WHERE BoatSerialNo = 'ETWC4149F425'
            ORDER BY LineNo
        """)

        print(f"\n{'ItemNo':<15} {'MCTDesc':<20} {'MCT':<8} {'Cat':<8} {'Amount':<12} {'Description':<30}")
        print("-"*100)
        for row in cursor.fetchall():
            item = (row[0] or '')[:15]
            desc = (row[1] or '')[:30]
            mct_desc = (row[2] or '')[:20]
            mct = row[3] or ''
            cat = row[4] or ''
            amt = f"${row[5]:,.2f}" if row[5] else ''
            print(f"{item:<15} {mct_desc:<20} {mct:<8} {cat:<8} {amt:<12} {desc:<30}")

        # 6. Try to get the view definition
        print("\n" + "="*80)
        print("BOATOPTIONS25 VIEW DEFINITION:")
        print("="*80)
        cursor.execute("""
            SELECT OBJECT_DEFINITION(OBJECT_ID('warrantyparts.dbo.BoatOptions25'))
        """)
        view_def = cursor.fetchone()
        if view_def and view_def[0]:
            print("\n" + view_def[0][:2000])  # First 2000 chars
            if len(view_def[0]) > 2000:
                print(f"\n... (truncated, total length: {len(view_def[0])} chars)")
        else:
            print("  Could not retrieve view definition")

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

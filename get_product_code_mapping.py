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

        # 4. Get ALL product code descriptions
        print("\n" + "="*80)
        print("PRODUCT CODE DESCRIPTIONS:")
        print("="*80)

        cursor.execute("""
            SELECT
                product_code,
                description
            FROM prodcode_mst
            WHERE site_ref = 'BENN'
            ORDER BY product_code
        """)

        print(f"\n{'Code':<10} {'Description':<50}")
        print("-"*60)
        for row in cursor.fetchall():
            code = row[0] or ''
            desc = (row[1] or '')[:50]
            print(f"{code:<10} {desc:<50}")

        # 5. Check which database has BoatOptions25
        print("\n" + "="*80)
        print("SEARCHING FOR BOATOPTIONS25 TABLE:")
        print("="*80)

        # First, list all databases
        cursor.execute("SELECT name FROM sys.databases ORDER BY name")
        databases = [row[0] for row in cursor.fetchall()]
        print(f"\n  Available databases: {', '.join(databases)}")

        # Search for BoatOptions25 in each database
        for db in databases:
            try:
                cursor.execute(f"""
                    SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE
                    FROM {db}.INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_NAME LIKE '%BoatOptions%'
                """)
                tables = cursor.fetchall()
                if tables:
                    print(f"\n  Found in {db}:")
                    for table in tables:
                        print(f"    {table[0]}.{table[1]} ({table[2]})")
            except:
                pass  # Skip databases we can't access

        # 6. Find BoatOptions25 in CSISTG schemas
        print("\n" + "="*80)
        print("SEARCHING FOR BOATOPTIONS25 IN CSISTG:")
        print("="*80)
        cursor.execute("""
            SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE
            FROM CSISTG.INFORMATION_SCHEMA.TABLES
            WHERE TABLE_NAME LIKE '%BoatOptions%'
        """)
        tables = cursor.fetchall()
        if tables:
            print("\n  Found tables:")
            for table in tables:
                print(f"    {table[0]}.{table[1]} ({table[2]})")

        # 7. Sample actual data from BoatOptions25
        print("\n" + "="*80)
        print("SAMPLE DATA FROM BOATOPTIONS25:")
        print("="*80)

        # Try different schema names
        for schema in ['dbo', 'warrantyparts']:
            try:
                cursor.execute(f"""
                    SELECT TOP 10
                        ItemNo,
                        ItemDesc1,
                        MCTDesc,
                        ItemMasterMCT,
                        ItemMasterProdCat,
                        ExtSalesAmount
                    FROM CSISTG.{schema}.BoatOptions25
                    WHERE BoatSerialNo = 'ETWC4149F425'
                    ORDER BY [LineNo]
                """)

                rows = cursor.fetchall()
                if rows:
                    print(f"\n  Found data in CSISTG.{schema}.BoatOptions25:")
                    print(f"\n  {'ItemNo':<15} {'MCTDesc':<20} {'MCT':<8} {'Cat':<8} {'Amount':<12} {'Description':<30}")
                    print("  " + "-"*100)
                    for row in rows:
                        item = (row[0] or '')[:15]
                        desc = (row[1] or '')[:30]
                        mct_desc = (row[2] or '')[:20]
                        mct = row[3] or ''
                        cat = row[4] or ''
                        amt = f"${row[5]:,.2f}" if row[5] else ''
                        print(f"  {item:<15} {mct_desc:<20} {mct:<8} {cat:<8} {amt:<12} {desc:<30}")

                    # 8. Try to get the view definition
                    print("\n" + "="*80)
                    print(f"BOATOPTIONS25 VIEW DEFINITION (CSISTG.{schema}):")
                    print("="*80)
                    cursor.execute(f"""
                        SELECT OBJECT_DEFINITION(OBJECT_ID('CSISTG.{schema}.BoatOptions25'))
                    """)
                    view_def = cursor.fetchone()
                    if view_def and view_def[0]:
                        print("\n" + view_def[0])
                    else:
                        print("  Could not retrieve view definition")
                    break
            except Exception as e:
                print(f"  CSISTG.{schema} - {e}")

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

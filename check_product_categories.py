#!/usr/bin/env python3
"""
Check Uf_BENN_ProductCategory values to understand configuration vs physical items
"""
import pymssql

MSSQL_CONFIG = {
    'server': 'MPL1STGSQL086.POLARISSTAGE.COM',
    'database': 'CSISTG',
    'user': 'svccsimarine',
    'password': 'CNKmoFxEsXs0D9egZQXH'
}

def main():
    print("="*140)
    print("CHECKING PRODUCT CATEGORY FIELD VALUES")
    print("="*140)

    try:
        conn = pymssql.connect(**MSSQL_CONFIG)
        cursor = conn.cursor()
        print("✅ Connected to MSSQL\n")

        # Get all items from SO00927911 with product category field
        print("="*140)
        print("ALL ITEMS FROM SO00927911 WITH PRODUCT CATEGORY FIELD:")
        print("="*140)
        cursor.execute("""
            SELECT
                coi.co_line,
                coi.item,
                itm.description,
                itm.product_code,
                pc.description as product_code_desc,
                itm.Uf_BENN_ProductCategory,
                coi.qty_ordered,
                coi.price,
                coi.price * coi.qty_ordered as ext_amount
            FROM coitem_mst coi
            JOIN item_mst itm ON coi.item = itm.item AND coi.site_ref = itm.site_ref
            LEFT JOIN prodcode_mst pc ON itm.product_code = pc.product_code AND itm.site_ref = pc.site_ref
            WHERE coi.co_num = 'SO00927911'
              AND coi.site_ref = 'BENN'
            ORDER BY coi.co_line
        """)

        items = cursor.fetchall()
        if items:
            print(f"\n{'Line':<6} {'Item':<20} {'ProdCode':<8} {'Prod Desc':<30} {'Cat':<6} {'Qty':<8} {'Price':<12} {'Ext$':<12} {'Item Description':<40}")
            print("-"*140)
            for row in items:
                line = row[0] or ''
                item = (row[1] or '')[:20]
                item_desc = (row[2] or '')[:40]
                prod_code = row[3] or ''
                prod_desc = (row[4] or '')[:30]
                cat = row[5] or ''
                qty = row[6] or 0
                price = row[7] or 0
                ext = row[8] or 0

                # Highlight potential config items
                if prod_code in ['DIS', 'CAS', 'DIW', 'LOY', 'VOD', 'GRO', 'LAB']:
                    marker = ">>> "
                elif cat == '111':
                    marker = "*** "
                elif ext == 0:
                    marker = "$$$ "
                else:
                    marker = "    "

                print(f"{marker}{line:<6} {item:<20} {prod_code:<8} {prod_desc:<30} {cat:<6} {qty:<8.2f} ${price:<11.2f} ${ext:<11.2f} {item_desc:<40}")

            print("\n  Legend:")
            print("  >>> = Known config item (DIS, CAS, DIW, LOY, VOD, GRO, LAB)")
            print("  *** = ProductCategory = '111' (potential config item)")
            print("  $$$ = ExtAmount = $0 (potential config item)")

        # Group by ProductCategory
        print("\n" + "="*140)
        print("ITEMS GROUPED BY PRODUCT CATEGORY:")
        print("="*140)
        cursor.execute("""
            SELECT
                itm.Uf_BENN_ProductCategory,
                itm.product_code,
                pc.description as product_code_desc,
                COUNT(*) as item_count,
                SUM(CASE WHEN coi.price * coi.qty_ordered = 0 THEN 1 ELSE 0 END) as zero_dollar_count,
                MIN(itm.item) as sample_item,
                MIN(itm.description) as sample_desc
            FROM coitem_mst coi
            JOIN item_mst itm ON coi.item = itm.item AND coi.site_ref = itm.site_ref
            LEFT JOIN prodcode_mst pc ON itm.product_code = pc.product_code AND itm.site_ref = pc.site_ref
            WHERE coi.co_num = 'SO00927911'
              AND coi.site_ref = 'BENN'
            GROUP BY itm.Uf_BENN_ProductCategory, itm.product_code, pc.description
            ORDER BY itm.Uf_BENN_ProductCategory, itm.product_code
        """)

        groups = cursor.fetchall()
        if groups:
            print(f"\n{'Category':<12} {'ProdCode':<10} {'Prod Desc':<30} {'Count':<8} {'$0 Count':<10} {'Sample Item':<20} {'Sample Description':<40}")
            print("-"*140)
            for row in groups:
                cat = row[0] or ''
                prod = row[1] or ''
                prod_desc = (row[2] or '')[:30]
                count = row[3] or 0
                zero_count = row[4] or 0
                sample_item = (row[5] or '')[:20]
                sample_desc = (row[6] or '')[:40]

                marker = ">>> " if cat == '111' else "    "
                print(f"{marker}{cat:<12} {prod:<10} {prod_desc:<30} {count:<8} {zero_count:<10} {sample_item:<20} {sample_desc:<40}")

        # Check what all category codes mean
        print("\n" + "="*140)
        print("ALL UNIQUE PRODUCT CATEGORY CODES IN ITEM_MST:")
        print("="*140)
        cursor.execute("""
            SELECT
                Uf_BENN_ProductCategory,
                COUNT(*) as item_count,
                MIN(product_code) as sample_prod_code,
                MIN(item) as sample_item,
                MIN(description) as sample_description
            FROM item_mst
            WHERE site_ref = 'BENN'
              AND Uf_BENN_ProductCategory IS NOT NULL
              AND Uf_BENN_ProductCategory != ''
            GROUP BY Uf_BENN_ProductCategory
            ORDER BY Uf_BENN_ProductCategory
        """)

        cats = cursor.fetchall()
        if cats:
            print(f"\n{'Category':<12} {'Count':<10} {'Sample ProdCode':<15} {'Sample Item':<20} {'Sample Description':<40}")
            print("-"*100)
            for row in cats:
                cat = row[0] or ''
                count = row[1] or 0
                prod = row[2] or ''
                item = (row[3] or '')[:20]
                desc = (row[4] or '')[:40]
                print(f"{cat:<12} {count:<10,} {prod:<15} {item:<20} {desc:<40}")

        cursor.close()
        conn.close()

        print("\n" + "="*140)
        print("QUERY COMPLETE")
        print("="*140)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

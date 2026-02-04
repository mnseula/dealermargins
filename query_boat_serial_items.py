#!/usr/bin/env python3
"""
Query all items for a boat serial number from MSSQL
Shows physical items vs configuration items
"""
import pymssql

MSSQL_CONFIG = {
    'server': 'MPL1STGSQL086.POLARISSTAGE.COM',
    'database': 'CSISTG',
    'user': 'svccsimarine',
    'password': 'CNKmoFxEsXs0D9egZQXH'
}

def main():
    print("="*120)
    print("QUERYING BOAT SERIAL NUMBER ITEMS FROM MSSQL")
    print("="*120)

    try:
        conn = pymssql.connect(**MSSQL_CONFIG)
        cursor = conn.cursor()
        print("✅ Connected to MSSQL\n")

        # 1. Find a recent boat serial number
        print("="*120)
        print("FINDING RECENT BOAT SERIAL NUMBERS:")
        print("="*120)
        cursor.execute("""
            SELECT TOP 10
                ser.ser_num,
                ser.item,
                itm.description,
                ser.ref_num as order_num
            FROM serial_mst ser
            JOIN item_mst itm ON ser.item = itm.item AND ser.site_ref = itm.site_ref
            WHERE ser.site_ref = 'BENN'
              AND ser.ser_num LIKE 'ETWC%'
              AND itm.product_code IN ('BOA', 'BOI')
            ORDER BY ser.RecordDate DESC
        """)

        serials = cursor.fetchall()
        if serials:
            print(f"\n{'Serial Number':<20} {'Item':<20} {'Description':<40} {'Order#':<15}")
            print("-"*120)
            for row in serials:
                serial = row[0] or ''
                item = (row[1] or '')[:20]
                desc = (row[2] or '')[:40]
                order = row[3] or ''
                print(f"{serial:<20} {item:<20} {desc:<40} {order:<15}")

            test_serial = serials[0][0]
            print(f"\n>>> Using test serial: {test_serial}")
        else:
            print("  No boat serial numbers found")
            test_serial = 'ETWC4149F425'  # Fallback
            print(f"\n>>> Using fallback serial: {test_serial}")

        # 2. Get ALL items for this serial number
        print("\n" + "="*120)
        print(f"ALL LINE ITEMS FOR BOAT SERIAL {test_serial}:")
        print("="*120)
        cursor.execute(f"""
            SELECT
                coi.co_num,
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
            WHERE coi.Uf_BENN_BoatSerialNumber = '{test_serial}'
              AND coi.site_ref = 'BENN'
            ORDER BY coi.co_line
        """)

        all_items = cursor.fetchall()
        if all_items:
            print(f"\n{'Line':<6} {'Item':<20} {'ProdCode':<8} {'MCT Description':<30} {'Cat':<6} {'Qty':<8} {'Price':<12} {'Ext$':<12} {'Item Description':<40}")
            print("-"*120)
            for row in all_items:
                order = row[0] or ''
                line = row[1] or ''
                item = (row[2] or '')[:20]
                item_desc = (row[3] or '')[:40]
                prod_code = row[4] or ''
                prod_desc = (row[5] or '')[:30]
                cat = row[6] or ''
                qty = row[7] or 0
                price = row[8] or 0
                ext = row[9] or 0
                print(f"{line:<6} {item:<20} {prod_code:<8} {prod_desc:<30} {cat:<6} {qty:<8.2f} ${price:<11.2f} ${ext:<11.2f} {item_desc:<40}")

            print(f"\n  Total items: {len(all_items)}")
        else:
            print(f"  No items found for serial {test_serial}")

        # 3. Group by product code to see categories
        print("\n" + "="*120)
        print("ITEMS GROUPED BY PRODUCT CODE:")
        print("="*120)
        cursor.execute(f"""
            SELECT
                itm.product_code,
                pc.description as product_code_desc,
                COUNT(*) as item_count,
                SUM(coi.price * coi.qty_ordered) as total_amount
            FROM coitem_mst coi
            JOIN item_mst itm ON coi.item = itm.item AND coi.site_ref = itm.site_ref
            LEFT JOIN prodcode_mst pc ON itm.product_code = pc.product_code AND itm.site_ref = pc.site_ref
            WHERE coi.Uf_BENN_BoatSerialNumber = '{test_serial}'
              AND coi.site_ref = 'BENN'
            GROUP BY itm.product_code, pc.description
            ORDER BY itm.product_code
        """)

        groups = cursor.fetchall()
        if groups:
            print(f"\n{'Product Code':<15} {'Description':<40} {'Count':<10} {'Total Amount':<15}")
            print("-"*80)
            for row in groups:
                prod_code = row[0] or ''
                prod_desc = (row[1] or '')[:40]
                count = row[2] or 0
                amount = row[3] or 0
                marker = ">>> " if prod_code in ['DIC', 'DIF', 'DIP', 'DIR', 'DIA', 'DIW', 'LOY', 'PRD', 'VOD', 'DIV', 'DIS', 'ENZ', 'FRE', 'WAR', 'GRO'] else "    "
                print(f"{marker}{prod_code:<15} {prod_desc:<40} {count:<10} ${amount:<14.2f}")

            print("\n  >>> = Configuration/Non-Physical Items (should be filtered out)")

        # 4. Show what SHOULD be included (physical items only)
        print("\n" + "="*120)
        print("PHYSICAL ITEMS ONLY (FILTERED):")
        print("="*120)
        cursor.execute(f"""
            SELECT
                coi.co_line,
                coi.item,
                itm.description,
                itm.product_code,
                pc.description as product_code_desc,
                coi.qty_ordered,
                coi.price * coi.qty_ordered as ext_amount
            FROM coitem_mst coi
            JOIN item_mst itm ON coi.item = itm.item AND coi.site_ref = itm.site_ref
            LEFT JOIN prodcode_mst pc ON itm.product_code = pc.product_code AND itm.site_ref = pc.site_ref
            WHERE coi.Uf_BENN_BoatSerialNumber = '{test_serial}'
              AND coi.site_ref = 'BENN'
              AND itm.product_code NOT IN (
                'DIC','DIF','DIP','DIR','DIA','DIW','LOY','PRD','VOD','DIV',
                'SHO','GRO','ZZZ','FRE','WAR','DLR','FRT',
                'A0','A0C','A0G','A0I','A0P','A0T','A0V','A1','A6','FUR',
                'DIS','ENZ','TAX','CAS','INT','LAB','MKT','ADV','DLM',
                'DMG','DSP','OTD','OTI','PGA','MKA','MIG','DON','REW','SNAP'
              )
            ORDER BY
              CASE pc.description
                WHEN 'Pontoon Boats OB' THEN 1
                WHEN 'Pontoon Boats IO' THEN 1
                WHEN 'Engine' THEN 2
                WHEN 'Engine IO' THEN 2
                WHEN 'Engine Accessory' THEN 2
                WHEN 'Prerig' THEN 3
                WHEN 'Accessory' THEN 4
                WHEN 'Trailer' THEN 5
                ELSE 6
              END,
              coi.co_line
        """)

        physical_items = cursor.fetchall()
        if physical_items:
            print(f"\n{'Line':<6} {'Item':<20} {'Product Code':<15} {'MCT Desc':<30} {'Qty':<8} {'Ext Amount':<12} {'Item Description':<40}")
            print("-"*120)
            total = 0
            for row in physical_items:
                line = row[0] or ''
                item = (row[1] or '')[:20]
                item_desc = (row[2] or '')[:40]
                prod_code = row[3] or ''
                prod_desc = (row[4] or '')[:30]
                qty = row[5] or 0
                ext = row[6] or 0
                total += ext
                print(f"{line:<6} {item:<20} {prod_code:<15} {prod_desc:<30} {qty:<8.2f} ${ext:<11.2f} {item_desc:<40}")

            print(f"\n  Total physical items: {len(physical_items)}")
            print(f"  Total amount: ${total:,.2f}")
        else:
            print(f"  No physical items found")

        cursor.close()
        conn.close()

        print("\n" + "="*120)
        print("QUERY COMPLETE")
        print("="*120)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

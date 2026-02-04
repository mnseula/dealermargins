#!/usr/bin/env python3
"""
Test filtering logic on SO00927911 to show what gets included vs excluded
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
    print("TESTING FILTER LOGIC ON SO00927911")
    print("="*140)

    try:
        conn = pymssql.connect(**MSSQL_CONFIG)
        cursor = conn.cursor()
        print("✅ Connected to MSSQL\n")

        # Get serial number for SO00927911
        cursor.execute("""
            SELECT ser_num, item
            FROM serial_mst
            WHERE ref_num = 'SO00927911'
              AND site_ref = 'BENN'
        """)
        serial_info = cursor.fetchone()
        if serial_info:
            serial = serial_info[0]
            boat_model = serial_info[1]
            print(f"Serial Number: {serial}")
            print(f"Boat Model: {boat_model}\n")
        else:
            print("⚠️  No serial found for SO00927911")
            return

        # Get ALL items (before filtering)
        print("="*140)
        print("ALL ITEMS (BEFORE FILTERING):")
        print("="*140)
        cursor.execute("""
            SELECT
                coi.co_line,
                coi.item,
                itm.description,
                itm.product_code,
                pc.description as prod_desc,
                itm.Uf_BENN_ProductCategory,
                coi.qty_ordered,
                coi.price * coi.qty_ordered as ext_amount
            FROM coitem_mst coi
            JOIN item_mst itm ON coi.item = itm.item AND coi.site_ref = itm.site_ref
            LEFT JOIN prodcode_mst pc ON itm.product_code = pc.product_code AND itm.site_ref = pc.site_ref
            WHERE coi.co_num = 'SO00927911'
              AND coi.site_ref = 'BENN'
            ORDER BY coi.co_line
        """)

        all_items = cursor.fetchall()
        print(f"\n{'Line':<6} {'Item':<20} {'ProdCode':<8} {'Category':<10} {'Ext Amount':<12} {'Status':<12} {'Description':<40}")
        print("-"*140)

        total_before = 0
        for row in all_items:
            line = row[0] or ''
            item = (row[1] or '')[:20]
            desc = (row[2] or '')[:40]
            prod_code = row[3] or ''
            prod_desc = (row[4] or '')[:30]
            cat = row[5] or ''
            qty = row[6] or 0
            ext = row[7] or 0
            total_before += ext

            # Determine if this will be filtered out
            status = "INCLUDE"
            reason = ""

            # Check all filter conditions
            if cat == '111':
                status = "EXCLUDE"
                reason = "BOM placeholder"
            elif prod_code in ['DIC','DIF','DIP','DIR','DIA','DIW','LOY','PRD','VOD','DIS','CAS',
                               'SHO','GRO','ZZZ','WAR','DLR','FRE','FRP','FRT',
                               'A0','A0C','A0G','A0I','A0P','A0T','A0V','A1','A6','FUR',
                               'TAX','INT','LAB','MKT','ADV','DLM',
                               'DMG','DSP','OTD','OTI','PGA','MKA','MIG','DON','REW','SNAP']:
                status = "EXCLUDE"
                reason = f"Product code: {prod_code}"
            elif cat.startswith('C') or cat.startswith('DI') or cat.startswith('W') or cat.startswith('N') or \
                 cat.startswith('PA') or cat.startswith('X'):
                status = "EXCLUDE"
                reason = f"Category: {cat}"
            elif cat in ['GRO','LAB','TAX','SHO','INT','PGA','VOI','S1','S3','S4','S5']:
                status = "EXCLUDE"
                reason = f"Special category: {cat}"
            elif prod_code == 'DIS' and item != 'NPPNPRICE16S':
                status = "EXCLUDE"
                reason = "DIS item (not allowed)"
            elif prod_code == 'ENZ' and 'VALUE' not in desc:
                status = "EXCLUDE"
                reason = "ENZ item (no VALUE)"
            elif cat in ['H1','H1I','H1P','H1V','H3U','H5','L0','S2','ASY'] and ext == 0:
                status = "EXCLUDE"
                reason = f"$0 config: {cat}"
            elif prod_code == 'ACY' and ext == 0:
                status = "EXCLUDE"
                reason = "ACY $0 item"

            marker = ">>>" if status == "EXCLUDE" else "   "
            amt_str = f"${ext:,.2f}" if ext else "$0.00"

            print(f"{marker}{line:<6} {item:<20} {prod_code:<8} {cat:<10} {amt_str:<12} {status:<12} {desc:<40}")
            if reason and status == "EXCLUDE":
                print(f"      └─ Reason: {reason}")

        print(f"\nTotal items BEFORE filtering: {len(all_items)}")
        print(f"Total amount BEFORE filtering: ${total_before:,.2f}")

        # Get FILTERED items (after applying all filters)
        print("\n" + "="*140)
        print("FILTERED ITEMS (AFTER FILTERING - WHAT WILL BE IN BOATOPTIONS25):")
        print("="*140)
        cursor.execute("""
            SELECT
                coi.co_line,
                coi.item,
                itm.description,
                itm.product_code,
                pc.description as prod_desc,
                itm.Uf_BENN_ProductCategory,
                coi.qty_ordered,
                coi.price * coi.qty_ordered as ext_amount
            FROM coitem_mst coi
            JOIN item_mst itm ON coi.item = itm.item AND coi.site_ref = itm.site_ref
            LEFT JOIN prodcode_mst pc ON itm.product_code = pc.product_code AND itm.site_ref = pc.site_ref
            WHERE coi.co_num = 'SO00927911'
              AND coi.site_ref = 'BENN'
              AND itm.Uf_BENN_ProductCategory <> '111'
              AND itm.product_code NOT IN (
                'DIC','DIF','DIP','DIR','DIA','DIW',
                'LOY','PRD','VOD','DIS','CAS',
                'SHO','GRO','ZZZ','WAR','DLR',
                'FRE','FRP','FRT',
                'A0','A0C','A0G','A0I','A0P','A0T','A0V','A1','A6','FUR',
                'TAX','INT','LAB','MKT','ADV','DLM',
                'DMG','DSP','OTD','OTI','PGA','MKA','MIG','DON','REW','SNAP'
              )
              AND itm.Uf_BENN_ProductCategory NOT LIKE 'C%'
              AND itm.Uf_BENN_ProductCategory NOT LIKE 'DI%'
              AND itm.Uf_BENN_ProductCategory NOT LIKE 'W%'
              AND itm.Uf_BENN_ProductCategory NOT LIKE 'N%'
              AND itm.Uf_BENN_ProductCategory NOT LIKE 'PA%'
              AND itm.Uf_BENN_ProductCategory NOT LIKE 'X%'
              AND itm.Uf_BENN_ProductCategory NOT IN ('GRO','LAB','TAX','SHO','INT','PGA','VOI','S1','S3','S4','S5')
              AND NOT (itm.product_code = 'DIS' AND coi.item <> 'NPPNPRICE16S')
              AND NOT (itm.product_code = 'ENZ' AND itm.description NOT LIKE '%VALUE%')
              AND NOT (
                itm.Uf_BENN_ProductCategory IN ('H1','H1I','H1P','H1V','H3U','H5','L0','S2','ASY')
                AND COALESCE(coi.price * coi.qty_ordered, 0) = 0
              )
              AND NOT (
                itm.product_code = 'ACY'
                AND COALESCE(coi.price * coi.qty_ordered, 0) = 0
              )
            ORDER BY
              CASE pc.description
                WHEN 'Pontoon Boats OB' THEN 1
                WHEN 'Pontoon Boats IO' THEN 1
                WHEN 'Engine' THEN 2
                WHEN 'Engine IO' THEN 2
                WHEN 'Engine Accessory' THEN 3
                WHEN 'Prerig' THEN 4
                WHEN 'Accessory' THEN 5
                ELSE 6
              END,
              coi.co_line
        """)

        filtered_items = cursor.fetchall()
        print(f"\n{'Line':<6} {'Item':<20} {'ProdCode':<8} {'Prod Desc':<30} {'Category':<10} {'Qty':<8} {'Ext Amount':<12} {'Description':<40}")
        print("-"*140)

        total_after = 0
        for row in filtered_items:
            line = row[0] or ''
            item = (row[1] or '')[:20]
            desc = (row[2] or '')[:40]
            prod_code = row[3] or ''
            prod_desc = (row[4] or '')[:30]
            cat = row[5] or ''
            qty = row[6] or 0
            ext = row[7] or 0
            total_after += ext

            amt_str = f"${ext:,.2f}" if ext else "$0.00"
            print(f"   {line:<6} {item:<20} {prod_code:<8} {prod_desc:<30} {cat:<10} {qty:<8.2f} {amt_str:<12} {desc:<40}")

        print(f"\nTotal items AFTER filtering: {len(filtered_items)}")
        print(f"Total amount AFTER filtering: ${total_after:,.2f}")

        # Summary
        print("\n" + "="*140)
        print("SUMMARY:")
        print("="*140)
        excluded_count = len(all_items) - len(filtered_items)
        excluded_amount = total_before - total_after
        print(f"Items EXCLUDED: {excluded_count} ({excluded_count*100//len(all_items)}%)")
        print(f"Amount EXCLUDED: ${excluded_amount:,.2f}")
        print(f"\nItems INCLUDED: {len(filtered_items)} ({len(filtered_items)*100//len(all_items)}%)")
        print(f"Amount INCLUDED: ${total_after:,.2f}")

        cursor.close()
        conn.close()

        print("\n" + "="*140)
        print("TEST COMPLETE")
        print("="*140)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

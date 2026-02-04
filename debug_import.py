#!/usr/bin/env python3
"""
Debug Import Script - Shows what data is extracted from MSSQL
"""
import pymssql
from datetime import datetime

MSSQL_CONFIG = {
    'server': 'MPL1STGSQL086.POLARISSTAGE.COM',
    'database': 'CSISTG',
    'user': 'svccsimarine',
    'password': 'CNKmoFxEsXs0D9egZQXH',
    'timeout': 300,
    'login_timeout': 60
}

# Same query as import script
MSSQL_QUERY = """
-- Part 1: Main order lines (e.g., boat itself, engine, accessories)
SELECT
    LEFT(coi.Uf_BENN_BoatWebOrderNumber, 30) AS [WebOrderNo],
    LEFT(im.Uf_BENN_Series, 5) AS [C_Series],
    coi.qty_invoiced AS [QuantitySold],
    LEFT(co.type, 1) AS [Orig_Ord_Type],
    LEFT(ser.ser_num, 12) AS [OptionSerialNo],
    pcm.description AS [MCTDesc],
    coi.co_line AS [LineSeqNo],
    coi.co_line AS [LineNo],
    LEFT(coi.item, 15) AS [ItemNo],
    NULL AS [ItemMasterProdCatDesc],
    LEFT(im.Uf_BENN_ProductCategory, 3) AS [ItemMasterProdCat],
    LEFT(im.Uf_BENN_MaterialCostType, 10) AS [ItemMasterMCT],
    LEFT(coi.description, 30) AS [ItemDesc1],
    LEFT(iim.inv_num, 30) AS [InvoiceNo],
    CASE
        WHEN ah.inv_date IS NOT NULL
        THEN CONVERT(INT, CONVERT(VARCHAR(8), ah.inv_date, 112))
        ELSE NULL
    END AS [InvoiceDate],
    CAST((coi.price * coi.qty_invoiced) AS DECIMAL(10,2)) AS [ExtSalesAmount],
    LEFT(coi.co_num, 30) AS [ERP_OrderNo],
    LEFT(coi.Uf_BENN_BoatSerialNumber, 15) AS [BoatSerialNo],
    LEFT(coi.Uf_BENN_BoatModel, 14) AS [BoatModelNo],
    ah.apply_to_inv_num AS [ApplyToNo],
    '' AS [ConfigID],
    '' AS [ValueText],
    co.order_date AS [order_date],
    co.external_confirmation_ref AS [external_confirmation_ref]
FROM [CSISTG].[dbo].[coitem_mst] coi
LEFT JOIN [CSISTG].[dbo].[inv_item_mst] iim
    ON coi.co_num = iim.co_num
    AND coi.co_line = iim.co_line
    AND coi.co_release = iim.co_release
    AND coi.site_ref = iim.site_ref
LEFT JOIN [CSISTG].[dbo].[arinv_mst] ah
    ON iim.inv_num = ah.inv_num
    AND iim.site_ref = ah.site_ref
LEFT JOIN [CSISTG].[dbo].[co_mst] co
    ON coi.co_num = co.co_num
    AND coi.site_ref = co.site_ref
LEFT JOIN [CSISTG].[dbo].[item_mst] im
    ON coi.item = im.item
    AND coi.site_ref = im.site_ref
LEFT JOIN [CSISTG].[dbo].[prodcode_mst] pcm
    ON im.Uf_BENN_MaterialCostType = pcm.product_code
    AND im.site_ref = pcm.site_ref
LEFT JOIN [CSISTG].[dbo].[serial_mst] ser
    ON coi.co_num = ser.ref_num
    AND coi.co_line = ser.ref_line
    AND coi.co_release = ser.ref_release
    AND coi.item = ser.item
    AND coi.site_ref = ser.site_ref
    AND ser.ref_type = 'O'
WHERE coi.site_ref = 'BENN'
    AND coi.Uf_BENN_BoatSerialNumber IS NOT NULL
    AND coi.Uf_BENN_BoatSerialNumber != ''
    AND iim.inv_num IS NOT NULL
    AND coi.qty_invoiced > 0
    AND co.order_date >= '2025-12-14'

UNION ALL

-- Part 2: Component "Description" attributes for invoiced, configured items (CPQ boats)
SELECT
    LEFT(coi.Uf_BENN_BoatWebOrderNumber, 30) AS [WebOrderNo],
    LEFT(im.Uf_BENN_Series, 5) AS [C_Series],
    coi.qty_invoiced AS [QuantitySold],
    LEFT(co.type, 1) AS [Orig_Ord_Type],
    LEFT(ser.ser_num, 12) AS [BoatModelNo],
    pcm.description AS [MCTDesc],
    coi.co_line AS [LineSeqNo],
    coi.co_line AS [LineNo],
    LEFT(ISNULL(ccm.comp_name, attr_detail.comp_id), 15) AS [ItemNo],
    NULL AS [ItemMasterProdCatDesc],
    LEFT(im.Uf_BENN_ProductCategory, 3) AS [ItemMasterProdCat],
    LEFT(im.Uf_BENN_MaterialCostType, 10) AS [ItemMasterMCT],
    LEFT(attr_detail.attr_value, 30) AS [ItemDesc1],
    LEFT(iim.inv_num, 30) AS [InvoiceNo],
    CASE
        WHEN ah.inv_date IS NOT NULL
        THEN CONVERT(INT, CONVERT(VARCHAR(8), ah.inv_date, 112))
        ELSE NULL
    END AS [InvoiceDate],
    CAST((coi.price * coi.qty_invoiced) AS DECIMAL(10,2)) AS [ExtSalesAmount],
    LEFT(coi.co_num, 30) AS [ERP_OrderNo],
    LEFT(coi.Uf_BENN_BoatSerialNumber, 15) AS [BoatSerialNo],
    LEFT(coi.Uf_BENN_BoatModel, 14) AS [OptionSerialNo],
    ah.apply_to_inv_num AS [ApplyToNo],
    LEFT(coi.config_id, 30) AS [ConfigID],
    LEFT(attr_detail.attr_value, 100) AS [ValueText],
    co.order_date AS [order_date],
    co.external_confirmation_ref AS [external_confirmation_ref]
FROM [CSISTG].[dbo].[coitem_mst] coi
INNER JOIN [CSISTG].[dbo].[cfg_attr_mst] attr_detail
    ON coi.config_id = attr_detail.config_id
    AND coi.site_ref = attr_detail.site_ref
    AND attr_detail.attr_name = 'Description'
    AND attr_detail.sl_field = 'jobmatl.description'
    AND attr_detail.attr_type = 'Schema'
    AND attr_detail.attr_value IS NOT NULL
LEFT JOIN [CSISTG].[dbo].[cfg_comp_mst] ccm
    ON attr_detail.config_id = ccm.config_id
    AND attr_detail.comp_id = ccm.comp_id
    AND attr_detail.site_ref = ccm.site_ref
LEFT JOIN [CSISTG].[dbo].[inv_item_mst] iim
    ON coi.co_num = iim.co_num
    AND coi.co_line = iim.co_line
    AND coi.co_release = iim.co_release
    AND coi.site_ref = iim.site_ref
LEFT JOIN [CSISTG].[dbo].[arinv_mst] ah
    ON iim.inv_num = ah.inv_num
    AND iim.site_ref = ah.site_ref
LEFT JOIN [CSISTG].[dbo].[co_mst] co
    ON coi.co_num = co.co_num
    AND coi.site_ref = co.site_ref
LEFT JOIN [CSISTG].[dbo].[item_mst] im
    ON coi.item = im.item
    AND coi.site_ref = im.site_ref
LEFT JOIN [CSISTG].[dbo].[prodcode_mst] pcm
    ON im.Uf_BENN_MaterialCostType = pcm.product_code
    AND im.site_ref = pcm.site_ref
LEFT JOIN [CSISTG].[dbo].[serial_mst] ser
    ON coi.co_num = ser.ref_num
    AND coi.co_line = ser.ref_line
    AND coi.co_release = ser.ref_release
    AND coi.item = ser.item
    AND coi.site_ref = ser.site_ref
    AND ser.ref_type = 'O'
WHERE coi.config_id IS NOT NULL
    AND coi.qty_invoiced = coi.qty_ordered
    AND coi.qty_invoiced > 0
    AND coi.site_ref = 'BENN'
    AND co.order_date >= '2025-12-14'

ORDER BY [ERP_OrderNo], [LineSeqNo]
"""

def main():
    print("="*120)
    print("DEBUG: MSSQL EXTRACTION")
    print("="*120)
    print(f"Query filters: order_date >= 2025-12-14, invoiced only")
    print("="*120)

    try:
        conn = pymssql.connect(**MSSQL_CONFIG)
        cursor = conn.cursor(as_dict=True)

        print("\nExecuting query...")
        cursor.execute(MSSQL_QUERY)
        rows = cursor.fetchall()

        print(f"\n✅ Extracted {len(rows)} rows from MSSQL\n")

        if len(rows) == 0:
            print("No data found!")
            return

        # Show all rows
        print("="*120)
        print("ALL EXTRACTED ROWS:")
        print("="*120)
        print(f"{'#':<4} {'ERP Order':<15} {'LineSeq':<8} {'Serial':<15} {'Item':<20} {'Description':<30} {'ConfigID':<15}")
        print("-"*120)

        for i, row in enumerate(rows, 1):
            erp = (row.get('ERP_OrderNo') or '')[:15]
            line = str(row.get('LineSeqNo') or '')
            serial = (row.get('BoatSerialNo') or '')[:15]
            item = (row.get('ItemNo') or '')[:20]
            desc = (row.get('ItemDesc1') or '')[:30]
            config = (row.get('ConfigID') or '')[:15]
            print(f"{i:<4} {erp:<15} {line:<8} {serial:<15} {item:<20} {desc:<30} {config:<15}")

        # Summary by order
        print("\n" + "="*120)
        print("SUMMARY BY ORDER:")
        print("="*120)

        orders = {}
        for row in rows:
            erp = row.get('ERP_OrderNo')
            if erp not in orders:
                orders[erp] = {
                    'lines': 0,
                    'with_serial': 0,
                    'with_config': 0,
                    'order_date': row.get('order_date'),
                    'ext_ref': row.get('external_confirmation_ref')
                }
            orders[erp]['lines'] += 1
            if row.get('BoatSerialNo'):
                orders[erp]['with_serial'] += 1
            if row.get('ConfigID'):
                orders[erp]['with_config'] += 1

        print(f"{'ERP Order':<15} {'Lines':<8} {'W/Serial':<10} {'W/Config':<10} {'Order Date':<12} {'Ext Ref':<15}")
        print("-"*90)
        for erp, data in sorted(orders.items()):
            order_dt = str(data['order_date']) if data['order_date'] else 'NULL'
            ext_ref = data['ext_ref'] or ''
            print(f"{erp:<15} {data['lines']:<8} {data['with_serial']:<10} {data['with_config']:<10} {order_dt:<12} {ext_ref:<15}")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

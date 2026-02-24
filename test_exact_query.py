#!/usr/bin/env python3
"""Test the EXACT SerialNumberMaster query"""

import pymssql

MSSQL_CONFIG = {
    'server': 'MPL1ITSSQL086.POLARISIND.COM',
    'database': 'CSIPRD',
    'user': 'svcSpecs01',
    'password': 'SD4nzr0CJ5oj38',
    'timeout': 300,
    'login_timeout': 60
}

conn = pymssql.connect(**MSSQL_CONFIG)
cursor = conn.cursor(as_dict=True)

ORDER_DATE_CUTOFF = '2021-01-01'
db = 'CSIPRD'

# Test with the exact query from the script, but just for one serial
query = f"""
SELECT DISTINCT
    COALESCE(NULLIF(coi.Uf_BENN_BoatSerialNumber, ''), ser.ser_num) AS BoatSerialNo,
    coi.item AS BoatItemNo,
    coi.description AS BoatDesc1,
    im.Uf_BENN_Series AS Series,
    coi.co_num AS ERP_OrderNo,
    LEFT(coi.Uf_BENN_BoatWebOrderNumber, 30) AS WebOrderNo,
    iim.inv_num AS InvoiceNo,
    CASE WHEN ah.inv_date IS NOT NULL 
        THEN CONVERT(INT, CONVERT(VARCHAR(8), ah.inv_date, 112)) 
        ELSE NULL 
    END AS InvoiceDate,
    co.cust_num AS DealerNumber,
    cust.name AS DealerName,
    cust.city AS DealerCity,
    cust.state AS DealerState,
    cust.zip AS DealerZip,
    cust.country AS DealerCountry,
    coi.Uf_BENN_BoatModel AS BoatModelNo,
    co.order_date AS OrderDate,
    co.Uf_BENN_ProductionNumber AS ProdNo,
    co.Uf_BENN_BenningtonOwned AS BenningtonOwned,
    coi.Uf_BENN_PannelColor AS PanelColor,
    coi.Uf_BENN_BaseVnyl AS BaseVinyl,
    coi.config_id AS ConfigId
FROM [{db}].[dbo].[coitem_mst] coi
LEFT JOIN [{db}].[dbo].[serial_mst] ser
    ON coi.co_num = ser.ref_num
    AND coi.co_line = ser.ref_line
    AND coi.co_release = ser.ref_release
    AND coi.item = ser.item
    AND coi.site_ref = ser.site_ref
    AND ser.ref_type = 'O'
INNER JOIN [{db}].[dbo].[inv_item_mst] iim
    ON coi.co_num = iim.co_num
    AND coi.co_line = iim.co_line
    AND coi.co_release = iim.co_release
    AND coi.site_ref = iim.site_ref
INNER JOIN [{db}].[dbo].[arinv_mst] ah
    ON iim.inv_num = ah.inv_num
    AND iim.site_ref = ah.site_ref
INNER JOIN [{db}].[dbo].[co_mst] co
    ON coi.co_num = co.co_num
    AND coi.site_ref = co.site_ref
LEFT JOIN [{db}].[dbo].[item_mst] im
    ON coi.item = im.item
    AND coi.site_ref = im.site_ref
LEFT JOIN [{db}].[dbo].[custaddr_mst] cust
    ON co.cust_num = cust.cust_num
    AND co.site_ref = cust.site_ref
    AND cust.cust_seq = 0
WHERE coi.site_ref = 'BENN'
    AND im.Uf_BENN_MaterialCostType IN ('BOA', 'BOI')
    AND (
        (coi.Uf_BENN_BoatSerialNumber IS NOT NULL AND coi.Uf_BENN_BoatSerialNumber != '')
        OR ser.ser_num IS NOT NULL
    )
    AND iim.inv_num IS NOT NULL
    AND coi.qty_invoiced > 0
    AND co.order_date >= '{ORDER_DATE_CUTOFF}'
    AND (coi.Uf_BENN_BoatSerialNumber = 'ETWS0887A626' OR ser.ser_num = 'ETWS0887A626')
ORDER BY BoatSerialNo
"""

print("="*120)
print("Running EXACT SerialNumberMaster query for ETWS0887A626...")
print("="*120)

cursor.execute(query)
rows = cursor.fetchall()

print(f"\nFound {len(rows)} rows")
print("-"*120)

if rows:
    for row in rows:
        print(f"\nBoatSerialNo: {row['BoatSerialNo']}")
        print(f"BoatItemNo: {row['BoatItemNo']}")
        print(f"BoatDesc1: {row['BoatDesc1']}")
        print(f"Series: {row['Series']}")
        print(f"ERP_OrderNo: {row['ERP_OrderNo']}")
        print(f"InvoiceNo: {row['InvoiceNo']}")
        print(f"InvoiceDate: {row['InvoiceDate']}")
        print(f"DealerName: {row['DealerName']}")
        print(f"BoatModelNo: {row['BoatModelNo']}")
        print(f"ConfigId: {row['ConfigId']}")
else:
    print("NO ROWS FOUND!")
    print("\nLet's test without the filters...")
    
    # Test without filters
    simple_query = f"""
    SELECT TOP 1
        COALESCE(NULLIF(coi.Uf_BENN_BoatSerialNumber, ''), ser.ser_num) AS BoatSerialNo,
        coi.item AS BoatItemNo,
        coi.co_num,
        coi.co_line,
        ser.ref_line,
        coi.item,
        ser.item as ser_item,
        iim.inv_num,
        ah.inv_num as ah_inv_num,
        im.Uf_BENN_MaterialCostType
    FROM [{db}].[dbo].[coitem_mst] coi
    LEFT JOIN [{db}].[dbo].[serial_mst] ser
        ON coi.co_num = ser.ref_num
        AND coi.co_line = ser.ref_line
        AND coi.co_release = ser.ref_release
        AND coi.item = ser.item
        AND coi.site_ref = ser.site_ref
        AND ser.ref_type = 'O'
    LEFT JOIN [{db}].[dbo].[inv_item_mst] iim
        ON coi.co_num = iim.co_num
        AND coi.co_line = iim.co_line
        AND coi.co_release = iim.co_release
        AND coi.site_ref = iim.site_ref
    LEFT JOIN [{db}].[dbo].[arinv_mst] ah
        ON iim.inv_num = ah.inv_num
        AND iim.site_ref = ah.site_ref
    LEFT JOIN [{db}].[dbo].[co_mst] co
        ON coi.co_num = co.co_num
        AND coi.site_ref = co.site_ref
    LEFT JOIN [{db}].[dbo].[item_mst] im
        ON coi.item = im.item
        AND coi.site_ref = im.site_ref
    WHERE coi.site_ref = 'BENN'
      AND ser.ser_num = 'ETWS0887A626'
    """
    
    cursor.execute(simple_query)
    row = cursor.fetchone()
    
    if row:
        print("\nFound with LEFT JOINs (no filters):")
        print(f"  BoatSerialNo: {row['BoatSerialNo']}")
        print(f"  co_num: {row['co_num']}")
        print(f"  co_line: {row['co_line']}")
        print(f"  ser_line: {row['ref_line']}")
        print(f"  coi.item: {row['BoatItemNo']}")
        print(f"  ser.item: {row['ser_item']}")
        print(f"  inv_num (iim): {row['inv_num']}")
        print(f"  inv_num (ah): {row['ah_inv_num']}")
        print(f"  MCT: {row['Uf_BENN_MaterialCostType']}")
    else:
        print("Not even with LEFT JOINs!")

cursor.close()
conn.close()
print("\n" + "="*120)

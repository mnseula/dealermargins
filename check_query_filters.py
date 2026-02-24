#!/usr/bin/env python3
"""Check if specific boats pass all query filters in CSIPRD"""

import pymssql

MSSQL_CONFIG = {
    'server': 'MPL1ITSSQL086.POLARISIND.COM',
    'database': 'CSIPRD',
    'user': 'svcSpecs01',
    'password': 'SD4nzr0CJ5oj38',
    'timeout': 300,
    'login_timeout': 60
}

boats_to_check = [
    'ETWS0887A626', 'ETWS0884A626', 'ETWS0889A626', 'ETWS0890A626', 'ETWS0872A626',
    'ETWS0796A626', 'ETWS0804A626', 'ETWS0925A626', 'ETWS1044A626', 'ETWS1047A626',
    'ETWS0838A626', 'ETWS0422L526', 'ETWS0121L526', 'ETWS9752K526', 'ETWS9874K526',
    'ETWS0927A626'
]

conn = pymssql.connect(**MSSQL_CONFIG)
cursor = conn.cursor(as_dict=True)

print("="*120)
print("Checking if boats pass all query filters (simulating the actual import query)")
print("="*120)
print(f"\n{'Serial':<20} {'Order No':<15} {'Has inv_item':<12} {'Has arinv':<10} {'Qty Inv':<10} {'Order Date':<12} {'In Query?'}")
print("-"*120)

for serial in boats_to_check:
    # Simplified version of the actual query join logic
    cursor.execute("""
    SELECT TOP 1
        coi.co_num,
        coi.qty_invoiced,
        co.order_date,
        iim.inv_num as iim_inv_num,
        ah.inv_num as ah_inv_num,
        ah.inv_date
    FROM [CSIPRD].[dbo].[coitem_mst] coi
    LEFT JOIN [CSIPRD].[dbo].[serial_mst] ser
        ON coi.co_num = ser.ref_num
        AND coi.co_line = ser.ref_line
        AND coi.co_release = ser.ref_release
        AND coi.item = ser.item
        AND coi.site_ref = ser.site_ref
        AND ser.ref_type = 'O'
    LEFT JOIN [CSIPRD].[dbo].[inv_item_mst] iim
        ON coi.co_num = iim.co_num
        AND coi.co_line = iim.co_line
        AND coi.co_release = iim.co_release
        AND coi.site_ref = iim.site_ref
    LEFT JOIN [CSIPRD].[dbo].[arinv_mst] ah
        ON iim.inv_num = ah.inv_num
        AND iim.site_ref = ah.site_ref
    INNER JOIN [CSIPRD].[dbo].[co_mst] co
        ON coi.co_num = co.co_num
        AND coi.site_ref = co.site_ref
    WHERE coi.site_ref = 'BENN'
        AND (coi.Uf_BENN_BoatSerialNumber = %s OR ser.ser_num = %s)
        AND co.order_date >= '2025-01-01'
    """, (serial, serial))
    
    row = cursor.fetchone()
    
    if row:
        has_inv_item = "YES" if row['iim_inv_num'] else "NO"
        has_arinv = "YES" if row['ah_inv_num'] else "NO"
        qty_inv = str(row['qty_invoiced']) if row['qty_invoiced'] else "0"
        order_date = row['order_date'].strftime('%Y-%m-%d') if row['order_date'] else 'NULL'
        
        # Check if would pass all filters
        would_pass = "YES" if (row['iim_inv_num'] and row['qty_invoiced'] and row['qty_invoiced'] > 0) else "NO"
        
        print(f"{serial:<20} {row['co_num']:<15} {has_inv_item:<12} {has_arinv:<10} {qty_inv:<10} {order_date:<12} {would_pass}")
    else:
        print(f"{serial:<20} {'NOT FOUND':<15} {'N/A':<12} {'N/A':<10} {'N/A':<10} {'N/A':<12} {'NO'}")

cursor.close()
conn.close()
print("\n" + "="*120)

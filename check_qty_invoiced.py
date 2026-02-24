#!/usr/bin/env python3
"""Check qty_invoiced values for the 16 boats"""

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

print("="*100)
print("Checking qty_invoiced for the 16 boats")
print("="*100)
print(f"\n{'Serial':<20} {'Order No':<15} {'Qty Invoiced':<15} {'Qty Ordered':<15} {'Qty Shipped':<15}")
print("-"*100)

for serial in boats_to_check:
    cursor.execute("""
    SELECT TOP 1 
        coi.co_num,
        coi.qty_invoiced,
        coi.qty_ordered,
        coi.qty_shipped
    FROM [CSIPRD].[dbo].[coitem_mst] coi
    LEFT JOIN [CSIPRD].[dbo].[serial_mst] ser
        ON coi.co_num = ser.ref_num
        AND coi.co_line = ser.ref_line
        AND coi.co_release = ser.ref_release
        AND coi.item = ser.item
        AND coi.site_ref = ser.site_ref
        AND ser.ref_type = 'O'
    WHERE coi.site_ref = 'BENN'
      AND (ser.ser_num = %s)
    """, (serial,))
    
    row = cursor.fetchone()
    
    if row:
        qty_inv = row['qty_invoiced'] if row['qty_invoiced'] is not None else 'NULL'
        qty_ord = row['qty_ordered'] if row['qty_ordered'] is not None else 'NULL'
        qty_ship = row['qty_shipped'] if row['qty_shipped'] is not None else 'NULL'
        
        # Check if any are negative
        neg_flag = ""
        if qty_inv != 'NULL' and qty_inv < 0:
            neg_flag = " ** NEGATIVE **"
        
        print(f"{serial:<20} {row['co_num']:<15} {qty_inv:<15} {qty_ord:<15} {qty_ship:<15}{neg_flag}")
    else:
        print(f"{serial:<20} {'NOT FOUND':<15}")

cursor.close()
conn.close()
print("\n" + "="*100)

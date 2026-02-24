#!/usr/bin/env python3
"""Check if specific boats exist in MSSQL production database"""

import pymssql

MSSQL_CONFIG = {
    'server': 'MPL1ITSSQL086.POLARISIND.COM',
    'database': 'CSIPRD',
    'user': 'svcSpecs01',
    'password': 'SD4nzr0CJ5oj38',
    'timeout': 300,
    'login_timeout': 60
}

# List of boats to check
boats_to_check = [
    'ETWS0887A626', 'ETWS0884A626', 'ETWS0889A626', 'ETWS0890A626', 'ETWS0872A626',
    'ETWS0796A626', 'ETWS0804A626', 'ETWS0925A626', 'ETWS1044A626', 'ETWS1047A626',
    'ETWS0838A626', 'ETWS0422L526', 'ETWS0121L526', 'ETWS9752K526', 'ETWS9874K526',
    'ETWS0927A626'
]

conn = pymssql.connect(**MSSQL_CONFIG)
cursor = conn.cursor(as_dict=True)

print("="*100)
print("Checking CSIPRD for specific boats")
print("="*100)
print(f"\n{'Serial Number':<20} {'Status':<15} {'Order No':<15} {'Has Invoice':<12} {'Qty Invoiced':<12}")
print("-"*100)

for serial in boats_to_check:
    # Check if boat exists at all
    cursor.execute("""
    SELECT TOP 1 
        coi.co_num,
        coi.Uf_BENN_BoatSerialNumber,
        iim.inv_num,
        coi.qty_invoiced,
        ah.inv_date
    FROM [CSIPRD].[dbo].[coitem_mst] coi
    LEFT JOIN [CSIPRD].[dbo].[serial_mst] ser
        ON coi.co_num = ser.ref_num
        AND coi.co_line = ser.ref_line
        AND ser.ref_type = 'O'
    LEFT JOIN [CSIPRD].[dbo].[inv_item_mst] iim
        ON coi.co_num = iim.co_num
        AND coi.co_line = iim.co_line
    LEFT JOIN [CSIPRD].[dbo].[arinv_mst] ah
        ON iim.inv_num = ah.inv_num
    WHERE coi.site_ref = 'BENN'
        AND (coi.Uf_BENN_BoatSerialNumber = %s OR ser.ser_num = %s)
    """, (serial, serial))
    
    row = cursor.fetchone()
    
    if row:
        status = "EXISTS"
        has_inv = "YES" if row['inv_num'] else "NO"
        qty_inv = str(row['qty_invoiced']) if row['qty_invoiced'] else "0"
        print(f"{serial:<20} {status:<15} {row['co_num'] or 'N/A':<15} {has_inv:<12} {qty_inv:<12}")
    else:
        print(f"{serial:<20} {'NOT FOUND':<15} {'N/A':<15} {'N/A':<12} {'N/A':<12}")

cursor.close()
conn.close()
print("\n" + "="*100)

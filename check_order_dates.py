#!/usr/bin/env python3
"""Check order dates for specific boats in CSIPRD"""

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
print("Checking order dates for specific boats (must be >= 2025-12-14 to be imported)")
print("="*120)
print(f"\n{'Serial':<20} {'Order No':<15} {'Order Date':<15} {'Inv Date':<15} {'ConfigID':<20} {'In Import?'}")
print("-"*120)

for serial in boats_to_check:
    cursor.execute("""
    SELECT TOP 1 
        coi.co_num,
        co.order_date,
        ah.inv_date,
        coi.config_id,
        coi.Uf_BENN_BoatSerialNumber,
        ser.ser_num
    FROM [CSIPRD].[dbo].[coitem_mst] coi
    LEFT JOIN [CSIPRD].[dbo].[serial_mst] ser
        ON coi.co_num = ser.ref_num
        AND coi.co_line = ser.ref_line
        AND ser.ref_type = 'O'
    INNER JOIN [CSIPRD].[dbo].[co_mst] co
        ON coi.co_num = co.co_num
        AND coi.site_ref = co.site_ref
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
        order_date = row['order_date'].strftime('%Y-%m-%d') if row['order_date'] else 'NULL'
        inv_date = row['inv_date'].strftime('%Y-%m-%d') if row['inv_date'] else 'NULL'
        config_id = row['config_id'] or 'NULL'
        
        # Check if would be imported
        import_cutoff = '2025-12-14'
        would_import = 'YES' if order_date >= import_cutoff else 'NO - TOO OLD'
        
        print(f"{serial:<20} {row['co_num']:<15} {order_date:<15} {inv_date:<15} {config_id:<20} {would_import}")
    else:
        print(f"{serial:<20} {'NOT FOUND':<15} {'N/A':<15} {'N/A':<15} {'N/A':<20} {'NO'}")

cursor.close()
conn.close()
print("\n" + "="*120)
print("Import cutoff date: 2025-12-14")
print("="*120)

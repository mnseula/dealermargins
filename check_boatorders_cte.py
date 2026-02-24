#!/usr/bin/env python3
"""Check if boats match the BoatOrders CTE criteria"""

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

print("="*130)
print("Checking BoatOrders CTE criteria (this is the FIRST filter in the query)")
print("="*130)
print(f"\n{'Serial':<20} {'In BoatOrders CTE?':<20} {'coi.Uf_BENN_BoatSerialNumber':<35} {'ser.ser_num':<20} {'coi.config_id':<15}")
print("-"*130)

for serial in boats_to_check:
    # Check if boat would be in BoatOrders CTE
    cursor.execute("""
    SELECT 
        coi.co_num,
        coi.Uf_BENN_BoatSerialNumber,
        ser.ser_num,
        coi.config_id
    FROM [CSIPRD].[dbo].[coitem_mst] coi
    LEFT JOIN [CSIPRD].[dbo].[serial_mst] ser
        ON coi.co_num = ser.ref_num
        AND coi.co_line = ser.ref_line
        AND coi.co_release = ser.ref_release
        AND coi.item = ser.item
        AND coi.site_ref = ser.site_ref
        AND ser.ref_type = 'O'
    WHERE coi.site_ref = 'BENN'
        AND (
            (coi.Uf_BENN_BoatSerialNumber IS NOT NULL AND coi.Uf_BENN_BoatSerialNumber != '')
            OR
            (coi.config_id IS NOT NULL AND coi.config_id != '')
        )
        AND (coi.Uf_BENN_BoatSerialNumber = %s OR ser.ser_num = %s)
    """, (serial, serial))
    
    row = cursor.fetchone()
    
    if row:
        in_cte = "YES"
        boat_serial = row['Uf_BENN_BoatSerialNumber'] or 'NULL'
        ser_num = row['ser_num'] or 'NULL'
        config_id = row['config_id'] or 'NULL'
        print(f"{serial:<20} {in_cte:<20} {boat_serial:<35} {ser_num:<20} {config_id:<15}")
    else:
        # Boat not in CTE - check why
        cursor.execute("""
        SELECT 
            coi.co_num,
            coi.Uf_BENN_BoatSerialNumber,
            ser.ser_num,
            coi.config_id
        FROM [CSIPRD].[dbo].[coitem_mst] coi
        LEFT JOIN [CSIPRD].[dbo].[serial_mst] ser
            ON coi.co_num = ser.ref_num
            AND coi.co_line = ser.ref_line
            AND coi.co_release = ser.ref_release
            AND coi.item = ser.item
            AND coi.site_ref = ser.site_ref
            AND ser.ref_type = 'O'
        WHERE coi.site_ref = 'BENN'
            AND (coi.Uf_BENN_BoatSerialNumber = %s OR ser.ser_num = %s)
        """, (serial, serial))
        
        row = cursor.fetchone()
        if row:
            boat_serial = row['Uf_BENN_BoatSerialNumber'] or 'NULL'
            ser_num = row['ser_num'] or 'NULL'
            config_id = row['config_id'] or 'NULL'
            reason = "Missing both BoatSerialNumber AND config_id"
            print(f"{serial:<20} {'NO - ' + reason:<20} {boat_serial:<35} {ser_num:<20} {config_id:<15}")
        else:
            print(f"{serial:<20} {'NO - Not found in coitem_mst':<20} {'N/A':<35} {'N/A':<20} {'N/A':<15}")

cursor.close()
conn.close()
print("\n" + "="*130)
print("BoatOrders CTE requires: (Uf_BENN_BoatSerialNumber IS NOT NULL) OR (config_id IS NOT NULL)")
print("="*130)

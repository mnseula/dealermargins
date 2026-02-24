#!/usr/bin/env python3
"""Diagnostic script to test SerialNumberMaster query filters"""

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
print("Testing SerialNumberMaster Query Filters")
print("="*130)

# Test 1: Basic boat lookup without filters
print("\n1. Checking if boats exist in coitem_mst at all:")
print("-"*130)
for serial in boats_to_check[:3]:  # Just check first 3
    cursor.execute("""
    SELECT TOP 1 co_num, Uf_BENN_BoatSerialNumber, item, co_line
    FROM [CSIPRD].[dbo].[coitem_mst]
    WHERE site_ref = 'BENN'
      AND (Uf_BENN_BoatSerialNumber = %s OR item LIKE %s)
    """, (serial, f'%{serial}%'))
    
    row = cursor.fetchone()
    if row:
        print(f"{serial}: co_num={row['co_num']}, BoatSerialNo={row['Uf_BENN_BoatSerialNumber']}, item={row['item']}")
    else:
        print(f"{serial}: NOT FOUND in coitem_mst")

# Test 2: Check serial_mst join
print("\n2. Checking serial_mst join:")
print("-"*130)
for serial in boats_to_check[:3]:
    cursor.execute("""
    SELECT TOP 1 
        ser.ref_num, ser.ref_line, ser.ser_num,
        coi.co_num, coi.co_line, coi.item
    FROM [CSIPRD].[dbo].[serial_mst] ser
    INNER JOIN [CSIPRD].[dbo].[coitem_mst] coi
        ON ser.ref_num = coi.co_num
        AND ser.ref_line = coi.co_line
        AND ser.ref_release = coi.co_release
        AND ser.item = coi.item
        AND ser.site_ref = coi.site_ref
    WHERE ser.ser_num = %s
      AND ser.site_ref = 'BENN'
      AND ser.ref_type = 'O'
    """, (serial,))
    
    row = cursor.fetchone()
    if row:
        print(f"{serial}: Join SUCCESS - co_num={row['co_num']}, ser_line={row['ref_line']}, coi_line={row['co_line']}")
    else:
        print(f"{serial}: Join FAILED - checking serial_mst directly...")
        # Check if serial exists in serial_mst at all
        cursor.execute("""
        SELECT TOP 1 ref_num, ref_line, ref_release, item, ser_num
        FROM [CSIPRD].[dbo].[serial_mst]
        WHERE ser_num = %s
        AND site_ref = 'BENN'
        AND ref_type = 'O'
        """, (serial,))
        row2 = cursor.fetchone()
        if row2:
            print(f"  -> Serial exists: ref_num={row2['ref_num']}, line={row2['ref_line']}, item={row2['item']}")
        else:
            print(f"  -> Serial NOT in serial_mst")

# Test 3: Check item_mst MaterialCostType
print("\n3. Checking item_mst MaterialCostType:")
print("-"*130)
for serial in boats_to_check[:3]:
    cursor.execute("""
    SELECT TOP 1 
        coi.item, coi.Uf_BENN_BoatSerialNumber, 
        im.Uf_BENN_MaterialCostType, im.Uf_BENN_Series
    FROM [CSIPRD].[dbo].[coitem_mst] coi
    LEFT JOIN [CSIPRD].[dbo].[serial_mst] ser
        ON coi.co_num = ser.ref_num
        AND coi.co_line = ser.ref_line
        AND coi.co_release = ser.ref_release
        AND coi.item = ser.item
        AND coi.site_ref = ser.site_ref
        AND ser.ref_type = 'O'
    LEFT JOIN [CSIPRD].[dbo].[item_mst] im
        ON coi.item = im.item
        AND coi.site_ref = im.site_ref
    WHERE coi.site_ref = 'BENN'
      AND (coi.Uf_BENN_BoatSerialNumber = %s OR ser.ser_num = %s)
    """, (serial, serial))
    
    row = cursor.fetchone()
    if row:
        print(f"{serial}: item={row['item']}, MCT={row['Uf_BENN_MaterialCostType']}, Series={row['Uf_BENN_Series']}")
    else:
        print(f"{serial}: No data")

# Test 4: Check inv_item_mst
print("\n4. Checking inv_item_mst join:")
print("-"*130)
for serial in boats_to_check[:3]:
    cursor.execute("""
    SELECT TOP 1 
        coi.co_num, coi.co_line, coi.co_release,
        iim.inv_num
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
    WHERE coi.site_ref = 'BENN'
      AND (coi.Uf_BENN_BoatSerialNumber = %s OR ser.ser_num = %s)
      AND coi.qty_invoiced > 0
    """, (serial, serial))
    
    row = cursor.fetchone()
    if row:
        print(f"{serial}: inv_num={row['inv_num']}, qty_invoiced match")
    else:
        print(f"{serial}: inv_item_mst join FAILED")

cursor.close()
conn.close()
print("\n" + "="*130)

#!/usr/bin/env python3
"""Verify ETWINVTEST01 import"""
import mysql.connector

conn = mysql.connector.connect(
    host='ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    port=3306,
    database='warrantyparts',
    user='awsmaster',
    password='VWvHG9vfG23g7gD'
)

cursor = conn.cursor(dictionary=True)

print('='*80)
print('VERIFYING ETWINVTEST01 IMPORT')
print('='*80)
print()

cursor.execute('''
    SELECT
        LineNo,
        LineSeqNo,
        ERP_OrderNo,
        BoatSerialNo,
        BoatModelNo,
        ItemNo,
        ItemDesc1,
        ItemMasterProdCat,
        ItemMasterMCT,
        MCTDesc,
        ConfigID,
        CfgName,
        CfgValue,
        MSRP,
        ExtSalesAmount
    FROM BoatOptions99_04
    WHERE BoatSerialNo = 'ETWINVTEST01'
    ORDER BY LineSeqNo
''')

rows = cursor.fetchall()

if not rows:
    print('❌ ETWINVTEST01 NOT FOUND!')
else:
    print(f'✅ Found {len(rows)} rows for ETWINVTEST01')
    print()

    for row in rows:
        print(f'LineSeqNo {row["LineSeqNo"]}: {row["ItemNo"]} - {row["ItemDesc1"]}')
        print(f'  Order: {row["ERP_OrderNo"]}')
        print(f'  BoatModelNo: {row["BoatModelNo"]}')
        print(f'  ProdCat: {row["ItemMasterProdCat"]}, MCT: {row["ItemMasterMCT"]}')

        if row['ConfigID']:
            print(f'  ✅ CPQ Config: {row["ConfigID"]}')
            print(f'     CfgName: {row["CfgName"]}')
            print(f'     CfgValue: {row["CfgValue"]}')
            msrp = row["MSRP"] or 0
            print(f'     MSRP: ${msrp:.2f}')
        else:
            print(f'  ⚠️  No CPQ data (ConfigID is NULL)')

        print()

    # Check for issues
    print('='*80)
    print('VALIDATION CHECKS:')
    print('='*80)

    # Check LineSeqNo uniqueness
    lineseqs = [r['LineSeqNo'] for r in rows]
    if len(lineseqs) == len(set(lineseqs)) and 0 not in lineseqs:
        print('✅ LineSeqNo values are unique and non-zero')
    else:
        print('❌ LineSeqNo has duplicates or zeros!')
        print(f'   Values: {lineseqs}')

    # Check BoatModelNo
    boat_items = [r for r in rows if r['ItemMasterMCT'] in ('BOA', 'BOI')]
    if boat_items and all(r['BoatModelNo'] for r in boat_items):
        print(f'✅ BoatModelNo is populated: {boat_items[0]["BoatModelNo"]}')
    else:
        print('❌ BoatModelNo is NULL on boat items!')

    # Check CPQ data
    cpq_rows = [r for r in rows if r['ConfigID']]
    if cpq_rows:
        print(f'✅ CPQ data present: {len(cpq_rows)} rows have ConfigID')
    else:
        print('❌ No CPQ data found!')

    # Check ERP_OrderNo
    if all(r['ERP_OrderNo'] == 'SO00936074' for r in rows):
        print('✅ ERP_OrderNo is correct: SO00936074')
    else:
        print('❌ ERP_OrderNo mismatch!')

cursor.close()
conn.close()

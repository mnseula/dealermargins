#!/usr/bin/env python3
"""Query boat ETWINVTEST0226 from Eos database"""

import mysql.connector

conn = mysql.connector.connect(
    host='ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    user='awsmaster',
    password='VWvHG9vfG23g7gD',
    database='Eos'
)

cursor = conn.cursor(dictionary=True)

# Get all line items for this boat
cursor.execute('''
    SELECT LineNo, ItemNo, ItemDesc1, ItemMasterMCT, ItemMasterProdCat,
           QuantitySold, ExtSalesAmount, MSRP, ConfigID
    FROM BoatOptions26_Complete
    WHERE BoatSerialNo = %s
    ORDER BY LineNo
''', ('ETWINVTEST0226',))

rows = cursor.fetchall()

print('='*80)
print('All line items for boat ETWINVTEST0226 (23ML, M Series):')
print('='*80)
print(f'Total lines: {len(rows)}')
print()

total_ext_sales = 0
total_msrp = 0

for row in rows:
    ext_sales = row['ExtSalesAmount'] or 0
    msrp = row['MSRP'] or 0
    total_ext_sales += ext_sales
    total_msrp += msrp

    print(f"Line {row['LineNo']:2}: {row['ItemNo']:15} {row['ItemDesc1']:30}")
    print(f"         MCT: {row['ItemMasterMCT']:10} ProdCat: {row['ItemMasterProdCat']:5}")
    print(f"         ExtSales: ${ext_sales:10,.2f}   MSRP: ${msrp:10,.2f}")
    if row['ConfigID']:
        print(f"         ConfigID: {row['ConfigID']}")
    print()

print('='*80)
print(f'TOTALS:')
print(f'  Total ExtSalesAmount: ${total_ext_sales:,.2f}')
print(f'  Total MSRP:           ${total_msrp:,.2f}')
print('='*80)

# Also get dealer information
cursor.execute('''
    SELECT DISTINCT DealerNo, DealerName
    FROM dealer_master_list
    WHERE DealerNo = '50'
''')

dealer = cursor.fetchone()
if dealer:
    print(f"\nDealer Information:")
    print(f"  Dealer No:   {dealer['DealerNo']}")
    print(f"  Dealer Name: {dealer['DealerName']}")

cursor.close()
conn.close()

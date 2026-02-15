#!/usr/bin/env python3
"""Check BoatOptions26 structure for ETWS7943H526"""
import mysql.connector

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts'
}

serial = 'ETWS7943H526'

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor(dictionary=True)

print('='*80)
print(f'BoatOptions26 Data Structure for {serial}')
print('='*80)

# Get sample records to understand structure
cursor.execute("""
    SELECT ItemMasterMCT, MCTDesc, ItemNo, ItemDesc1,
           BoatModelNo, InvoiceNo, QuantitySold, MSRP, ExtSalesAmount
    FROM BoatOptions26
    WHERE BoatSerialNo = %s
    ORDER BY LineNo
    LIMIT 10
""", (serial,))

rows = cursor.fetchall()
print(f'\nFirst 10 records (of 33 total):')
print('-'*80)
for i, row in enumerate(rows, 1):
    msrp_val = row['MSRP'] if row['MSRP'] is not None else 0
    print(f'{i}. MCT: {row["ItemMasterMCT"]:6s} | {row["ItemDesc1"][:40]:40s} | MSRP: ${msrp_val:,.2f}')

# Check if boat model record exists
cursor.execute("""
    SELECT * FROM BoatOptions26
    WHERE BoatSerialNo = %s
    AND ItemMasterMCT IN ('BOA', 'BOI')
""", (serial,))
boat_model = cursor.fetchone()

if boat_model:
    print(f'\n✅ Boat Model Record Found:')
    print(f'   Model: {boat_model["BoatModelNo"]}')
    print(f'   Description: {boat_model["ItemDesc1"]}')
    print(f'   Invoice: {boat_model["InvoiceNo"]}')
    msrp = boat_model["MSRP"] if boat_model["MSRP"] is not None else 0
    dealer_cost = boat_model["ExtSalesAmount"] if boat_model["ExtSalesAmount"] is not None else 0
    print(f'   MSRP: ${msrp:,.2f}')
    print(f'   Dealer Cost: ${dealer_cost:,.2f}')
else:
    print(f'\n❌ No boat model record (BOA/BOI) found')

cursor.close()
conn.close()

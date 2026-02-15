#!/usr/bin/env python3
"""Check margins for dealer 333833 - NICHOLS MARINE OF LONGVIEW LLC"""
import mysql.connector

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts'
}

dealer_id = '333833'

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor(dictionary=True)

print('='*80)
print(f'Dealer 333833 - NICHOLS MARINE OF LONGVIEW LLC')
print('='*80)

# Get all margin columns for this dealer
cursor.execute("""
    SELECT *
    FROM DealerMargins
    WHERE DealerID = %s
""", (dealer_id,))

dealer = cursor.fetchone()

if dealer:
    print(f'\nDealer: {dealer["Dealership"]}')
    print(f'DealerID: {dealer["DealerID"]}')
    print('\nMargins by Series:')
    print('-'*80)

    # Check S Series (boat ETWS7943H526 is 22SSBSF - S Series)
    if 'S_BASE_BOAT' in dealer:
        print(f'\nS Series (⭐ Current boat series):')
        print(f'  Base Boat: {dealer["S_BASE_BOAT"]}%')
        print(f'  Engine: {dealer["S_ENGINE"]}%')
        print(f'  Options: {dealer["S_OPTIONS"]}%')
        print(f'  Vol Disc: {dealer["S_VOL_DISC"]}%')
        print(f'  Freight: ${dealer["S_FREIGHT"]}')
        print(f'  Prep: ${dealer["S_PREP"]}')

    # Check other series
    for series in ['Q', 'QX', 'R', 'L', 'M']:
        col_base = f'{series}_BASE_BOAT'
        if col_base in dealer and dealer[col_base] is not None:
            print(f'\n{series} Series:')
            print(f'  Base: {dealer[col_base]}% | Engine: {dealer[series + "_ENGINE"]}% | Options: {dealer[series + "_OPTIONS"]}% | Vol: {dealer[series + "_VOL_DISC"]}%')
            print(f'  Freight: ${dealer[series + "_FREIGHT"]} | Prep: ${dealer[series + "_PREP"]}')
else:
    print(f'❌ Dealer {dealer_id} not found')

cursor.close()
conn.close()

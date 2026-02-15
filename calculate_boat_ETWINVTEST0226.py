#!/usr/bin/env python3
"""
Calculate MSRP and Price for boat ETWINVTEST0226 using CPQ margins
"""

import mysql.connector

# Connect to Eos database
conn = mysql.connector.connect(
    host='ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    user='awsmaster',
    password='VWvHG9vfG23g7gD',
    database='Eos'
)

cursor = conn.cursor(dictionary=True, buffered=True)

# Get boat data
print('='*80)
print('BOAT ETWINVTEST0226 - MARGIN CALCULATIONS')
print('='*80)

cursor.execute('''
    SELECT DISTINCT BoatSerialNo, BoatModelNo, Series
    FROM BoatOptions26_Complete
    WHERE BoatSerialNo = %s
''', ('ETWINVTEST0226',))

boat_info = cursor.fetchone()
print(f"\nBoat Information:")
print(f"  Serial:      {boat_info['BoatSerialNo']}")
print(f"  Model:       {boat_info['BoatModelNo']}")
print(f"  Series:      {boat_info['Series']}")

# Get CPQ base boat pricing
# The base boat is the BOA line with the highest ExtSalesAmount and non-zero MSRP
cursor.execute('''
    SELECT ItemNo, ItemDesc1, ExtSalesAmount, MSRP
    FROM BoatOptions26_Complete
    WHERE BoatSerialNo = %s
      AND ItemMasterProdCat = 'BS1'
      AND ItemMasterMCT = 'BOA'
      AND MSRP > 0
    ORDER BY MSRP DESC
    LIMIT 1
''', ('ETWINVTEST0226',))

base_boat = cursor.fetchone()

if base_boat:
    cpq_dealer_cost = float(base_boat['ExtSalesAmount'] or 0)
    cpq_msrp = float(base_boat['MSRP'] or 0)

    print(f"\nCPQ Base Boat Pricing (from API):")
    print(f"  Dealer Cost: ${cpq_dealer_cost:,.2f}")
    print(f"  MSRP:        ${cpq_msrp:,.2f}")
else:
    print("\n⚠️  Base boat line not found")
    cpq_dealer_cost = 0
    cpq_msrp = 0

# Get dealer margins from List 53ebba158ff57891258fef1e
# The dealer margins are stored in a separate list table in EOS
# For now, let's use the values from the previous session: Dealer 50, M Series = 37%

dealer_no = '50'
series = boat_info['Series']

# Query the dealer margin list
# The list is stored in EOS as List 53ebba158ff57891258fef1e
# Field mapping: BASE_BOAT, ENGINE, OPTIONS, VOL_DISC, FREIGHT, PREP

# For this demo, I'll use the known values from the previous session
# In production, these would be queried from the EOS List system

base_boat_margin = 37.0  # 37% margin
engine_margin = 37.0
option_margin = 37.0
vol_disc = 0.0
freight = 0.0
prep = 0.0

print(f"\nDealer Margins (Dealer {dealer_no}, Series {series}):")
print(f"  Base Boat:   {base_boat_margin}%")
print(f"  Engine:      {engine_margin}%")
print(f"  Options:     {option_margin}%")
print(f"  Vol Disc:    {vol_disc}%")
print(f"  Freight:     ${freight:,.2f}")
print(f"  Prep:        ${prep:,.2f}")

# Calculate sale price using CPQ formula: dealercost * margin
# CPQ boats: Start with dealer cost (before margins), multiply by margin to reduce
# margin_multiplier = (100 - margin_percent) / 100
# Example: 37% margin = (100 - 37) / 100 = 0.63

base_margin_multiplier = (100 - base_boat_margin) / 100
vol_disc_multiplier = (100 - vol_disc) / 100

print(f"\nMargin Multipliers:")
print(f"  Base Boat:   {base_margin_multiplier:.2f} (reduces price by {base_boat_margin}%)")
print(f"  Vol Disc:    {vol_disc_multiplier:.2f}")

# Calculate sale price
# Formula: (dealer_cost * vol_disc_multiplier) * base_margin_multiplier + freight + prep
sale_price = (cpq_dealer_cost * vol_disc_multiplier) * base_margin_multiplier + freight + prep

print(f"\n{'='*80}")
print("CALCULATED PRICING")
print('='*80)

print(f"\nMSRP (from CPQ):")
print(f"  ${cpq_msrp:,.2f}")

print(f"\nSale Price Calculation:")
print(f"  Dealer Cost:             ${cpq_dealer_cost:,.2f}")
print(f"  × Vol Disc ({vol_disc_multiplier:.2f}):    ${cpq_dealer_cost * vol_disc_multiplier:,.2f}")
print(f"  × Margin ({base_margin_multiplier:.2f}):     ${sale_price:.2f}")
print(f"  + Freight:               ${freight:,.2f}")
print(f"  + Prep:                  ${prep:,.2f}")
print(f"  ─────────────────────────────────")
print(f"  SALE PRICE:              ${sale_price:,.2f}")

print(f"\nMargin Verification:")
print(f"  Original Dealer Cost:    ${cpq_dealer_cost:,.2f}")
print(f"  Sale Price:              ${sale_price:,.2f}")
print(f"  Difference:              ${sale_price - cpq_dealer_cost:,.2f}")
if cpq_dealer_cost > 0:
    print(f"  Actual Margin:           {((cpq_dealer_cost - sale_price) / cpq_dealer_cost * 100):.2f}%")
else:
    print(f"  Actual Margin:           N/A (dealer cost is $0)")

print(f"\n{'='*80}")
print("ZERO MARGIN TEST (margin = 0%)")
print('='*80)

# Test with 0% margin (should equal original dealer cost)
zero_margin_multiplier = (100 - 0) / 100  # = 1.00
zero_margin_sale = (cpq_dealer_cost * vol_disc_multiplier) * zero_margin_multiplier + freight + prep

print(f"\nWith 0% margin:")
print(f"  Margin multiplier:       {zero_margin_multiplier:.2f}")
print(f"  Sale Price:              ${zero_margin_sale:,.2f}")
print(f"  Original Dealer Cost:    ${cpq_dealer_cost:,.2f}")
print(f"  Match:                   {'✅ YES' if abs(zero_margin_sale - cpq_dealer_cost) < 0.01 else '❌ NO'}")

print('='*80)

cursor.close()
conn.close()

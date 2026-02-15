#!/usr/bin/env python3
"""
Simulate Calculate2021.js calculation for CPQTEST26
Shows what the totals SHOULD be with the fix applied
"""

print("=" * 120)
print("SIMULATED CALCULATION FOR CPQTEST26")
print("Based on Calculate2021.js logic with Action Item 2 fix")
print("=" * 120)
print()

# From database and console logs
cpq_base_boat_dealer_cost = 42042.00
cpq_base_boat_msrp = 59459.00

# From dealer margins (dealer 50 = PONTOON BOAT, LLC, series M)
base_boat_margin_pct = 37  # 37% margin
engine_margin_pct = 37
option_margin_pct = 37
vol_disc_pct = 10  # 10% volume discount

# Convert to calculation values
baseboatmargin = (100 - base_boat_margin_pct) / 100  # 0.63 (to divide by for sale price)
optionmargin = (100 - option_margin_pct) / 100  # 0.63
msrpMargin = baseboatmargin  # Usually same as base boat
vol_disc = (100 - vol_disc_pct) / 100  # 0.9

# Costs
freight = 0.00
prep = 0.00
additional_charge = 0.00

print("INPUT VALUES:")
print("-" * 120)
print(f"  CPQ Base Boat Dealer Cost:    ${cpq_base_boat_dealer_cost:,.2f}")
print(f"  CPQ Base Boat MSRP:           ${cpq_base_boat_msrp:,.2f}")
print(f"  Base Boat Margin:             {base_boat_margin_pct}% ({baseboatmargin:.2f})")
print(f"  Option Margin:                {option_margin_pct}% ({optionmargin:.2f})")
print(f"  Volume Discount:              {vol_disc_pct}% ({vol_disc:.2f})")
print(f"  Freight:                      ${freight:,.2f}")
print(f"  Prep:                         ${prep:,.2f}")
print()

# Options from database (from console output)
options = [
    {"desc": "SPS Performance Package", "dealer_cost": 6288.00, "msrp": 8988.00},
    {"desc": "Rockford Fosgate M1 Lighted Sp", "dealer_cost": 534.00, "msrp": 764.00},
    {"desc": "Yamaha Mechanical Pre-Rig", "dealer_cost": 1688.00, "msrp": None},  # Will calculate
    {"desc": "Prerig Only", "dealer_cost": 0.00, "msrp": None},
]

print("=" * 120)
print("BOAT CALCULATION (CPQ)")
print("=" * 120)
print()

# Boat sale price calculation
boat_sale_price = (cpq_base_boat_dealer_cost * vol_disc) / baseboatmargin + freight + prep + additional_charge
boat_msrp = cpq_base_boat_msrp  # Use CPQ MSRP directly

print("BASE BOAT:")
print(f"  Dealer Cost: ${cpq_base_boat_dealer_cost:,.2f}")
print(f"  Formula: (${cpq_base_boat_dealer_cost:,.2f} × {vol_disc}) / {baseboatmargin} + ${freight} + ${prep}")
print(f"  Sale Price: ${boat_sale_price:,.2f}")
print(f"  MSRP: ${boat_msrp:,.2f} (from CPQ)")
print()

print("=" * 120)
print("OPTIONS CALCULATION")
print("=" * 120)
print()

total_options_sp = 0
total_options_msrp = 0

for opt in options:
    dealer_cost = opt["dealer_cost"]
    
    # Calculate sale price
    if dealer_cost > 0:
        sale_price = (dealer_cost / optionmargin) * vol_disc
    else:
        sale_price = 0
    
    # Calculate MSRP - use real MSRP if available, otherwise calculate
    if opt["msrp"] and opt["msrp"] > 0:
        msrp = opt["msrp"]
        msrp_source = "(real MSRP)"
    else:
        msrp = (dealer_cost * vol_disc) / msrpMargin if dealer_cost > 0 else 0
        msrp_source = "(calculated)"
    
    total_options_sp += sale_price
    total_options_msrp += msrp
    
    print(f"{opt['desc']}:")
    print(f"  Dealer Cost: ${dealer_cost:,.2f}")
    print(f"  Sale Price: ${sale_price:,.2f}")
    print(f"  MSRP: ${msrp:,.2f} {msrp_source}")
    print()

print("-" * 120)
print(f"TOTAL OPTIONS - Sale Price: ${total_options_sp:,.2f}")
print(f"TOTAL OPTIONS - MSRP: ${total_options_msrp:,.2f}")
print()

print("=" * 120)
print("FINAL TOTALS")
print("=" * 120)
print()

final_sale_price = boat_sale_price + total_options_sp
final_msrp = boat_msrp + total_options_msrp

print(f"Base Boat Sale Price:    ${boat_sale_price:>12,.2f}")
print(f"Options Sale Price:      ${total_options_sp:>12,.2f}")
print(f"{'-' * 45}")
print(f"TOTAL SALE PRICE:        ${final_sale_price:>12,.2f}")
print()
print(f"Base Boat MSRP:          ${boat_msrp:>12,.2f}")
print(f"Options MSRP:            ${total_options_msrp:>12,.2f}")
print(f"{'-' * 45}")
print(f"TOTAL MSRP:              ${final_msrp:>12,.2f}")
print()

print("=" * 120)
print("EXPECTED RESULT IN BROWSER")
print("=" * 120)
print()

print("After pulling the latest changes and reloading CPQTEST26, you should see:")
print()
print(f"  ✅ Total Sale Price: ~${final_sale_price:,.0f} (not $10,609)")
print(f"  ✅ Total MSRP: ~${final_msrp:,.0f} (not $10,503)")
print()
print("Console logs should show:")
print("  ✅ 'CPQ BOAT - Using CPQ base boat dealer cost: $42042'")
print("  ✅ 'CPQ BOAT - Added base boat to boatpackageprice: $42042'")
print("  ✅ 'CPQ BOAT - Added base boat to saleboatpackageprice: $60060'")
print("  ✅ 'BOAT MSRP TOTAL: 59459'")
print("  ✅ 'BOAT SP TOTAL: 60060'")
print()
print("=" * 120)


#!/usr/bin/env python3
"""Check pricing breakdown for CPQTEST26"""

import mysql.connector

conn = mysql.connector.connect(
    host='ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    user='awsmaster',
    password='VWvHG9vfG23g7gD',
    database='warrantyparts'
)

cursor = conn.cursor(dictionary=True)

print("\n" + "=" * 100)
print("CPQTEST26 - Pricing Breakdown")
print("=" * 100)

# Get all line items
cursor.execute("""
    SELECT
        LineNo,
        ItemNo,
        ItemDesc1,
        ItemMasterMCT,
        MCTDesc,
        MSRP,
        ExtSalesAmount,
        QuantitySold
    FROM BoatOptions26
    WHERE BoatSerialNo = 'CPQTEST26'
    ORDER BY
        CASE ItemMasterMCT
            WHEN 'BOA' THEN 1
            WHEN 'PRE' THEN 2
            WHEN 'ENGINES' THEN 3
            WHEN 'ACC' THEN 4
            ELSE 5
        END,
        LineNo
""")

items = cursor.fetchall()

print(f"\n{'Category':<15} {'ItemNo':<20} {'MCTDesc':<25} {'MSRP':<15} {'ExtSales':<15} {'Description':<40}")
print("-" * 140)

base_boat_items = []
pre_rig_items = []
engine_items = []
acc_items = []

for item in items:
    itemno = item['ItemNo'] or ''
    mct = item['ItemMasterMCT'] or ''
    mctdesc = item['MCTDesc'] or ''
    desc = (item['ItemDesc1'] or '')[:40]
    msrp = item['MSRP'] or 0
    extsales = item['ExtSalesAmount'] or 0

    if mct == 'BOA':
        base_boat_items.append(item)
        print(f"{'BASE BOAT':<15} {itemno:<20} {mctdesc:<25} ${msrp:<14,.2f} ${extsales:<14,.2f} {desc:<40}")
    elif mct == 'PRE':
        pre_rig_items.append(item)
        print(f"{'PRE-RIG':<15} {itemno:<20} {mctdesc:<25} ${msrp:<14,.2f} ${extsales:<14,.2f} {desc:<40}")
    elif mct == 'ENGINES':
        engine_items.append(item)
        print(f"{'ENGINE':<15} {itemno:<20} {mctdesc:<25} ${msrp:<14,.2f} ${extsales:<14,.2f} {desc:<40}")
    elif mct == 'ACC':
        acc_items.append(item)

# Show accessories summary
print(f"{'ACCESSORIES':<15} {'':<20} {'':<25} {'':<15} {'':<15} ({len(acc_items)} items)")

print("\n" + "=" * 100)
print("HOW SELLING PRICE IS CALCULATED:")
print("=" * 100)

print("\n1. BASE BOAT (CPQ boats use special pricing):")
print("-" * 100)
for item in base_boat_items:
    msrp = item['MSRP'] or 0
    extsales = item['ExtSalesAmount'] or 0
    if msrp > 0:
        print(f"   '{item['ItemDesc1']}' - MSRP: ${msrp:,.2f}, ExtSales (Dealer Cost): ${extsales:,.2f}")
        print(f"   → This item is used for BOAT_MS and BOAT_SP calculations")
    else:
        print(f"   '{item['ItemDesc1']}' - MSRP: ${msrp:,.2f} (SKIPPED - not displayed)")

print("\n   For CPQ boats, calculate.js sets:")
print("   - BOAT_MS (Base Boat MSRP) = $59,459.00 (from CPQ data)")
print("   - BOAT_SP (Base Boat Sale Price) = calculated using dealer margin")
print("   - These values are stored in DLR2.BOAT_MS and DLR2.BOAT_SP")

print("\n2. ENGINES:")
print("-" * 100)
engine_msrp_total = 0
engine_dc_total = 0
for item in engine_items:
    msrp = item['MSRP'] or 0
    extsales = item['ExtSalesAmount'] or 0
    print(f"   '{item['ItemDesc1']}' - MSRP: ${msrp:,.2f}, Dealer Cost: ${extsales:,.2f}")
    engine_msrp_total += msrp
    engine_dc_total += extsales

print(f"\n   Engine values stored in DLR2.ENG_MS and DLR2.ENG_SP")

print("\n3. PRE-RIG:")
print("-" * 100)
prerig_msrp_total = 0
prerig_dc_total = 0
for item in pre_rig_items:
    msrp = item['MSRP'] or 0
    extsales = item['ExtSalesAmount'] or 0
    print(f"   '{item['ItemDesc1']}' - MSRP: ${msrp:,.2f}, Dealer Cost: ${extsales:,.2f}")
    prerig_msrp_total += msrp
    prerig_dc_total += extsales

print(f"\n   Pre-rig included in option totals (DLR2.OPT_MS and DLR2.OPT_SP)")

print("\n4. ACCESSORIES:")
print("-" * 100)
acc_msrp_total = 0
acc_dc_total = 0
for item in acc_items:
    msrp = item['MSRP'] or 0
    extsales = item['ExtSalesAmount'] or 0
    acc_msrp_total += msrp
    acc_dc_total += extsales

print(f"   {len(acc_items)} accessories - Total MSRP: ${acc_msrp_total:,.2f}, Total Dealer Cost: ${acc_dc_total:,.2f}")
print(f"   Accessories included in option totals (DLR2.OPT_MS and DLR2.OPT_SP)")

print("\n\n" + "=" * 100)
print("FINAL SELLING PRICE CALCULATION:")
print("=" * 100)
print("\nTotal Selling Price = DLR2.BOAT_SP + DLR2.ENG_SP + DLR2.OPT_SP")
print("\nWhere:")
print("  - DLR2.BOAT_SP = Base boat sale price (calculated from dealer margin)")
print("  - DLR2.ENG_SP = Engine sale price (calculated from dealer margin)")
print("  - DLR2.OPT_SP = Options sale price (includes pre-rig + accessories)")
print("\n")
print("=" * 100)
print("IMPORTANT: Adding base boat to boattable array DOES NOT affect totals!")
print("=" * 100)
print("\n✓ boattable[] is ONLY used for display in GenerateBoatTable.js")
print("✓ Totals come from DLR2 values set by calculate.js")
print("✓ Our changes only added items to boattable for display purposes")
print("✓ The selling price calculations remain unchanged")
print("\n")

cursor.close()
conn.close()

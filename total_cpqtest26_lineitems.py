#!/usr/bin/env python3
"""
Total all line items from BoatOptions26 for CPQTEST26
Compare with window sticker when margins are set to 0%
"""

import mysql.connector
from decimal import Decimal

# Database connection
conn = mysql.connector.connect(
    host='ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    user='awsmaster',
    password='VWvHG9vfG23g7gD',
    database='warrantyparts'
)

cursor = conn.cursor(dictionary=True)

print("\n" + "="*100)
print("CPQTEST26 - Line Item Totals Analysis")
print("="*100)

# Get all line items for CPQTEST26
cursor.execute("""
    SELECT
        ItemNo,
        ItemDesc1,
        ItemMasterMCT,
        MCTDesc,
        ItemMasterProdCat,
        QuantitySold,
        ExtSalesAmount,
        MSRP
    FROM BoatOptions26
    WHERE BoatSerialNo = 'CPQTEST26'
    ORDER BY
        CASE MCTDesc
            WHEN 'PONTOONS' THEN 1
            WHEN 'Pontoon Boats OB' THEN 1
            WHEN 'ENGINES' THEN 2
            WHEN 'Engine' THEN 2
            WHEN 'PRE-RIG' THEN 3
            WHEN 'Prerig' THEN 3
            ELSE 4
        END,
        LineNo
""")

items = cursor.fetchall()

# Initialize category totals
categories = {
    'Base Boat (BOA)': {'dealer_cost': Decimal('0'), 'msrp': Decimal('0'), 'count': 0, 'items': []},
    'Engine (ENG)': {'dealer_cost': Decimal('0'), 'msrp': Decimal('0'), 'count': 0, 'items': []},
    'Pre-Rig (PRE)': {'dealer_cost': Decimal('0'), 'msrp': Decimal('0'), 'count': 0, 'items': []},
    'Options/Accessories (ACC)': {'dealer_cost': Decimal('0'), 'msrp': Decimal('0'), 'count': 0, 'items': []},
    'Config/Standard (STD)': {'dealer_cost': Decimal('0'), 'msrp': Decimal('0'), 'count': 0, 'items': []},
    'Other': {'dealer_cost': Decimal('0'), 'msrp': Decimal('0'), 'count': 0, 'items': []}
}

print(f"\nTotal line items: {len(items)}\n")

# Categorize and sum
for item in items:
    mct = item['ItemMasterMCT']
    desc = item['ItemDesc1']
    dealer_cost = Decimal(str(item['ExtSalesAmount'] or 0))
    msrp = Decimal(str(item['MSRP'] or 0))

    # Determine category
    if mct == 'BOA' or mct == 'BOI':
        cat = 'Base Boat (BOA)'
    elif mct == 'ENG':
        cat = 'Engine (ENG)'
    elif mct == 'PRE':
        cat = 'Pre-Rig (PRE)'
    elif item['ItemMasterProdCat'] == 'ACC':
        cat = 'Options/Accessories (ACC)'
    elif mct == 'STD' or item['ItemMasterProdCat'] == 'STD':
        cat = 'Config/Standard (STD)'
    else:
        cat = 'Other'

    categories[cat]['dealer_cost'] += dealer_cost
    categories[cat]['msrp'] += msrp
    categories[cat]['count'] += 1
    categories[cat]['items'].append({
        'desc': desc,
        'mct': mct,
        'dealer_cost': dealer_cost,
        'msrp': msrp
    })

# Print category summaries
print("CATEGORY TOTALS:")
print("-" * 100)
print(f"{'Category':<30} {'Count':>8} {'Dealer Cost':>15} {'MSRP':>15}")
print("-" * 100)

grand_total_dc = Decimal('0')
grand_total_msrp = Decimal('0')

for cat_name, cat_data in categories.items():
    if cat_data['count'] > 0:
        print(f"{cat_name:<30} {cat_data['count']:>8} ${cat_data['dealer_cost']:>14,.2f} ${cat_data['msrp']:>14,.2f}")
        grand_total_dc += cat_data['dealer_cost']
        grand_total_msrp += cat_data['msrp']

print("-" * 100)
print(f"{'GRAND TOTAL':<30} {len(items):>8} ${grand_total_dc:>14,.2f} ${grand_total_msrp:>14,.2f}")
print("=" * 100)

# Print detailed breakdown for key categories
print("\n" + "="*100)
print("DETAILED BREAKDOWN - Items with Non-Zero Costs")
print("="*100)

for cat_name in ['Base Boat (BOA)', 'Pre-Rig (PRE)', 'Options/Accessories (ACC)']:
    cat_data = categories[cat_name]
    if cat_data['count'] > 0:
        print(f"\n{cat_name} ({cat_data['count']} items):")
        print("-" * 100)
        print(f"{'Description':<50} {'MCT':>6} {'Dealer Cost':>15} {'MSRP':>15}")
        print("-" * 100)

        for item in cat_data['items']:
            if item['dealer_cost'] > 0 or item['msrp'] > 0:
                print(f"{item['desc'][:50]:<50} {item['mct']:>6} ${item['dealer_cost']:>14,.2f} ${item['msrp']:>14,.2f}")

# Calculate what window sticker SHOULD show at 0% margin
print("\n" + "="*100)
print("EXPECTED WINDOW STICKER TOTALS AT 0% MARGIN:")
print("="*100)
print("\nAt 0% margin, Sale Price should equal MSRP for all items.")
print("\nExpected totals (items that should appear on window sticker):")
print("-" * 100)

# Base Boat (CPQ uses Base Boat MSRP from "Base Boat" line)
base_boat_items = [i for i in categories['Base Boat (BOA)']['items'] if 'Base Boat' in i['desc'] or 'base' in i['desc'].lower()]
if base_boat_items:
    base_boat_msrp = base_boat_items[0]['msrp']
    print(f"Base Boat (from 'Base Boat' line):        ${base_boat_msrp:>12,.2f}")
else:
    # Fallback: sum all BOA items
    base_boat_msrp = categories['Base Boat (BOA)']['msrp']
    print(f"Base Boat (all BOA items):                 ${base_boat_msrp:>12,.2f}")

# Pre-Rig
prerig_msrp = categories['Pre-Rig (PRE)']['msrp']
print(f"Pre-Rig:                                   ${prerig_msrp:>12,.2f}")

# Options/Accessories
options_msrp = categories['Options/Accessories (ACC)']['msrp']
print(f"Options/Accessories:                       ${options_msrp:>12,.2f}")

# Total
expected_total = base_boat_msrp + prerig_msrp + options_msrp
print("-" * 100)
print(f"EXPECTED WINDOW STICKER TOTAL:             ${expected_total:>12,.2f}")
print("=" * 100)

print("\n📊 Compare this total to the window sticker when margins are set to 0%")
print("   (At 0% margin, Sale Price = MSRP for all items)\n")

cursor.close()
conn.close()

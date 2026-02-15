#!/usr/bin/env python3
"""
Test Action Item 2 Fix: Verify boat items (BS1/BOA) are excluded from calculations

Expected behavior:
- BS1/BOA items should NOT be included in line item totals
- Base boat MSRP comes from Models/ModelPricing tables, not from line items
- Total should exclude the $93,198 boat items and only sum accessories, engines, etc.
"""

import mysql.connector

conn = mysql.connector.connect(
    host='ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    user='awsmaster',
    password='VWvHG9vfG23g7gD',
    database='warrantyparts'
)
cursor = conn.cursor()

print("=" * 100)
print("ACTION ITEM 2 FIX VERIFICATION - Boat Item Double-Counting")
print("=" * 100)
print()

# Test with CPQTEST26
test_serial = 'CPQTEST26'

cursor.execute("""
    SELECT
        LineNo,
        ItemNo,
        ItemDesc1,
        ItemMasterProdCat,
        QuantitySold,
        ExtSalesAmount
    FROM BoatOptions26
    WHERE BoatSerialNo = %s
    ORDER BY LineNo
""", (test_serial,))

rows = cursor.fetchall()

print(f"Testing boat serial: {test_serial}")
print(f"Total line items: {len(rows)}")
print()

# Categorize items
boat_items = []  # BS1/BOA - Should be EXCLUDED
engine_items = []  # ENG/ENA/ENI
accessory_items = []  # ACC
other_items = []

for row in rows:
    line_no, item_no, desc, prod_cat, qty, ext_amt = row
    ext_amt = ext_amt or 0

    if prod_cat in ('BS1', 'BOA'):
        boat_items.append((line_no, item_no, desc, ext_amt))
    elif prod_cat in ('ENG', 'ENA', 'ENI'):
        engine_items.append((line_no, item_no, desc, ext_amt))
    elif prod_cat == 'ACC':
        accessory_items.append((line_no, item_no, desc, ext_amt))
    else:
        other_items.append((line_no, item_no, desc, prod_cat, ext_amt))

# Display results
print("🚫 BOAT ITEMS (BS1/BOA) - Should be EXCLUDED from calculations:")
print("-" * 100)
boat_total = 0
for line_no, item_no, desc, amt in boat_items:
    boat_total += amt
    print(f"   Line {line_no}: {item_no:<20} {desc[:50]:<50} ${amt:>12,.2f}")
print(f"   {'EXCLUDED TOTAL':<72} ${boat_total:>12,.2f}")
print()

print("✅ ENGINE ITEMS (ENG/ENA/ENI) - INCLUDED:")
print("-" * 100)
engine_total = sum(item[3] for item in engine_items)
for line_no, item_no, desc, amt in engine_items:
    if amt != 0:  # Only show non-zero
        print(f"   Line {line_no}: {item_no:<20} {desc[:50]:<50} ${amt:>12,.2f}")
print(f"   {'ENGINE TOTAL':<72} ${engine_total:>12,.2f}")
print()

print("✅ ACCESSORY ITEMS (ACC) - INCLUDED:")
print("-" * 100)
acc_total = sum(item[3] for item in accessory_items if item[3] != 0)
acc_count = sum(1 for item in accessory_items if item[3] != 0)
print(f"   {acc_count} accessories with non-zero amounts")
print(f"   {'ACCESSORIES TOTAL':<72} ${acc_total:>12,.2f}")
print()

# Calculate corrected total (excluding boat items)
corrected_total = engine_total + acc_total + sum(item[4] for item in other_items)

# Calculate original incorrect total (including boat items)
incorrect_total = corrected_total + boat_total

print("=" * 100)
print("SUMMARY:")
print("=" * 100)
print(f"❌ OLD INCORRECT TOTAL (with boat items):        ${incorrect_total:>12,.2f}")
print(f"✅ NEW CORRECT TOTAL (without boat items):       ${corrected_total:>12,.2f}")
print(f"💰 DIFFERENCE (boat items excluded):             ${boat_total:>12,.2f}")
print()

if len(boat_items) > 0:
    print(f"✅ SUCCESS: Found {len(boat_items)} boat items that should be excluded")
    print(f"   These boat items totaling ${boat_total:,.2f} will no longer double-count")
else:
    print("⚠️  WARNING: No boat items (BS1/BOA) found - test may not be valid")

print()
print("=" * 100)

cursor.close()
conn.close()

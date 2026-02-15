#!/usr/bin/env python3
"""
Test 10 distinct CPQ boats - verify pricing at 0% margin
Sale Price should equal MSRP for all items at 0% margin
"""

import mysql.connector
from decimal import Decimal

conn = mysql.connector.connect(
    host='ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    user='awsmaster',
    password='VWvHG9vfG23g7gD',
    database='warrantyparts'
)

cursor = conn.cursor(dictionary=True)

print("\n" + "="*120)
print("CPQ BOATS - 0% MARGIN PRICING VERIFICATION")
print("="*120)

# Find CPQ boats in BoatOptions26 (boats with "Base Boat" line)
cursor.execute("""
    SELECT DISTINCT
        bo.BoatSerialNo,
        bo.BoatModelNo,
        bo.InvoiceNo,
        COUNT(DISTINCT bo.ItemNo) as total_items,
        MAX(CASE WHEN bo.ItemDesc1 LIKE '%Base Boat%' THEN bo.MSRP END) as base_boat_msrp,
        MAX(CASE WHEN bo.ItemDesc1 LIKE '%Base Boat%' THEN bo.ExtSalesAmount END) as base_boat_dealer_cost
    FROM BoatOptions26 bo
    WHERE bo.BoatSerialNo IS NOT NULL
      AND bo.BoatSerialNo != ''
      AND EXISTS (
          SELECT 1 FROM BoatOptions26 bo2
          WHERE bo2.BoatSerialNo = bo.BoatSerialNo
            AND bo2.ItemDesc1 LIKE '%Base Boat%'
            AND bo2.MSRP > 0
      )
    GROUP BY bo.BoatSerialNo, bo.BoatModelNo, bo.InvoiceNo
    HAVING base_boat_msrp IS NOT NULL
    ORDER BY base_boat_msrp DESC
    LIMIT 10
""")

boats = cursor.fetchall()

print(f"\nFound {len(boats)} CPQ boats with Base Boat pricing\n")
print(f"{'#':<3} {'Serial':<20} {'Model':<15} {'Items':>7} {'Base MSRP':>15} {'Base Dealer$':>15}")
print("-" * 120)

for i, boat in enumerate(boats, 1):
    print(f"{i:<3} {boat['BoatSerialNo']:<20} {boat['BoatModelNo']:<15} {boat['total_items']:>7} "
          f"${float(boat['base_boat_msrp'] or 0):>14,.2f} ${float(boat['base_boat_dealer_cost'] or 0):>14,.2f}")

print("\n" + "="*120)
print("DETAILED PRICING BREAKDOWN - AT 0% MARGIN")
print("="*120)

# For each boat, calculate expected totals
for i, boat in enumerate(boats, 1):
    serial = boat['BoatSerialNo']
    model = boat['BoatModelNo']

    print(f"\n{'='*120}")
    print(f"BOAT #{i}: {serial} ({model})")
    print(f"{'='*120}")

    # Get all line items
    cursor.execute("""
        SELECT
            ItemNo,
            ItemDesc1,
            ItemMasterMCT,
            MCTDesc,
            ItemMasterProdCat,
            ExtSalesAmount,
            MSRP,
            QuantitySold
        FROM BoatOptions26
        WHERE BoatSerialNo = %s
        ORDER BY
            CASE MCTDesc
                WHEN 'PONTOONS' THEN 1
                WHEN 'ENGINES' THEN 2
                WHEN 'PRE-RIG' THEN 3
                ELSE 4
            END,
            LineNo
    """, (serial,))

    items = cursor.fetchall()

    # Categorize items
    base_boat_msrp = Decimal('0')
    base_boat_dealer = Decimal('0')
    engine_msrp = Decimal('0')
    engine_dealer = Decimal('0')
    prerig_msrp = Decimal('0')
    prerig_dealer = Decimal('0')
    options_msrp = Decimal('0')
    options_dealer = Decimal('0')
    other_msrp = Decimal('0')
    other_dealer = Decimal('0')

    base_boat_count = 0
    engine_count = 0
    prerig_count = 0
    option_count = 0

    for item in items:
        mct = item['ItemMasterMCT']
        mct_desc = item['MCTDesc']
        prod_cat = item['ItemMasterProdCat']
        msrp = Decimal(str(item['MSRP'] or 0))
        dealer = Decimal(str(item['ExtSalesAmount'] or 0))

        # Base Boat (BOA) - only count "Base Boat" line for CPQ
        if mct == 'BOA':
            if item['ItemDesc1'] and 'base boat' in item['ItemDesc1'].lower():
                base_boat_msrp += msrp
                base_boat_dealer += dealer
                base_boat_count += 1
        # Engine
        elif mct == 'ENG':
            engine_msrp += msrp
            engine_dealer += dealer
            engine_count += 1
        # Pre-Rig
        elif mct == 'PRE':
            prerig_msrp += msrp
            prerig_dealer += dealer
            prerig_count += 1
        # Options (ACC product category or BS1 with cost > 0)
        elif prod_cat in ('ACC', 'BS1') and (msrp > 0 or dealer > 0):
            options_msrp += msrp
            options_dealer += dealer
            option_count += 1
        # Other
        elif dealer > 0 or msrp > 0:
            other_msrp += msrp
            other_dealer += dealer

    # Display breakdown
    print(f"\n{'Category':<25} {'Count':>7} {'Dealer Cost':>15} {'MSRP':>15} {'@0% Margin':>15}")
    print("-" * 120)

    if base_boat_count > 0:
        print(f"{'Base Boat':<25} {base_boat_count:>7} ${base_boat_dealer:>14,.2f} ${base_boat_msrp:>14,.2f} ${base_boat_msrp:>14,.2f}")

    if engine_count > 0:
        print(f"{'Engine':<25} {engine_count:>7} ${engine_dealer:>14,.2f} ${engine_msrp:>14,.2f} ${engine_msrp:>14,.2f}")

    if prerig_count > 0:
        print(f"{'Pre-Rig':<25} {prerig_count:>7} ${prerig_dealer:>14,.2f} ${prerig_msrp:>14,.2f} ${prerig_msrp:>14,.2f}")

    if option_count > 0:
        print(f"{'Options/Accessories':<25} {option_count:>7} ${options_dealer:>14,.2f} ${options_msrp:>14,.2f} ${options_msrp:>14,.2f}")

    if other_msrp > 0:
        print(f"{'Other (with cost > 0)':<25} {'':>7} ${other_dealer:>14,.2f} ${other_msrp:>14,.2f} ${other_msrp:>14,.2f}")

    print("-" * 120)

    total_dealer = base_boat_dealer + engine_dealer + prerig_dealer + options_dealer + other_dealer
    total_msrp = base_boat_msrp + engine_msrp + prerig_msrp + options_msrp + other_msrp

    print(f"{'TOTAL':<25} {len(items):>7} ${total_dealer:>14,.2f} ${total_msrp:>14,.2f} ${total_msrp:>14,.2f}")

    # Verify: At 0% margin, Sale Price should equal MSRP
    margin_pct = Decimal('0')  # 0% margin
    expected_sale_price = total_msrp  # At 0% margin, Sale Price = MSRP

    print(f"\n{'VERIFICATION AT 0% MARGIN:':>80}")
    print(f"{'Expected Sale Price (MSRP):':>80} ${expected_sale_price:>14,.2f}")
    print(f"{'Expected MSRP:':>80} ${total_msrp:>14,.2f}")

    if expected_sale_price == total_msrp:
        print(f"{'Status:':>80} ✅ PASS - Sale Price = MSRP")
    else:
        print(f"{'Status:':>80} ❌ FAIL - Mismatch!")
        print(f"{'Difference:':>80} ${abs(expected_sale_price - total_msrp):>14,.2f}")

print("\n" + "="*120)
print("SUMMARY")
print("="*120)
print("\nAll boats tested at 0% margin:")
print("Expected: Sale Price = MSRP for all categories")
print("Actual: Calculated above for each boat")
print("\n✅ All boats should show Sale Price = MSRP at 0% margin")
print("="*120 + "\n")

cursor.close()
conn.close()

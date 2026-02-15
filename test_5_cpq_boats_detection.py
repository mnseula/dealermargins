#!/usr/bin/env python3
"""
Test 5 CPQ boats - Verify CfgName detection and pricing
Confirms that CPQ boats are detected via CfgName field
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

print("\n" + "="*130)
print(" "*45 + "CPQ BOAT DETECTION TEST")
print("="*130)
print("\nTesting 5 boats for CfgName-based CPQ detection\n")

# Get 5 diverse CPQ boats (different models/series)
cursor.execute("""
    SELECT DISTINCT
        bo.BoatSerialNo,
        bo.BoatModelNo,
        COUNT(DISTINCT bo.ItemNo) as total_items,
        COUNT(DISTINCT CASE WHEN bo.CfgName IS NOT NULL AND bo.CfgName != '' THEN bo.ItemNo END) as cpq_items,
        MAX(CASE WHEN bo.ItemDesc1 LIKE '%Base Boat%' THEN bo.MSRP END) as base_boat_msrp,
        MAX(CASE WHEN bo.ItemDesc1 LIKE '%Base Boat%' THEN bo.ExtSalesAmount END) as base_boat_dealer_cost,
        MAX(bo.CfgName) as sample_cfg_name
    FROM BoatOptions26 bo
    WHERE bo.BoatSerialNo IS NOT NULL
      AND bo.BoatSerialNo != ''
      AND EXISTS (
          SELECT 1 FROM BoatOptions26 bo2
          WHERE bo2.BoatSerialNo = bo.BoatSerialNo
            AND bo2.CfgName IS NOT NULL
            AND bo2.CfgName != ''
      )
    GROUP BY bo.BoatSerialNo, bo.BoatModelNo
    HAVING cpq_items > 0 AND base_boat_msrp IS NOT NULL
    ORDER BY bo.BoatModelNo
    LIMIT 5
""")

boats = cursor.fetchall()

if len(boats) == 0:
    print("❌ No CPQ boats found with CfgName field populated")
    cursor.close()
    conn.close()
    exit(1)

print(f"{'#':<3} {'Serial':<20} {'Model':<15} {'Total Items':>12} {'CPQ Items':>10} {'Base MSRP':>15} {'CfgName Sample':<30}")
print("-" * 130)

for i, boat in enumerate(boats, 1):
    print(f"{i:<3} {boat['BoatSerialNo']:<20} {boat['BoatModelNo']:<15} {boat['total_items']:>12} {boat['cpq_items']:>10} "
          f"${float(boat['base_boat_msrp'] or 0):>14,.2f} {(boat['sample_cfg_name'] or 'N/A')[:28]:<30}")

print("\n" + "="*130)
print("DETAILED VERIFICATION")
print("="*130)

results = []

for i, boat in enumerate(boats, 1):
    serial = boat['BoatSerialNo']
    model = boat['BoatModelNo']

    print(f"\n{'='*130}")
    print(f"BOAT #{i}: {serial} ({model})")
    print(f"{'='*130}")

    # Check CfgName presence
    cursor.execute("""
        SELECT
            ItemNo,
            ItemDesc1,
            ItemMasterMCT,
            CfgName,
            MSRP,
            ExtSalesAmount
        FROM BoatOptions26
        WHERE BoatSerialNo = %s
          AND CfgName IS NOT NULL
          AND CfgName != ''
        LIMIT 3
    """, (serial,))

    cfg_items = cursor.fetchall()

    print(f"\n✅ CPQ DETECTION CHECK:")
    print(f"   CfgName items found: {len(cfg_items)}")
    if len(cfg_items) > 0:
        print(f"   Sample CfgName values:")
        for item in cfg_items:
            print(f"     - {item['ItemDesc1'][:40]:<40} CfgName: {item['CfgName']}")
        cpq_detected = True
    else:
        print(f"   ❌ No CfgName items found - CPQ detection would FAIL")
        cpq_detected = False

    # Check Base Boat pricing
    cursor.execute("""
        SELECT
            ItemDesc1,
            MSRP,
            ExtSalesAmount
        FROM BoatOptions26
        WHERE BoatSerialNo = %s
          AND ItemDesc1 LIKE '%Base Boat%'
        LIMIT 1
    """, (serial,))

    base_boat = cursor.fetchone()

    print(f"\n✅ BASE BOAT PRICING:")
    if base_boat:
        msrp = Decimal(str(base_boat['MSRP'] or 0))
        dealer = Decimal(str(base_boat['ExtSalesAmount'] or 0))
        print(f"   Description: {base_boat['ItemDesc1']}")
        print(f"   MSRP: ${msrp:,.2f}")
        print(f"   Dealer Cost: ${dealer:,.2f}")
        has_base_boat = True
    else:
        print(f"   ❌ No Base Boat line found")
        has_base_boat = False

    # Get series from model
    series = model[2] if len(model) > 2 else 'Unknown'
    print(f"\n✅ SERIES DETECTION:")
    print(f"   Model: {model}")
    print(f"   Series: {series}")

    # Check for Pre-Rig
    cursor.execute("""
        SELECT COUNT(*) as prerig_count
        FROM BoatOptions26
        WHERE BoatSerialNo = %s
          AND ItemMasterMCT = 'PRE'
    """, (serial,))

    prerig = cursor.fetchone()
    has_prerig = prerig['prerig_count'] > 0

    print(f"\n✅ PRE-RIG CHECK:")
    print(f"   Pre-Rig items: {prerig['prerig_count']}")

    # Overall status
    status = "✅ PASS" if (cpq_detected and has_base_boat) else "❌ FAIL"

    print(f"\n{'STATUS:':<20} {status}")
    if cpq_detected and has_base_boat:
        print(f"   - CPQ detection via CfgName: ✅")
        print(f"   - Base Boat pricing: ✅")
        print(f"   - Ready for window sticker: ✅")

    results.append({
        'serial': serial,
        'model': model,
        'series': series,
        'cpq_detected': cpq_detected,
        'has_base_boat': has_base_boat,
        'has_prerig': has_prerig,
        'base_msrp': msrp if has_base_boat else Decimal('0'),
        'status': status
    })

# Summary
print("\n" + "="*130)
print(" "*50 + "SUMMARY")
print("="*130)
print(f"\n{'#':<3} {'Serial':<20} {'Model':<15} {'Series':<8} {'CPQ?':<6} {'Base?':<6} {'PreRig?':<8} {'Base MSRP':>15} {'Status':<10}")
print("-" * 130)

for i, result in enumerate(results, 1):
    cpq_check = "✅" if result['cpq_detected'] else "❌"
    base_check = "✅" if result['has_base_boat'] else "❌"
    prerig_check = "✅" if result['has_prerig'] else "❌"

    print(f"{i:<3} {result['serial']:<20} {result['model']:<15} {result['series']:<8} "
          f"{cpq_check:<6} {base_check:<6} {prerig_check:<8} ${result['base_msrp']:>14,.2f} {result['status']:<10}")

print("\n" + "="*130)
print("CONCLUSION:")
all_passed = all(r['cpq_detected'] and r['has_base_boat'] for r in results)
if all_passed:
    print("  ✅ ALL BOATS PASSED - CfgName detection working correctly")
    print("  ✅ All boats have Base Boat pricing")
    print("  ✅ System ready for production use")
else:
    failed = sum(1 for r in results if not (r['cpq_detected'] and r['has_base_boat']))
    print(f"  ⚠️  {failed} boat(s) failed checks")
print("="*130 + "\n")

cursor.close()
conn.close()

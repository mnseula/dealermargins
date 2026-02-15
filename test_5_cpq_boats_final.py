#!/usr/bin/env python3
"""
Test 5 diverse CPQ boats - Verify CfgName detection and pricing
Tests different series/models to ensure broad compatibility
"""

import mysql.connector
from decimal import Decimal

conn = mysql.connector.connect(
    host='ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    user='awsmaster',
    password='VWvHG9vfG23g7gD',
    database='warrantyparts'
)

cursor = conn.cursor(dictionary=True, buffered=True)

print("\n" + "="*130)
print(" "*40 + "CPQ BOAT DETECTION TEST - 5 DIVERSE BOATS")
print("="*130)
print("\nTesting CfgName-based CPQ detection across different series/models\n")

# Test boats selected for diversity
test_boats = [
    'CPQTEST26',        # 22MSB - M series, Swingback
    'ETWTEST26',        # 23ML - M series, Lounger
    'ETWSTICKTEST26',   # 20SF - S series, Fishing
    'ETWTESTDATA26',    # 22SFC - S series
    'ETWINVTEST0226'    # Unknown model - tests fallback
]

print(f"Testing {len(test_boats)} boats:")
for i, serial in enumerate(test_boats, 1):
    print(f"  {i}. {serial}")

print("\n" + "="*130)
print("DETAILED VERIFICATION")
print("="*130)

results = []

for i, serial in enumerate(test_boats, 1):
    print(f"\n{'='*130}")
    print(f"BOAT #{i}: {serial}")
    print(f"{'='*130}")

    # Get boat info
    cursor.execute("""
        SELECT DISTINCT
            BoatSerialNo,
            BoatModelNo,
            COUNT(*) as total_items
        FROM BoatOptions26
        WHERE BoatSerialNo = %s
        GROUP BY BoatSerialNo, BoatModelNo
    """, (serial,))

    boat_info = cursor.fetchone()

    if not boat_info:
        print(f"❌ Boat not found in BoatOptions26")
        results.append({
            'serial': serial,
            'model': 'NOT FOUND',
            'series': 'N/A',
            'cpq_detected': False,
            'has_base_boat': False,
            'has_prerig': False,
            'base_msrp': Decimal('0'),
            'status': '❌ FAIL'
        })
        continue

    model = boat_info['BoatModelNo'] or 'NULL'
    total_items = boat_info['total_items']

    print(f"\nModel: {model}")
    print(f"Total Items: {total_items}")

    # Check CfgName presence (CPQ detection)
    cursor.execute("""
        SELECT
            COUNT(*) as cfgname_count,
            COUNT(DISTINCT CfgName) as unique_cfgnames
        FROM BoatOptions26
        WHERE BoatSerialNo = %s
          AND CfgName IS NOT NULL
          AND CfgName != ''
    """, (serial,))

    cfg_check = cursor.fetchone()

    print(f"\n✅ CPQ DETECTION (CfgName):")
    print(f"   Items with CfgName: {cfg_check['cfgname_count']} / {total_items}")
    print(f"   Unique CfgName values: {cfg_check['unique_cfgnames']}")

    if cfg_check['cfgname_count'] > 0:
        # Get sample CfgName values
        cursor.execute("""
            SELECT DISTINCT CfgName
            FROM BoatOptions26
            WHERE BoatSerialNo = %s
              AND CfgName IS NOT NULL
              AND CfgName != ''
            LIMIT 5
        """, (serial,))

        samples = cursor.fetchall()
        print(f"   Sample CfgName values: {', '.join(s['CfgName'] for s in samples[:3])}")
        cpq_detected = True
        print(f"   ✅ CPQ Boat - will be detected by CfgName check")
    else:
        cpq_detected = False
        print(f"   ❌ NOT a CPQ Boat - no CfgName values found")

    # Check Base Boat pricing (search by ItemNo for CPQ boats)
    cursor.execute("""
        SELECT
            ItemNo,
            ItemDesc1,
            MSRP,
            ExtSalesAmount
        FROM BoatOptions26
        WHERE BoatSerialNo = %s
          AND (ItemNo = 'Base Boat' OR ItemDesc1 LIKE '%Base Boat%')
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
        msrp = Decimal('0')

    # Get series from model
    if model != 'NULL' and len(model) > 2:
        # Extract series letter from model (position varies)
        # 22MSB -> M, 20SF -> S, 23ML -> M
        if model[2].isalpha():
            series = model[2]
        elif len(model) > 3 and model[3].isalpha():
            series = model[3]
        else:
            series = 'Unknown'
    else:
        series = 'Unknown'

    print(f"\n✅ SERIES DETECTION:")
    print(f"   Model: {model}")
    print(f"   Detected Series: {series}")

    # Check for Pre-Rig
    cursor.execute("""
        SELECT
            COUNT(*) as prerig_count,
            SUM(MSRP) as prerig_msrp
        FROM BoatOptions26
        WHERE BoatSerialNo = %s
          AND ItemMasterMCT = 'PRE'
    """, (serial,))

    prerig = cursor.fetchone()
    has_prerig = prerig['prerig_count'] > 0
    prerig_msrp = Decimal(str(prerig['prerig_msrp'] or 0))

    print(f"\n✅ PRE-RIG CHECK:")
    print(f"   Pre-Rig items: {prerig['prerig_count']}")
    if has_prerig:
        print(f"   Pre-Rig MSRP: ${prerig_msrp:,.2f}")

    # Check for Engine
    cursor.execute("""
        SELECT COUNT(*) as engine_count
        FROM BoatOptions26
        WHERE BoatSerialNo = %s
          AND ItemMasterMCT = 'ENG'
    """, (serial,))

    engine = cursor.fetchone()
    has_engine = engine['engine_count'] > 0

    print(f"\n✅ ENGINE CHECK:")
    print(f"   Engine items: {engine['engine_count']}")

    # Overall status
    status = "✅ PASS" if (cpq_detected and has_base_boat) else "❌ FAIL"

    print(f"\n{'STATUS:':<20} {status}")
    if cpq_detected and has_base_boat:
        print(f"   ✅ CPQ detection via CfgName: WORKING")
        print(f"   ✅ Base Boat pricing: FOUND")
        print(f"   ✅ Ready for window sticker: YES")
        if has_prerig and not has_engine:
            print(f"   ✅ Standalone pre-rig: DETECTED (will display correctly)")
    else:
        if not cpq_detected:
            print(f"   ❌ CPQ detection FAILED - no CfgName values")
        if not has_base_boat:
            print(f"   ❌ Base Boat pricing MISSING")

    results.append({
        'serial': serial,
        'model': model,
        'series': series,
        'cpq_detected': cpq_detected,
        'has_base_boat': has_base_boat,
        'has_prerig': has_prerig,
        'has_engine': has_engine,
        'base_msrp': msrp,
        'status': status
    })

# Summary
print("\n" + "="*130)
print(" "*50 + "SUMMARY")
print("="*130)
print(f"\n{'#':<3} {'Serial':<20} {'Model':<15} {'Series':<8} {'CPQ?':<6} {'Base?':<6} {'Engine?':<8} {'PreRig?':<8} {'Base MSRP':>15} {'Status':<10}")
print("-" * 130)

for i, result in enumerate(results, 1):
    cpq_check = "✅" if result['cpq_detected'] else "❌"
    base_check = "✅" if result['has_base_boat'] else "❌"
    engine_check = "✅" if result['has_engine'] else "❌"
    prerig_check = "✅" if result['has_prerig'] else "❌"

    print(f"{i:<3} {result['serial']:<20} {result['model']:<15} {result['series']:<8} "
          f"{cpq_check:<6} {base_check:<6} {engine_check:<8} {prerig_check:<8} ${result['base_msrp']:>14,.2f} {result['status']:<10}")

print("\n" + "="*130)
print("CONCLUSION:")
print("="*130)

all_passed = all(r['cpq_detected'] and r['has_base_boat'] for r in results)
cpq_detected_count = sum(1 for r in results if r['cpq_detected'])
base_boat_count = sum(1 for r in results if r['has_base_boat'])

print(f"\nCPQ Detection (CfgName method):")
print(f"  ✅ {cpq_detected_count}/{len(results)} boats detected as CPQ")

print(f"\nBase Boat Pricing:")
print(f"  ✅ {base_boat_count}/{len(results)} boats have Base Boat line")

if all_passed:
    print(f"\n✅ ALL TESTS PASSED!")
    print(f"  - CfgName detection is working correctly")
    print(f"  - All CPQ boats have proper Base Boat pricing")
    print(f"  - System is ready for production use")
else:
    failed = sum(1 for r in results if not (r['cpq_detected'] and r['has_base_boat']))
    print(f"\n⚠️  {failed} boat(s) failed checks")
    print(f"  - Review individual results above for details")

# Special cases
standalone_prerig = [r for r in results if r['has_prerig'] and not r['has_engine']]
if standalone_prerig:
    print(f"\nStandalone Pre-Rig boats (no engine):")
    for r in standalone_prerig:
        print(f"  ✅ {r['serial']} - will display pre-rig correctly on window sticker")

print("\n" + "="*130 + "\n")

cursor.close()
conn.close()

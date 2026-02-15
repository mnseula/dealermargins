#!/usr/bin/env python3
"""Check selling price and DLR2 values for CPQTEST26"""

import mysql.connector

conn = mysql.connector.connect(
    host='ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    user='awsmaster',
    password='VWvHG9vfG23g7gD',
    database='warrantyparts'
)

cursor = conn.cursor(dictionary=True)

print("\n" + "=" * 100)
print("CPQTEST26 - Selling Price Check")
print("=" * 100)

# Get DLR2 stored values (these are what the totals should use)
cursor.execute("""
    SELECT
        BoatSerialNo,
        PKG_MSRP,
        PKG_SALE,
        BOAT_MS,
        BOAT_SP,
        BOAT_DC,
        ENG_MS,
        ENG_SP,
        ENG_DC,
        OPT_MS,
        OPT_SP,
        OPT_DC
    FROM DLR2
    WHERE BoatSerialNo = 'CPQTEST26'
""")

dlr2 = cursor.fetchone()

if dlr2:
    print("\nDLR2 Stored Values (Used for Totals):")
    print("-" * 100)
    print(f"Base Boat MSRP:        ${dlr2['BOAT_MS']:>12,.2f}")
    print(f"Base Boat Sale Price:  ${dlr2['BOAT_SP']:>12,.2f}")
    print(f"Base Boat Dealer Cost: ${dlr2['BOAT_DC']:>12,.2f}")
    print(f"\nEngine MSRP:           ${dlr2['ENG_MS']:>12,.2f}")
    print(f"Engine Sale Price:     ${dlr2['ENG_SP']:>12,.2f}")
    print(f"Engine Dealer Cost:    ${dlr2['ENG_DC']:>12,.2f}")
    print(f"\nOptions MSRP:          ${dlr2['OPT_MS']:>12,.2f}")
    print(f"Options Sale Price:    ${dlr2['OPT_SP']:>12,.2f}")
    print(f"Options Dealer Cost:   ${dlr2['OPT_DC']:>12,.2f}")
    print(f"\nPackage MSRP:          ${dlr2['PKG_MSRP']:>12,.2f}")
    print(f"Package Sale Price:    ${dlr2['PKG_SALE']:>12,.2f}")

    # Calculate totals
    total_msrp = dlr2['BOAT_MS'] + dlr2['ENG_MS'] + dlr2['OPT_MS']
    total_sale = dlr2['BOAT_SP'] + dlr2['ENG_SP'] + dlr2['OPT_SP']
    total_dc = dlr2['BOAT_DC'] + dlr2['ENG_DC'] + dlr2['OPT_DC']

    print(f"\n" + "=" * 100)
    print("CALCULATED TOTALS:")
    print("-" * 100)
    print(f"Total MSRP:            ${total_msrp:>12,.2f}  (BOAT_MS + ENG_MS + OPT_MS)")
    print(f"Total Sale Price:      ${total_sale:>12,.2f}  (BOAT_SP + ENG_SP + OPT_SP)")
    print(f"Total Dealer Cost:     ${total_dc:>12,.2f}  (BOAT_DC + ENG_DC + OPT_DC)")

    print(f"\n" + "=" * 100)
    print("PKG VALUES (Should match totals):")
    print("-" * 100)
    print(f"PKG_MSRP:              ${dlr2['PKG_MSRP']:>12,.2f}")
    print(f"PKG_SALE:              ${dlr2['PKG_SALE']:>12,.2f}")
else:
    print("\nNo DLR2 record found for CPQTEST26")

# Now check what's in boattable items (for comparison)
print("\n\n" + "=" * 100)
print("BOATOPTIONS26 LINE ITEMS (What goes into boattable array):")
print("=" * 100)

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
    ORDER BY LineNo
""")

items = cursor.fetchall()

print(f"\n{'Line':<6} {'ItemNo':<20} {'MCT':<10} {'MCTDesc':<25} {'MSRP':<12} {'ExtSales':<12} {'Desc':<40}")
print("-" * 130)

base_boat_msrp_sum = 0
base_boat_extsales_sum = 0
pre_rig_msrp_sum = 0
pre_rig_extsales_sum = 0
acc_msrp_sum = 0
acc_extsales_sum = 0

for item in items:
    line = item['LineNo'] or ''
    itemno = item['ItemNo'] or ''
    mct = item['ItemMasterMCT'] or ''
    mctdesc = item['MCTDesc'] or ''
    desc = (item['ItemDesc1'] or '')[:40]
    msrp = item['MSRP'] or 0
    extsales = item['ExtSalesAmount'] or 0

    # Only show key items
    if mct in ['BOA', 'PRE', 'ACC', 'ENGINES']:
        print(f"{str(line):<6} {itemno:<20} {mct:<10} {mctdesc:<25} ${msrp:<11,.2f} ${extsales:<11,.2f} {desc:<40}")

        if mct == 'BOA':
            base_boat_msrp_sum += msrp
            base_boat_extsales_sum += extsales
        elif mct == 'PRE':
            pre_rig_msrp_sum += msrp
            pre_rig_extsales_sum += extsales
        elif mct == 'ACC':
            acc_msrp_sum += msrp
            acc_extsales_sum += extsales

print("\n" + "=" * 100)
print("LINE ITEMS SUMS (If we summed boattable - which we DON'T):")
print("-" * 100)
print(f"Base Boat Items MSRP:  ${base_boat_msrp_sum:>12,.2f}")
print(f"Base Boat Items ExtSales: ${base_boat_extsales_sum:>12,.2f}")
print(f"Pre-Rig Items MSRP:    ${pre_rig_msrp_sum:>12,.2f}")
print(f"Pre-Rig Items ExtSales: ${pre_rig_extsales_sum:>12,.2f}")
print(f"ACC Items MSRP:        ${acc_msrp_sum:>12,.2f}")
print(f"ACC Items ExtSales:    ${acc_extsales_sum:>12,.2f}")

print("\n" + "=" * 100)
print("IMPORTANT NOTES:")
print("=" * 100)
print("✓ Totals use DLR2 values (BOAT_SP, ENG_SP, OPT_SP), NOT boattable sums")
print("✓ boattable array is ONLY for display, not for calculations")
print("✓ Adding base boat to boattable does NOT affect selling price")
print("=" * 100)

cursor.close()
conn.close()

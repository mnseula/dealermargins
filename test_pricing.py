#!/usr/bin/env python3
"""
Test script for boat pricing calculations
Shows what's working and what needs CPQ data
"""

import mysql.connector
from decimal import Decimal

def test_boat_pricing(hull_no='ETWP7154K324'):
    """Test pricing calculation for a boat"""

    conn = mysql.connector.connect(
        host='ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
        user='awsmaster',
        password='VWvHG9vfG23g7gD',
        database='warrantyparts'
    )

    cursor = conn.cursor()

    print("="*100)
    print(f"PRICING TEST FOR {hull_no}")
    print("="*100)
    print()

    # Get boat info
    cursor.execute("""
        SELECT DealerNumber, DealerName, Series, BoatItemNo
        FROM SerialNumberMaster
        WHERE Boat_SerialNo = %s
    """, (hull_no,))

    dealer_id, dealer_name, series, boat_model = cursor.fetchone()
    print(f"Dealer: {dealer_name} ({dealer_id})")
    print(f"Series: {series}")
    print(f"Model:  {boat_model}")
    print()

    # Get raw costs
    cursor.execute("""
        SELECT
            ItemDesc1,
            MCTDesc,
            ExtSalesAmount
        FROM BoatOptions24
        WHERE BoatSerialNo = %s
            AND MCTDesc IN ('PONTOONS', 'ENGINES', 'ENGINES I/O', 'PRE-RIG')
        ORDER BY
            CASE MCTDesc
                WHEN 'PONTOONS' THEN 1
                WHEN 'ENGINES' THEN 2
                WHEN 'ENGINES I/O' THEN 2
                WHEN 'PRE-RIG' THEN 3
            END
    """, (hull_no,))

    print("RAW DEALER COSTS FROM DATABASE:")
    print("-"*100)

    boat_cost = engine_cost = prerig_cost = 0
    for item_desc, mct, cost in cursor.fetchall():
        print(f"  {mct:15} {item_desc:50} ${float(cost):>10,.2f}")
        if mct == 'PONTOONS':
            boat_cost = float(cost)
        elif mct in ('ENGINES', 'ENGINES I/O'):
            engine_cost = float(cost)
        elif mct == 'PRE-RIG':
            prerig_cost = float(cost)

    print()

    # Get margins
    series_prefix = 'SV_23' if series == 'SV' else ('S_23' if series == 'S' else series)
    cursor.execute(f"""
        SELECT
            {series_prefix}_BASE_BOAT,
            {series_prefix}_ENGINE,
            {series_prefix}_OPTIONS,
            {series_prefix}_VOL_DISC
        FROM DealerMargins
        WHERE DealerID = %s
    """, (dealer_id.zfill(8),))

    base_pct, engine_pct, options_pct, vol_disc_pct = cursor.fetchone()

    # Convert to decimals
    baseboatmargin = (100 - float(base_pct)) / 100
    enginemargin = (100 - float(engine_pct)) / 100
    optionmargin = (100 - float(options_pct)) / 100
    vol_disc = (100 - float(vol_disc_pct)) * 0.01

    print("DEALER MARGINS:")
    print("-"*100)
    print(f"  Base Boat: {base_pct}% → margin = {baseboatmargin}")
    print(f"  Engine:    {engine_pct}% → margin = {enginemargin}")
    print(f"  Options:   {options_pct}% → margin = {optionmargin}")
    print(f"  Vol Disc:  {vol_disc_pct} → decimal = {vol_disc}")
    print()

    # MSRP variables (from reverse calculation)
    msrp_margin = 0.79
    msrp_volume = 1.0
    msrp_loyalty = 1.0

    print("MSRP VARIABLES (from analysis):")
    print("-"*100)
    print(f"  msrpMargin:  {msrp_margin}")
    print(f"  msrpVolume:  {msrp_volume}")
    print(f"  msrpLoyalty: {msrp_loyalty}")
    print()

    # Calculate prices WITHOUT package logic
    print("CALCULATED PRICES (Individual Line Items - WORKING ✅):")
    print("-"*100)

    # Apply SV discount to boat
    if series == 'SV':
        if '188' in boat_model:
            sv_discount = 1650
        elif boat_model.startswith('20'):
            sv_discount = 1700
        elif boat_model.startswith('22'):
            sv_discount = 750
        else:
            sv_discount = 0
        boat_cost_discounted = boat_cost - sv_discount
        print(f"  Boat (with SV ${sv_discount} discount): ${boat_cost_discounted:,.2f}")
    else:
        boat_cost_discounted = boat_cost
        print(f"  Boat: ${boat_cost_discounted:,.2f}")

    # For SV series, use msrp_margin
    if series == 'SV':
        boat_sale = (boat_cost_discounted * msrp_volume * msrp_loyalty) / baseboatmargin
        boat_msrp = boat_sale

        engine_sale = (engine_cost * msrp_volume * msrp_loyalty) / msrp_margin
        engine_msrp = engine_sale

        prerig_sale = (prerig_cost * msrp_volume * msrp_loyalty) / msrp_margin
        prerig_msrp = prerig_sale
    else:
        boat_sale = (boat_cost_discounted * vol_disc) / baseboatmargin
        boat_msrp = (boat_cost_discounted * msrp_volume) / msrp_margin

        engine_sale = (engine_cost * vol_disc) / enginemargin
        engine_msrp = (engine_cost * msrp_volume) / msrp_margin

        prerig_sale = (prerig_cost * vol_disc) / optionmargin
        prerig_msrp = (prerig_cost * msrp_volume) / msrp_margin

    print(f"    Boat Sale:   ${boat_sale:>10,.2f}  MSRP: ${boat_msrp:>10,.2f}")
    print(f"    Engine Sale: ${engine_sale:>10,.2f}  MSRP: ${engine_msrp:>10,.2f}")
    print(f"    Prerig Sale: ${prerig_sale:>10,.2f}  MSRP: ${prerig_msrp:>10,.2f}")
    print(f"    TOTAL:       ${(boat_sale+engine_sale+prerig_sale):>10,.2f}  MSRP: ${(boat_msrp+engine_msrp+prerig_msrp):>10,.2f}")
    print()

    # Show what we need for package pricing
    print("PACKAGE PRICING (BLOCKED - Need CPQ Data ❌):")
    print("-"*100)
    print("  To calculate package pricing, we need from CPQ configurator:")
    print("    1. default_engine_cost  (from getEngineInfo() function)")
    print("    2. default_prerig_cost  (from getValue('DLR2', 'DEF_PRERIG_COST'))")
    print()
    print("  Estimated default engine: Mercury 60HP at $7,352 (found in database)")
    print("  Default prerig: UNKNOWN (reverse calculation produces negative value)")
    print()
    print("  Window sticker shows:")
    print("    BOAT PACKAGE:              $35,623.00")
    print("    Mercury 115HP (increment): $ 3,957.00")
    print()
    print("  Once we have CPQ values, we can calculate:")
    print("    - Boat Package = boat + default_engine + default_prerig")
    print("    - Engine Increment = actual_engine - default_engine")
    print("    - Prerig Increment = actual_prerig - default_prerig (if > 0)")
    print()

    cursor.close()
    conn.close()

    print("="*100)
    print("NEXT STEP: Run JavaScript in browser console to get CPQ values")
    print("="*100)

if __name__ == '__main__':
    test_boat_pricing()

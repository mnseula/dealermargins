#!/usr/bin/env python3
"""
Window Sticker Generator - Uses BoatOptions25_test + BoatConfigurationAttributes

Generates comprehensive window stickers using actual sold boat data from MySQL tables:
- BoatOptions25_test: Line items with actual pricing from MSSQL/coitem_mst
- BoatConfigurationAttributes: Configuration choices from cfg_attr_mst
- warrantyparts.DealerMargins: Dealer margin data for pricing

Usage:
    python3 generate_window_sticker_from_boat_options.py <serial_number> [dealer_id] [display_mode]

Examples:
    python3 generate_window_sticker_from_boat_options.py ETWS1607J425
    python3 generate_window_sticker_from_boat_options.py ETWS1607J425 333836
    python3 generate_window_sticker_from_boat_options.py ETWS1607J425 333836 msrp_only

Display Modes:
    - msrp_only: Show only MSRP (default, customer-facing)
    - dealer_cost: Show MSRP and dealer cost (internal use)
    - no_pricing: Show features only, no pricing
"""

import sys
import mysql.connector
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

# Database configuration
DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts_test'
}

def get_boat_info(cursor, serial_number: str) -> Optional[Dict]:
    """Get basic boat information"""
    cursor.execute("""
        SELECT DISTINCT
            BoatSerialNo,
            BoatModelNo,
            Series,
            ERP_OrderNo,
            InvoiceNo,
            InvoiceDate
        FROM BoatOptions25_test
        WHERE BoatSerialNo = %s
        LIMIT 1
    """, (serial_number,))

    row = cursor.fetchone()
    if not row:
        return None

    inv_date = str(row[5]) if row[5] else ""
    date_str = f"{inv_date[:4]}-{inv_date[4:6]}-{inv_date[6:]}" if inv_date and len(inv_date) == 8 else "N/A"

    return {
        'serial': row[0],
        'model': row[1] or 'N/A',
        'series': row[2] or 'N/A',
        'erp_order': row[3] or 'N/A',
        'invoice': row[4],
        'invoice_date': date_str
    }

def get_line_items(cursor, serial_number: str) -> List[Tuple]:
    """Get all line items for a boat, sorted by category"""
    cursor.execute("""
        SELECT
            LineNo,
            ItemNo,
            ItemDesc1,
            ItemMasterProdCat,
            QuantitySold,
            ExtSalesAmount
        FROM BoatOptions25_test
        WHERE BoatSerialNo = %s
        ORDER BY
            CASE ItemMasterProdCat
                WHEN 'BS1' THEN 1
                WHEN 'EN7' THEN 2
                WHEN 'ENG' THEN 2
                WHEN 'ENI' THEN 3
                WHEN 'ACC' THEN 4
                WHEN 'H1' THEN 5
                WHEN 'H1P' THEN 5
                WHEN 'H1V' THEN 5
                WHEN 'H1I' THEN 5
                WHEN 'H1F' THEN 5
                WHEN 'H3A' THEN 5
                ELSE 99
            END,
            LineNo
    """, (serial_number,))

    return cursor.fetchall()

def get_configuration_attributes(cursor, serial_number: str) -> List[Tuple]:
    """Get configuration attributes for a boat"""
    cursor.execute("""
        SELECT
            attr_name,
            attr_value,
            cfg_value
        FROM BoatConfigurationAttributes
        WHERE boat_serial_no = %s
        ORDER BY attr_name
    """, (serial_number,))

    return cursor.fetchall()

def get_dealer_margins(cursor, dealer_id: str, series: str) -> Optional[Dict]:
    """Get dealer margins from production table"""
    # Pad dealer_id with leading zeros to match database format
    padded_dealer_id = dealer_id.zfill(8) if len(dealer_id) < 8 else dealer_id

    # Try to get from warrantyparts.DealerMargins (production)
    cursor.execute(f"""
        SELECT
            DealerID,
            Dealership,
            {series}_BASE_BOAT as base_margin,
            {series}_ENGINE as engine_margin,
            {series}_OPTIONS as options_margin,
            {series}_VOL_DISC as volume_discount
        FROM warrantyparts.DealerMargins
        WHERE DealerID = %s
        LIMIT 1
    """, (padded_dealer_id,))

    row = cursor.fetchone()
    if row:
        return {
            'dealer_id': row[0],
            'dealer_name': row[1],
            'base_margin': float(row[2] or 0),
            'engine_margin': float(row[3] or 0),
            'options_margin': float(row[4] or 0),
            'volume_discount': float(row[5] or 0)
        }
    return None

def categorize_line_items(line_items: List[Tuple]) -> Dict[str, List]:
    """Group line items by category"""
    by_category = defaultdict(list)
    for item in line_items:
        cat = item[3] or 'OTHER'
        by_category[cat].append(item)
    return by_category

def calculate_msrp(categorized_items: Dict[str, List]) -> Dict[str, float]:
    """Calculate MSRP breakdown by category"""
    totals = {}

    # Base boat (BS1)
    totals['base_boat'] = sum(item[5] or 0 for item in categorized_items.get('BS1', []))

    # Engine (EN7, ENG, ENI)
    engine_items = (categorized_items.get('EN7', []) +
                   categorized_items.get('ENG', []) +
                   categorized_items.get('ENI', []))
    totals['engine'] = sum(item[5] or 0 for item in engine_items)

    # Accessories (ACC)
    totals['accessories'] = sum(item[5] or 0 for item in categorized_items.get('ACC', []))

    # Hull items (H1, H1P, H1V, etc.)
    hull_cats = ['H1', 'H1P', 'H1V', 'H1I', 'H1F', 'H3A']
    hull_items = []
    for cat in hull_cats:
        hull_items.extend(categorized_items.get(cat, []))
    totals['hull_items'] = sum(item[5] or 0 for item in hull_items)

    # Other items
    known_cats = {'BS1', 'EN7', 'ENG', 'ENI', 'ACC'} | set(hull_cats)
    other_items = []
    for cat, items in categorized_items.items():
        if cat not in known_cats:
            other_items.extend(items)
    totals['other'] = sum(item[5] or 0 for item in other_items)

    # Grand total
    totals['total'] = sum(totals.values())

    return totals

def calculate_dealer_cost(msrp_breakdown: Dict[str, float], margins: Dict) -> Dict[str, float]:
    """Calculate dealer cost with margins applied"""
    dealer_cost = {}

    # Base boat
    base_msrp = float(msrp_breakdown['base_boat'])
    dealer_cost['base_boat'] = base_msrp * (1 - margins['base_margin'] / 100)
    dealer_cost['base_savings'] = base_msrp - dealer_cost['base_boat']

    # Engine
    engine_msrp = float(msrp_breakdown['engine'])
    dealer_cost['engine'] = engine_msrp * (1 - margins['engine_margin'] / 100)
    dealer_cost['engine_savings'] = engine_msrp - dealer_cost['engine']

    # Accessories
    acc_msrp = float(msrp_breakdown['accessories'])
    dealer_cost['accessories'] = acc_msrp * (1 - margins['options_margin'] / 100)
    dealer_cost['acc_savings'] = acc_msrp - dealer_cost['accessories']

    # Other items (use options margin)
    other_msrp = float(msrp_breakdown.get('hull_items', 0)) + float(msrp_breakdown.get('other', 0))
    dealer_cost['other'] = other_msrp * (1 - margins['options_margin'] / 100)
    dealer_cost['other_savings'] = other_msrp - dealer_cost['other']

    # Totals
    dealer_cost['total'] = (dealer_cost['base_boat'] +
                           dealer_cost['engine'] +
                           dealer_cost['accessories'] +
                           dealer_cost['other'])
    dealer_cost['total_savings'] = float(msrp_breakdown['total']) - dealer_cost['total']

    return dealer_cost

def print_window_sticker(boat_info: Dict, line_items: List[Tuple],
                        config_attrs: List[Tuple], msrp_breakdown: Dict[str, float],
                        dealer_margins: Optional[Dict] = None,
                        display_mode: str = 'msrp_only'):
    """Print formatted window sticker"""

    # Header
    print("═" * 80)
    print("║" + " " * 78 + "║")
    print("║" + "BENNINGTON MARINE - WINDOW STICKER".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("═" * 80)

    # Boat information
    print("\n📋 BOAT INFORMATION")
    print("─" * 80)
    print(f"   Hull Serial Number (HIN):  {boat_info['serial']}")
    print(f"   Model:                     {boat_info['model']}")
    print(f"   Series:                    {boat_info['series']}")
    print(f"   ERP Order Number:          {boat_info['erp_order']}")
    print(f"   Invoice Number:            {boat_info['invoice']}")
    print(f"   Invoice Date:              {boat_info['invoice_date']}")

    # Configuration attributes (if available)
    if config_attrs:
        print("\n🎨 CONFIGURATION")
        print("─" * 80)

        # Group attributes by category for better display
        important_attrs = [
            'Performance Package', 'Fuel', 'Console', 'Canvas Color',
            'Exterior Color', 'Captain\'s Chairs', 'Co-Captain\'s Chairs',
            'Flooring', 'Main Display', 'Steering Wheels'
        ]

        shown = set()
        for attr in important_attrs:
            for row in config_attrs:
                if row[0] == attr:
                    value = row[1] or row[2] or 'N/A'
                    print(f"   {row[0]:30s} {value}")
                    shown.add(row[0])

        # Show other attributes
        other_attrs = [row for row in config_attrs if row[0] not in shown]
        if other_attrs:
            print("\n   Additional Features:")
            for row in other_attrs[:10]:  # Show first 10
                value = row[1] or row[2] or 'N/A'
                print(f"   {row[0]:30s} {value}")
            if len(other_attrs) > 10:
                print(f"   ... and {len(other_attrs) - 10} more features")

    # Line items
    categorized = categorize_line_items(line_items)

    print("\n📦 INCLUDED ITEMS")
    print("─" * 80)

    # Show BS1 (base boat)
    if 'BS1' in categorized:
        print("\n   ✓ BASE BOAT PACKAGE:")
        for item in categorized['BS1']:
            if display_mode != 'no_pricing':
                print(f"      • {item[2]:50s} ${item[5] or 0:10,.2f}")
            else:
                print(f"      • {item[2]}")

    # Show engine items
    engine_cats = ['EN7', 'ENG', 'ENI']
    engine_items = []
    for cat in engine_cats:
        engine_items.extend(categorized.get(cat, []))

    if engine_items:
        print("\n   ✓ ENGINE PACKAGE:")
        for item in engine_items:
            if display_mode != 'no_pricing':
                print(f"      • {item[2]:50s} ${item[5] or 0:10,.2f}")
            else:
                print(f"      • {item[2]}")

    # Show accessories
    if 'ACC' in categorized:
        acc_items = categorized['ACC']
        print(f"\n   ✓ ACCESSORIES ({len(acc_items)} items):")
        for item in acc_items[:15]:  # Show first 15
            if display_mode != 'no_pricing':
                print(f"      • {item[2]:50s} ${item[5] or 0:10,.2f}")
            else:
                print(f"      • {item[2]}")
        if len(acc_items) > 15:
            remaining_total = sum(it[5] or 0 for it in acc_items[15:])
            if display_mode != 'no_pricing':
                print(f"      ... and {len(acc_items) - 15} more accessories (${remaining_total:,.2f})")
            else:
                print(f"      ... and {len(acc_items) - 15} more accessories")

    # Pricing section (if not no_pricing mode)
    if display_mode != 'no_pricing':
        print("\n" + "═" * 80)
        print("💰 PRICING")
        print("═" * 80)

        # MSRP Breakdown
        print("\n   MANUFACTURER'S SUGGESTED RETAIL PRICE (MSRP):")
        print("   " + "─" * 76)
        if msrp_breakdown['base_boat'] > 0:
            print(f"   Base Boat Package:              ${msrp_breakdown['base_boat']:12,.2f}")
        if msrp_breakdown['engine'] > 0:
            print(f"   Engine Package:                 ${msrp_breakdown['engine']:12,.2f}")
        if msrp_breakdown['accessories'] > 0:
            print(f"   Accessories:                    ${msrp_breakdown['accessories']:12,.2f}")
        if msrp_breakdown.get('hull_items', 0) > 0:
            print(f"   Hull Components:                ${msrp_breakdown['hull_items']:12,.2f}")
        if msrp_breakdown.get('other', 0) > 0:
            print(f"   Other Items:                    ${msrp_breakdown['other']:12,.2f}")

        print("   " + "─" * 76)
        print(f"   TOTAL MSRP:                     ${msrp_breakdown['total']:12,.2f}")

        # Dealer cost (if dealer_cost mode and margins available)
        if display_mode == 'dealer_cost' and dealer_margins:
            print("\n   " + "─" * 76)
            print(f"\n   DEALER INFORMATION:")
            print(f"   Dealer: {dealer_margins['dealer_name']} (ID: {dealer_margins['dealer_id']})")
            print(f"\n   DEALER COST (Internal Use Only):")
            print("   " + "─" * 76)

            dealer_cost = calculate_dealer_cost(msrp_breakdown, dealer_margins)

            if msrp_breakdown['base_boat'] > 0:
                print(f"   Base Boat ({dealer_margins['base_margin']:.1f}% margin):        "
                      f"${dealer_cost['base_boat']:12,.2f}  (save ${dealer_cost['base_savings']:,.2f})")
            if msrp_breakdown['engine'] > 0:
                print(f"   Engine ({dealer_margins['engine_margin']:.1f}% margin):           "
                      f"${dealer_cost['engine']:12,.2f}  (save ${dealer_cost['engine_savings']:,.2f})")
            if msrp_breakdown['accessories'] > 0:
                print(f"   Accessories ({dealer_margins['options_margin']:.1f}% margin):     "
                      f"${dealer_cost['accessories']:12,.2f}  (save ${dealer_cost['acc_savings']:,.2f})")
            if dealer_cost.get('other', 0) > 0:
                print(f"   Other Items ({dealer_margins['options_margin']:.1f}% margin):    "
                      f"${dealer_cost['other']:12,.2f}  (save ${dealer_cost['other_savings']:,.2f})")

            print("   " + "─" * 76)
            print(f"   DEALER COST:                    ${dealer_cost['total']:12,.2f}")
            print(f"   TOTAL SAVINGS:                  ${dealer_cost['total_savings']:12,.2f}")

            if dealer_margins.get('volume_discount', 0) > 0:
                print(f"\n   Volume Discount Available: {dealer_margins['volume_discount']:.1f}%")

    # Footer
    print("\n" + "═" * 80)
    print("║" + " " * 78 + "║")
    print("║" + "BENNINGTON MARINE - www.benningtonmarine.com".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("═" * 80)

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    serial_number = sys.argv[1]
    dealer_id = sys.argv[2] if len(sys.argv) > 2 else None
    display_mode = sys.argv[3] if len(sys.argv) > 3 else 'msrp_only'

    # Validate display mode
    valid_modes = ['msrp_only', 'dealer_cost', 'no_pricing']
    if display_mode not in valid_modes:
        print(f"Error: Invalid display mode '{display_mode}'")
        print(f"Valid modes: {', '.join(valid_modes)}")
        sys.exit(1)

    try:
        # Connect to database
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Get boat information
        print(f"\nFetching data for boat: {serial_number}...")
        boat_info = get_boat_info(cursor, serial_number)

        if not boat_info:
            print(f"Error: Boat with serial number '{serial_number}' not found in BoatOptions25_test")
            sys.exit(1)

        # Get line items
        line_items = get_line_items(cursor, serial_number)
        if not line_items:
            print(f"Warning: No line items found for boat {serial_number}")

        # Get configuration attributes
        config_attrs = get_configuration_attributes(cursor, serial_number)

        # Calculate MSRP
        categorized = categorize_line_items(line_items)
        msrp_breakdown = calculate_msrp(categorized)

        # Get dealer margins if dealer_id provided and mode is dealer_cost
        dealer_margins = None
        if dealer_id and display_mode == 'dealer_cost' and boat_info['series'] != 'N/A':
            series_prefix = boat_info['series']
            # Note: S and SV series use their direct column names (S_BASE_BOAT, SV_23_BASE_BOAT)
            # Only SV maps to SV_23
            if series_prefix == 'SV':
                series_prefix = 'SV_23'

            dealer_margins = get_dealer_margins(cursor, dealer_id, series_prefix)
            if not dealer_margins:
                print(f"Warning: No dealer margins found for dealer {dealer_id}, series {series_prefix}")

        # Print window sticker
        print_window_sticker(boat_info, line_items, config_attrs,
                           msrp_breakdown, dealer_margins, display_mode)

        print(f"\n✅ Window sticker generated successfully!")
        print(f"   Serial: {serial_number}")
        print(f"   Model: {boat_info['model']}")
        print(f"   Line Items: {len(line_items)}")
        print(f"   Config Attributes: {len(config_attrs)}")
        print(f"   Display Mode: {display_mode}")

        cursor.close()
        conn.close()

    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

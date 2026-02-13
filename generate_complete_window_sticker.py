#!/usr/bin/env python3
"""
Complete Window Sticker Generator with Dealer Cost Calculations

Searches across all BoatOptions tables and calculates dealer margins.

Usage:
    python3 generate_complete_window_sticker.py <hull_serial_no>
    python3 generate_complete_window_sticker.py ETWP6278J324
"""

import sys
import mysql.connector
from typing import Dict, List, Optional, Tuple

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD'
}

# Product category mapping
CATEGORY_MAP = {
    'BS1': {'name': 'Base Boat', 'margin_field': 'base_boat_margin', 'priority': 1},
    'BOA': {'name': 'Base Boat', 'margin_field': 'base_boat_margin', 'priority': 1},
    'EN7': {'name': 'Engine', 'margin_field': 'engine_margin', 'priority': 2},
    'ENG': {'name': 'Engine', 'margin_field': 'engine_margin', 'priority': 2},
    'ENA': {'name': 'Engine Accessories', 'margin_field': 'engine_margin', 'priority': 3},
    'ENI': {'name': 'Engine Installation', 'margin_field': 'engine_margin', 'priority': 4},
    'ACC': {'name': 'Accessories', 'margin_field': 'options_margin', 'priority': 5},
    'ACY': {'name': 'Accessories', 'margin_field': 'options_margin', 'priority': 5},
    'PPR': {'name': 'Prep & Rigging', 'margin_field': 'prep_margin', 'priority': 6},
    'PPY': {'name': 'Prep & Rigging', 'margin_field': 'prep_margin', 'priority': 6},
    'PRE': {'name': 'Pre-Rigging', 'margin_field': 'prep_margin', 'priority': 7},
    'FRE': {'name': 'Freight', 'margin_field': 'freight_margin', 'priority': 8},
    'FRT': {'name': 'Freight', 'margin_field': 'freight_margin', 'priority': 8},
    'H1': {'name': 'Colors & Options', 'margin_field': 'options_margin', 'priority': 9},
    'H1P': {'name': 'Colors & Options', 'margin_field': 'options_margin', 'priority': 9},
    'H1V': {'name': 'Colors & Options', 'margin_field': 'options_margin', 'priority': 9},
    'H1I': {'name': 'Colors & Options', 'margin_field': 'options_margin', 'priority': 9},
    'H1F': {'name': 'Colors & Options', 'margin_field': 'options_margin', 'priority': 9},
    'H3A': {'name': 'Colors & Options', 'margin_field': 'options_margin', 'priority': 9},
    'H3G': {'name': 'Colors & Options', 'margin_field': 'options_margin', 'priority': 9},
    'H5': {'name': 'Colors & Options', 'margin_field': 'options_margin', 'priority': 9},
    'L0': {'name': 'Seating & Furniture', 'margin_field': 'options_margin', 'priority': 10},
    'L12': {'name': 'Seating & Furniture', 'margin_field': 'options_margin', 'priority': 10},
    'GRO': {'name': 'Other Charges', 'margin_field': 'options_margin', 'priority': 11},
    'C1L': {'name': 'Discounts', 'margin_field': None, 'priority': 12},
    'C2': {'name': 'Discounts', 'margin_field': None, 'priority': 12},
    'C3P': {'name': 'Discounts', 'margin_field': None, 'priority': 12},
    'VOD': {'name': 'Discounts', 'margin_field': None, 'priority': 12},
    'DIS': {'name': 'Discounts', 'margin_field': None, 'priority': 12},
}

def get_boat_from_serial_master(hull_no: str) -> Optional[Dict]:
    """Get boat information from SerialNumberMaster"""
    conn = mysql.connector.connect(**DB_CONFIG, database='warrantyparts')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            SN_MY,
            Boat_SerialNo,
            BoatItemNo,
            Series,
            BoatDesc1,
            BoatDesc2,
            SerialModelYear,
            ERP_OrderNo,
            InvoiceNo,
            InvoiceDateYYYYMMDD,
            DealerNumber,
            DealerName,
            DealerCity,
            DealerState,
            DealerZip,
            PanelColor,
            AccentPanel,
            TrimAccent,
            BaseVinyl
        FROM SerialNumberMaster
        WHERE Boat_SerialNo = %s
    """, (hull_no,))

    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        return None

    inv_date = row[9]
    if inv_date and len(str(inv_date)) == 8:
        inv_date_str = f"{inv_date[:4]}-{inv_date[4:6]}-{inv_date[6:]}"
    else:
        inv_date_str = "N/A"

    return {
        'model_year': row[0],
        'serial': row[1],
        'item_no': row[2],
        'series': row[3],
        'desc1': row[4],
        'desc2': row[5],
        'serial_model_year': row[6],
        'order': row[7],
        'invoice': row[8],
        'invoice_date': inv_date_str,
        'dealer_no': row[10],
        'dealer_name': row[11],
        'dealer_city': row[12],
        'dealer_state': row[13],
        'dealer_zip': row[14],
        'panel_color': row[15],
        'accent_panel': row[16],
        'trim_accent': row[17],
        'base_vinyl': row[18]
    }

def get_line_items_by_model_year(hull_no: str, model_year: int) -> Tuple[List, str]:
    """Get line items from the correct BoatOptions table based on model year"""
    conn = mysql.connector.connect(**DB_CONFIG, database='warrantyparts')
    cursor = conn.cursor()

    # Determine table name from model year
    table_name = f'BoatOptions{model_year}'

    try:
        cursor.execute(f"""
            SELECT
                LineNo,
                ItemNo,
                ItemDesc1,
                ItemMasterProdCat,
                QuantitySold,
                ExtSalesAmount
            FROM {table_name}
            WHERE BoatSerialNo = %s
            ORDER BY LineNo
        """, (hull_no,))

        items = cursor.fetchall()
        cursor.close()
        conn.close()

        if items:
            return items, table_name
        else:
            return [], table_name

    except Exception as e:
        cursor.close()
        conn.close()
        # If table doesn't exist or other error, try fallback search
        return get_line_items_fallback(hull_no)

def get_line_items_fallback(hull_no: str) -> Tuple[List, str]:
    """Fallback: Search all BoatOptions tables if model year approach fails"""
    conn = mysql.connector.connect(**DB_CONFIG, database='warrantyparts')
    cursor = conn.cursor()

    tables = ['BoatOptions26', 'BoatOptions25', 'BoatOptions24', 'BoatOptions23', 'BoatOptions22']

    for table in tables:
        try:
            cursor.execute(f"""
                SELECT
                    LineNo,
                    ItemNo,
                    ItemDesc1,
                    ItemMasterProdCat,
                    QuantitySold,
                    ExtSalesAmount
                FROM {table}
                WHERE BoatSerialNo = %s
                ORDER BY LineNo
            """, (hull_no,))

            items = cursor.fetchall()
            if items:
                cursor.close()
                conn.close()
                return items, table
        except Exception as e:
            continue

    cursor.close()
    conn.close()
    return [], None

def get_dealer_margins(dealer_no: str, series: str) -> Optional[Dict]:
    """Get dealer margins from DealerMargins table"""
    conn = mysql.connector.connect(**DB_CONFIG, database='warrantyparts_test')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            base_boat_margin,
            engine_margin,
            options_margin,
            freight_margin,
            prep_margin
        FROM DealerMargins
        WHERE dealer_id = %s
          AND series_id = %s
          AND enabled = 1
        LIMIT 1
    """, (dealer_no, series))

    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        return None

    return {
        'base_boat_margin': row[0] or 0,
        'engine_margin': row[1] or 0,
        'options_margin': row[2] or 0,
        'freight_margin': row[3] or 0,
        'prep_margin': row[4] or 0
    }

def categorize_items(line_items: List) -> Dict:
    """Group line items by category"""
    categories = {}
    for item in line_items:
        cat = item[3] or 'OTHER'
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)
    return categories

def calculate_totals_with_margins(categorized: Dict, margins: Optional[Dict]) -> Tuple[Dict, Dict, Dict]:
    """Calculate MSRP totals, dealer costs, and savings

    IMPORTANT: Excludes BS1/BOA (boat items) to prevent double-counting.
    Base boat MSRP comes from Models/ModelPricing tables, not from line items.
    """
    msrp_totals = {}
    dealer_costs = {}
    savings = {}

    for cat, items in categorized.items():
        # Skip boat items (BS1/BOA) - base boat already counted in Models table
        if cat in ('BS1', 'BOA'):
            continue

        msrp = sum(item[5] or 0 for item in items)
        msrp_totals[cat] = msrp

        # Calculate dealer cost if margins available
        if margins and cat in CATEGORY_MAP and CATEGORY_MAP[cat]['margin_field']:
            margin_field = CATEGORY_MAP[cat]['margin_field']
            margin_pct = margins.get(margin_field, 0)
            dealer_cost = msrp * (1 - margin_pct / 100)
            dealer_costs[cat] = dealer_cost
            savings[cat] = msrp - dealer_cost
        else:
            # No margin for discounts or unknown categories
            dealer_costs[cat] = msrp
            savings[cat] = 0

    return msrp_totals, dealer_costs, savings

def print_window_sticker(boat: Dict, line_items: List, table_name: str, margins: Optional[Dict]):
    """Print formatted window sticker with dealer pricing"""

    print("=" * 80)
    print("║" + " " * 78 + "║")
    print("║" + "BENNINGTON MARINE - WINDOW STICKER".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("=" * 80)

    # Dealer Information
    print("\n" + boat['dealer_name'].upper())
    if boat['dealer_city'] and boat['dealer_state']:
        print(f"{boat['dealer_city']}, {boat['dealer_state']} {boat['dealer_zip']}")
    print("www.benningtonmarine.com")
    print("888-906-2628")

    # Boat Information
    print("\n" + "=" * 80)
    print("📋 BOAT INFORMATION")
    print("=" * 80)
    print(f"   Model:                 {boat['serial_model_year']} {boat['item_no']}")
    print(f"   Description:           {boat['desc1']}")
    print(f"   Hull Serial (HIN):     {boat['serial']}")
    print(f"   Series:                {boat['series']} Series")
    print(f"   Invoice Date:          {boat['invoice_date']}")

    # Categorize and calculate
    categorized = categorize_items(line_items)
    msrp_totals, dealer_costs, savings = calculate_totals_with_margins(categorized, margins)

    # Sort categories by priority
    sorted_cats = sorted(
        categorized.keys(),
        key=lambda x: CATEGORY_MAP.get(x, {'priority': 99})['priority']
    )

    # Display line items
    print("\n" + "=" * 80)
    print("📦 INCLUDED ITEMS")
    print("=" * 80)

    for cat in sorted_cats:
        # Skip boat items (BS1/BOA) - base boat already in Models table
        if cat in ('BS1', 'BOA'):
            continue

        items = categorized[cat]
        cat_name = CATEGORY_MAP.get(cat, {'name': cat})['name']
        cat_msrp = msrp_totals.get(cat, 0)

        # Skip zero or very small amounts
        if abs(cat_msrp) < 0.01:
            continue

        print(f"\n   ✓ {cat_name.upper()} ({cat})")

        for item in items:
            desc = item[2] or 'No description'
            amount = item[5] or 0
            if abs(amount) >= 0.01:  # Only show non-zero amounts
                print(f"      • {desc:50s} ${amount:12,.2f}")

    # Pricing Summary
    print("\n" + "=" * 80)
    print("💰 PRICING SUMMARY")
    print("=" * 80)

    # MSRP breakdown
    print(f"\n   {'CATEGORY':<30s} {'MSRP':>12s}", end='')
    if margins:
        print(f" {'DEALER COST':>15s} {'SAVINGS':>12s}")
    else:
        print()

    print(f"   {'-'*30} {'-'*12}", end='')
    if margins:
        print(f" {'-'*15} {'-'*12}")
    else:
        print()

    total_msrp = 0
    total_dealer_cost = 0
    total_savings = 0

    for cat in sorted_cats:
        # Skip boat items (BS1/BOA) - already in Models table
        if cat in ('BS1', 'BOA'):
            continue

        cat_name = CATEGORY_MAP.get(cat, {'name': cat})['name']
        msrp = msrp_totals.get(cat, 0)

        if abs(msrp) < 0.01:
            continue

        total_msrp += msrp

        print(f"   {cat_name:<30s} ${msrp:11,.2f}", end='')

        if margins:
            cost = dealer_costs.get(cat, msrp)
            save = savings.get(cat, 0)
            total_dealer_cost += cost
            total_savings += save
            print(f" ${cost:14,.2f} ${save:11,.2f}")
        else:
            print()

    # Totals
    print(f"   {'-'*30} {'-'*12}", end='')
    if margins:
        print(f" {'-'*15} {'-'*12}")
    else:
        print()

    print(f"   {'TOTAL':<30s} ${total_msrp:11,.2f}", end='')
    if margins:
        print(f" ${total_dealer_cost:14,.2f} ${total_savings:11,.2f}")
        margin_pct = (total_savings / total_msrp * 100) if total_msrp > 0 else 0
        print(f"\n   Dealer Margin: {margin_pct:.1f}%")
    else:
        print()
        print(f"\n   Dealer cost available upon request")

    # Footer
    print("\n" + "=" * 80)
    print("║" + " " * 78 + "║")
    print("║" + "BENNINGTON MARINE - www.benningtonmarine.com".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("=" * 80)

    # Summary
    print(f"\n✅ Window sticker generated successfully!")
    print(f"   Hull: {boat['serial']}")
    print(f"   Model: {boat['serial_model_year']} {boat['item_no']}")
    print(f"   Dealer: {boat['dealer_name']}")
    print(f"   Data source: {table_name}")
    print(f"   Line Items: {len(line_items)}")
    print(f"   Total MSRP: ${total_msrp:,.2f}")
    if margins:
        print(f"   Dealer Cost: ${total_dealer_cost:,.2f}")
        print(f"   Dealer Savings: ${total_savings:,.2f}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_complete_window_sticker.py <hull_serial_no>")
        print("Example: python3 generate_complete_window_sticker.py ETWP6278J324")
        sys.exit(1)

    hull_no = sys.argv[1]

    try:
        print(f"\nFetching data for hull: {hull_no}...")

        # Step 1: Get boat header
        boat = get_boat_from_serial_master(hull_no)
        if not boat:
            print(f"Error: Hull '{hull_no}' not found in SerialNumberMaster")
            sys.exit(1)

        print(f"✓ Found boat: {boat['serial_model_year']} {boat['item_no']}")
        print(f"✓ Dealer: {boat['dealer_name']}")
        print(f"✓ Model Year: {boat['model_year']} → Searching BoatOptions{boat['model_year']}")

        # Step 2: Get line items using model year
        line_items, table_name = get_line_items_by_model_year(hull_no, boat['model_year'])
        if not line_items:
            print(f"Note: No line items found in {table_name}")
            print("      (Showing header information only)")
            margins = None
        else:
            print(f"✓ Found {len(line_items)} line items in {table_name}")

            # Step 3: Get dealer margins
            margins = get_dealer_margins(boat['dealer_no'], boat['series'])
            if margins:
                print(f"✓ Found dealer margins for dealer {boat['dealer_no']} + series {boat['series']}")
            else:
                print(f"Note: No dealer margins found for dealer {boat['dealer_no']} + series {boat['series']}")

        # Step 4: Generate sticker
        print("\nGenerating window sticker...\n")
        print_window_sticker(boat, line_items, table_name, margins)

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

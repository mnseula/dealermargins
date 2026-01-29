#!/usr/bin/env python3
"""
Window Sticker Generator for BoatOptions26_test

Uses actual MSSQL product codes (BOA, ACY, ENG, etc.)

Usage:
    python3 generate_window_sticker_26.py <order_number>
    python3 generate_window_sticker_26.py SO00933794
"""

import sys
import mysql.connector
from typing import Dict, List

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts_test'
}

# Product code category mapping
CATEGORY_MAP = {
    'BOA': {'name': 'Base Boat', 'priority': 1},
    'ENG': {'name': 'Engine Package', 'priority': 2},
    'ENA': {'name': 'Engine Accessories', 'priority': 3},
    'ENI': {'name': 'Engine Installation', 'priority': 4},
    'ACY': {'name': 'Accessories', 'priority': 5},
    'PPR': {'name': 'Prep and Rigging', 'priority': 6},
    'PRE': {'name': 'Pre-Rigging', 'priority': 7},
    'PRD': {'name': 'Product Items', 'priority': 8},
    'WIP': {'name': 'Work in Progress', 'priority': 9},
    'GRO': {'name': 'Group Items', 'priority': 10},
    'LAB': {'name': 'Labor', 'priority': 11},
    'FRE': {'name': 'Freight', 'priority': 12},
    'FRT': {'name': 'Freight', 'priority': 12},
    'VOD': {'name': 'Volume Discount', 'priority': 13},
    'DIS': {'name': 'Discount', 'priority': 14},
    'DIR': {'name': 'Discount', 'priority': 14},
    'WAR': {'name': 'Warranty', 'priority': 15},
    'LOY': {'name': 'Loyalty', 'priority': 16},
}

def get_boat_info(cursor, order_no: str) -> Dict:
    """Get basic boat information"""
    cursor.execute("""
        SELECT DISTINCT
            ERP_OrderNo,
            BoatSerialNo,
            BoatModelNo,
            Series,
            InvoiceNo,
            InvoiceDate
        FROM BoatOptions26_test
        WHERE ERP_OrderNo = %s
        LIMIT 1
    """, (order_no,))

    row = cursor.fetchone()
    if not row:
        return None

    inv_date = str(row[5]) if row[5] else ""
    date_str = f"{inv_date[:4]}-{inv_date[4:6]}-{inv_date[6:]}" if inv_date and len(inv_date) == 8 else "N/A"

    return {
        'order': row[0],
        'serial': row[1] or 'N/A',
        'model': row[2] or 'N/A',
        'series': row[3] or 'N/A',
        'invoice': row[4],
        'invoice_date': date_str
    }

def get_line_items(cursor, order_no: str) -> List:
    """Get all line items for an order"""
    cursor.execute("""
        SELECT
            LineNo,
            ItemNo,
            ItemDesc1,
            ItemMasterProdCat,
            QuantitySold,
            ExtSalesAmount
        FROM BoatOptions26_test
        WHERE ERP_OrderNo = %s
        ORDER BY LineNo
    """, (order_no,))

    return cursor.fetchall()

def categorize_items(line_items: List) -> Dict:
    """Group line items by product category"""
    categories = {}
    for item in line_items:
        cat = item[3] or 'OTHER'
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)
    return categories

def calculate_totals(categorized: Dict) -> Dict:
    """Calculate totals by category"""
    totals = {}
    for cat, items in categorized.items():
        total = sum(item[5] or 0 for item in items)
        totals[cat] = total
    return totals

def print_window_sticker(boat_info: Dict, line_items: List):
    """Print formatted window sticker"""

    print("=" * 80)
    print("║" + " " * 78 + "║")
    print("║" + "BENNINGTON MARINE - WINDOW STICKER".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("=" * 80)

    # Boat Information
    print("\n📋 BOAT INFORMATION")
    print("-" * 80)
    print(f"   Order Number:          {boat_info['order']}")
    print(f"   Hull Serial (HIN):     {boat_info['serial']}")
    print(f"   Model:                 {boat_info['model']}")
    print(f"   Series:                {boat_info['series']}")
    print(f"   Invoice Number:        {boat_info['invoice']}")
    print(f"   Invoice Date:          {boat_info['invoice_date']}")

    # Categorize items
    categorized = categorize_items(line_items)
    totals = calculate_totals(categorized)

    # Sort categories by priority
    sorted_cats = sorted(
        categorized.keys(),
        key=lambda x: CATEGORY_MAP.get(x, {'priority': 99})['priority']
    )

    # Display line items by category
    print("\n📦 INCLUDED ITEMS")
    print("-" * 80)

    for cat in sorted_cats:
        items = categorized[cat]
        cat_name = CATEGORY_MAP.get(cat, {'name': cat})['name']
        cat_total = totals[cat]

        if cat_total == 0:
            continue  # Skip zero-amount categories

        print(f"\n   ✓ {cat_name.upper()} ({cat})")

        # Show items (limit to first 10 per category)
        for item in items[:10]:
            desc = item[2] or 'No description'
            amount = item[5] or 0
            print(f"      • {desc:50s} ${amount:12,.2f}")

        if len(items) > 10:
            remaining = len(items) - 10
            remaining_total = sum(it[5] or 0 for it in items[10:])
            print(f"      ... and {remaining} more items (${remaining_total:,.2f})")

    # Pricing Summary
    print("\n" + "=" * 80)
    print("💰 PRICING SUMMARY")
    print("=" * 80)

    # Main categories
    base_boat = totals.get('BOA', 0)
    engine = totals.get('ENG', 0) + totals.get('ENA', 0) + totals.get('ENI', 0)
    accessories = totals.get('ACY', 0)
    prep = totals.get('PPR', 0) + totals.get('PRE', 0)
    labor = totals.get('LAB', 0)
    wip = totals.get('WIP', 0)

    print(f"\n   Base Boat Package:           ${base_boat:15,.2f}")
    print(f"   Engine Package:              ${engine:15,.2f}")
    print(f"   Accessories:                 ${accessories:15,.2f}")
    if prep > 0:
        print(f"   Prep & Rigging:              ${prep:15,.2f}")
    if labor > 0:
        print(f"   Labor:                       ${labor:15,.2f}")
    if wip > 0:
        print(f"   Work in Progress:            ${wip:15,.2f}")

    # Other items
    other_cats = set(totals.keys()) - {'BOA', 'ENG', 'ENA', 'ENI', 'ACY', 'PPR', 'PRE', 'LAB', 'WIP'}
    other_total = sum(totals.get(c, 0) for c in other_cats if totals.get(c, 0) != 0)

    if other_total != 0:
        print(f"   Other Items:                 ${other_total:15,.2f}")

    # Grand total
    grand_total = sum(totals.values())
    print(f"   " + "-" * 48)
    print(f"   TOTAL MSRP:                  ${grand_total:15,.2f}")

    # Footer
    print("\n" + "=" * 80)
    print("║" + " " * 78 + "║")
    print("║" + "BENNINGTON MARINE - www.benningtonmarine.com".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("=" * 80)

    # Summary
    print(f"\n✅ Window sticker generated successfully!")
    print(f"   Order: {boat_info['order']}")
    print(f"   Model: {boat_info['model']}")
    print(f"   Line Items: {len(line_items)}")
    print(f"   Total MSRP: ${grand_total:,.2f}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_window_sticker_26.py <order_number>")
        print("Example: python3 generate_window_sticker_26.py SO00933794")
        sys.exit(1)

    order_no = sys.argv[1]

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        print(f"\nFetching data for order: {order_no}...")

        boat_info = get_boat_info(cursor, order_no)
        if not boat_info:
            print(f"Error: Order '{order_no}' not found in BoatOptions26_test")
            sys.exit(1)

        line_items = get_line_items(cursor, order_no)
        if not line_items:
            print(f"Error: No line items found for order '{order_no}'")
            sys.exit(1)

        print_window_sticker(boat_info, line_items)

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

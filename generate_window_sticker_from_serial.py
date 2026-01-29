#!/usr/bin/env python3
"""
Window Sticker Generator using SerialNumberMaster

This is the correct way to generate window stickers for unregistered boats.
Uses the warrantyparts.SerialNumberMaster table.

Usage:
    python3 generate_window_sticker_from_serial.py <hull_serial_no>
    python3 generate_window_sticker_from_serial.py ETWTEST024
"""

import sys
import mysql.connector
from typing import Dict, List, Optional

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD'
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
            DealerCountry,
            PanelColor,
            AccentPanel,
            TrimAccent,
            WebOrderNo
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
        'dealer_country': row[15],
        'panel_color': row[16],
        'accent_panel': row[17],
        'trim_accent': row[18],
        'web_order': row[19]
    }

def get_line_items(order_no: str) -> List:
    """Get line items from BoatOptions tables"""
    conn = mysql.connector.connect(**DB_CONFIG, database='warrantyparts_test')
    cursor = conn.cursor()

    # Try BoatOptions26_test first
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

    items = cursor.fetchall()

    if not items:
        # Try BoatOptions25_test
        cursor.execute("""
            SELECT
                LineNo,
                ItemNo,
                ItemDesc1,
                ItemMasterProdCat,
                QuantitySold,
                ExtSalesAmount
            FROM BoatOptions25_test
            WHERE ERP_OrderNo = %s
            ORDER BY LineNo
        """, (order_no,))
        items = cursor.fetchall()

    cursor.close()
    conn.close()

    return items

def print_window_sticker(boat: Dict, line_items: List):
    """Print formatted window sticker"""

    print("=" * 80)
    print("║" + " " * 78 + "║")
    print("║" + "BENNINGTON MARINE - WINDOW STICKER".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("=" * 80)

    # Dealer Information
    print("\n" + "=" * 80)
    print("DEALER INFORMATION")
    print("=" * 80)
    print(f"{boat['dealer_name']}")
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
    if boat['desc2']:
        print(f"   Type:                  {boat['desc2']}")
    print(f"   Hull Serial (HIN):     {boat['serial']}")
    print(f"   Series:                {boat['series']} Series")
    print(f"   Order Number:          {boat['order']}")
    print(f"   Invoice Number:        {boat['invoice']}")
    print(f"   Invoice Date:          {boat['invoice_date']}")
    if boat['web_order']:
        print(f"   Web Order:             {boat['web_order']}")

    # Colors & Options
    if boat['panel_color'] or boat['accent_panel'] or boat['trim_accent']:
        print("\n" + "=" * 80)
        print("🎨 COLORS & TRIM")
        print("=" * 80)
        if boat['panel_color']:
            print(f"   Panel Color:           {boat['panel_color']}")
        if boat['accent_panel']:
            print(f"   Accent Panel:          {boat['accent_panel']}")
        if boat['trim_accent']:
            print(f"   Trim Accent:           {boat['trim_accent']}")

    # Line Items
    if line_items:
        print("\n" + "=" * 80)
        print("📦 INCLUDED ITEMS")
        print("=" * 80)

        # Group by category
        categories = {}
        for item in line_items:
            cat = item[3] or 'OTHER'
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(item)

        # Category mapping
        cat_names = {
            'BOA': 'Base Boat',
            'ENG': 'Engine Package',
            'ACY': 'Accessories',
            'PPR': 'Prep and Rigging',
            'PRE': 'Pre-Rigging',
            'VOD': 'Volume Discount',
            'WAR': 'Warranty',
            'LOY': 'Loyalty',
            'DIG': 'Discount',
            'LAB': 'Labor',
            'FRE': 'Freight',
            'FRT': 'Freight'
        }

        total_msrp = 0
        for cat, items in categories.items():
            cat_name = cat_names.get(cat, cat)
            cat_total = sum(item[5] or 0 for item in items)
            total_msrp += cat_total

            print(f"\n   ✓ {cat_name.upper()} ({cat})")
            for item in items[:10]:  # Show first 10
                desc = item[2] or 'No description'
                amount = item[5] or 0
                print(f"      • {desc:50s} ${amount:12,.2f}")

            if len(items) > 10:
                remaining = len(items) - 10
                remaining_total = sum(i[5] or 0 for i in items[10:])
                print(f"      ... and {remaining} more items (${remaining_total:,.2f})")

        # Pricing Summary
        print("\n" + "=" * 80)
        print("💰 PRICING SUMMARY")
        print("=" * 80)
        print(f"   TOTAL MSRP:              ${total_msrp:15,.2f}")
    else:
        print("\n" + "=" * 80)
        print("💰 PRICING")
        print("=" * 80)
        print("   NO PRICES - DISPLAY MODEL")
        print("\n   *This is a display/test boat. Pricing available upon request.")

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
    if line_items:
        print(f"   Line Items: {len(line_items)}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_window_sticker_from_serial.py <hull_serial_no>")
        print("Example: python3 generate_window_sticker_from_serial.py ETWTEST024")
        sys.exit(1)

    hull_no = sys.argv[1]

    try:
        print(f"\nFetching data for hull: {hull_no}...")

        boat = get_boat_from_serial_master(hull_no)
        if not boat:
            print(f"Error: Hull '{hull_no}' not found in SerialNumberMaster")
            sys.exit(1)

        line_items = get_line_items(boat['order'])
        if not line_items:
            print(f"Note: No line items found for order {boat['order']}")
            print("      (This is normal for display/test boats)")

        print_window_sticker(boat, line_items)

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

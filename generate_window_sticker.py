#!/usr/bin/env python3
"""
Simple Window Sticker Generator - SQL-Driven

Calls the GetWindowStickerData stored procedure with dealer ID, boat model, year, and optional identifier.

Usage:
    python3 generate_window_sticker.py <model_id> <dealer_id> <year> [identifier]

    identifier (optional): HIN (Hull ID Number) or Sales Order Number
        - If provided: shows only the configured performance package for that specific boat
        - If omitted: shows all available performance packages

Examples:
    python3 generate_window_sticker.py 25QXFBWA 00333836 2025
    python3 generate_window_sticker.py 25QXFBWA 00333836 2025 SO00935977
"""
import sys
import mysql.connector
from datetime import datetime

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts_test'
}

def format_currency(amount):
    """Format a number as currency"""
    if amount is None:
        return "N/A"
    return f"${amount:,.2f}"

def generate_window_sticker(model_id, dealer_id, year, identifier=None):
    """Generate window sticker by calling GetWindowStickerData stored procedure"""

    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor()

    try:
        # Call the stored procedure with year and optional identifier parameter
        cursor.callproc('GetWindowStickerData', [model_id, dealer_id, year, identifier])

        # Fetch all result sets
        results = []
        for result in cursor.stored_results():
            results.append(result.fetchall())

        if len(results) < 5:
            print(f"❌ Error: Expected 5 result sets, got {len(results)}")
            return

        # Result Set 1: Model Information
        model_info = results[0]
        if not model_info:
            print(f"❌ Error: No model found for ID '{model_id}' and year {year}")
            return

        model = model_info[0]

        # Result Set 2: Performance Specifications
        performance = results[1]

        # Result Set 3: Standard Features
        features = results[2]

        # Result Set 4: Included Options
        options = results[3]

        # Print Window Sticker
        print("=" * 80)
        print("BENNINGTON MARINE - WINDOW STICKER")
        print("=" * 80)

        # Model Information
        print(f"\nMODEL: {model[1]}")
        print(f"Model ID: {model[0]}")
        print(f"Series: {model[2]} ({model[3]})")
        if model[4]:
            print(f"Parent Series: {model[4]}")
        print(f"Floorplan: {model[5]} - {model[6]}")
        print(f"\nDIMENSIONS:")
        print(f"  Length: {model[7]}' ({model[8]})")
        print(f"  Beam: {model[9]}' ({model[10]})")
        print(f"  LOA: {model[11]}' ({model[12]})")
        print(f"  Seats: {model[13]}")

        # Pricing
        print(f"\nPRICING:")
        print(f"  Base MSRP: {format_currency(model[14])}")
        print(f"  Model Year: {model[15]}")
        print(f"  Effective Date: {model[16]}")

        # Performance Packages
        if performance:
            print(f"\nPERFORMANCE PACKAGES ({len(performance)} available):")
            print("-" * 80)
            for perf in performance:
                print(f"\n{perf[0]} - {perf[1]}")
                print(f"  Max HP: {perf[2]} HP")
                print(f"  Tubes: {perf[3]}")
                print(f"  Person Capacity: {perf[4]}")
                print(f"  Hull Weight: {perf[5]} lbs")
                if perf[6]:
                    print(f"  Pontoon Gauge: {perf[6]}")
                if perf[7]:
                    print(f"  Transom: {perf[7]}")
                if perf[8]:
                    print(f"  Tube Height: {perf[8]}")
                if perf[9]:
                    print(f"  Tube Center to Center: {perf[9]}")
                if perf[10]:
                    print(f"  Max Width: {perf[10]}")
                if perf[11]:
                    print(f"  Fuel Capacity: {perf[11]} gallons")
                if perf[12]:
                    print(f"  Tube Length: {perf[12]}")
                if perf[13]:
                    print(f"  Deck Length: {perf[13]}")
        else:
            print(f"\nPERFORMANCE PACKAGES: No performance data for year {year}")

        # Standard Features
        if features:
            print(f"\nSTANDARD FEATURES ({len(features)} total):")
            print("-" * 80)
            current_area = None
            for feature in features:
                area = feature[0]
                description = feature[1]

                if area != current_area:
                    print(f"\n{area}:")
                    current_area = area

                print(f"  • {description}")
        else:
            print(f"\nSTANDARD FEATURES: No features for year {year}")

        # Included Options
        if options:
            print(f"\nINCLUDED OPTIONS ({len(options)} items):")
            print("-" * 80)
            for option in options:
                item_no = option[0]
                description = option[1]
                quantity = option[2]
                sale_price = option[3]
                msrp = option[4]

                print(f"  {item_no}: {description}")
                print(f"    Quantity: {quantity}, Price: {format_currency(sale_price)}")
        else:
            print(f"\nINCLUDED OPTIONS: None in sales database for this model")

        # Footer
        print("\n" + "=" * 80)
        print(f"DEALER: {model[18]} (ID: {model[17]})")
        if model[19] and model[20]:
            print(f"Location: {model[19]}, {model[20]}")
        print(f"Generated: {model[21].strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

    except Exception as e:
        print(f"❌ Error generating window sticker: {e}")
        raise
    finally:
        cursor.close()
        connection.close()

def main():
    if len(sys.argv) < 4 or len(sys.argv) > 5:
        print("Usage: python3 generate_window_sticker.py <model_id> <dealer_id> <year> [identifier]")
        print("\nExamples:")
        print('  python3 generate_window_sticker.py 25QXFBWA 00333836 2025')
        print('  python3 generate_window_sticker.py 25QXFBWA 00333836 2025 SO00935977')
        sys.exit(1)

    model_id = sys.argv[1]
    dealer_id = sys.argv[2]
    year = int(sys.argv[3])
    identifier = sys.argv[4] if len(sys.argv) == 5 else None

    generate_window_sticker(model_id, dealer_id, year, identifier)

if __name__ == '__main__':
    main()

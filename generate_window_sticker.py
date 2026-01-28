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

        if len(results) < 4:
            print(f"❌ Error: Expected 4 result sets, got {len(results)}")
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

        # Print Window Sticker with fancy formatting
        width = 100
        print("═" * width)
        print("║" + " " * 98 + "║")
        print("║" + "BENNINGTON MARINE".center(98) + "║")
        print("║" + "MANUFACTURER'S SUGGESTED RETAIL PRICE".center(98) + "║")
        print("║" + " " * 98 + "║")
        print("═" * width)

        # Model Information
        # Construct model name if NULL: "25' Fastback with Windshield and Arch"
        model_name = model[1] if model[1] else f"{model[7]}' {model[6]}"

        print("\nMODEL INFORMATION")
        print("─" * width)
        print(f"Model Number:          {model[0]}")
        print(f"Series:                {model[2]} ({model[4] if model[4] else model[3]} Parent Series)")
        print(f"Year:                  {model[15]}")
        print(f"Model Description:     {model_name}")

        # Vessel Specifications
        print("\nVESSEL SPECIFICATIONS")
        print("─" * width)
        print(f"Length:                {model[7]}' (Length Overall)")
        print(f"Beam Width:            {model[10]}")
        print(f"Floorplan:             {model[6]} ({model[5]})")
        print(f"Seating Capacity:      {model[13]} seats")

        # Add performance specs from first package to vessel specs
        if performance:
            perf = performance[0]  # Use base/first performance package
            if perf[5]:  # hull_weight
                print(f"Hull Weight:           {int(perf[5]):,} lbs")
            if perf[2]:  # max_hp
                print(f"Maximum HP:            {int(perf[2])} HP")
            if perf[4]:  # person_capacity
                print(f"Person Capacity:       {perf[4]}")
            if perf[3]:  # no_of_tubes
                print(f"Pontoon Configuration: {int(perf[3])} Tubes")
            if perf[6]:  # pontoon_gauge
                print(f"Pontoon Gauge:         {perf[6]}")
            if perf[8]:  # tube_height
                print(f"Tube Height:           {perf[8]}")
            if perf[9]:  # tube_center_to_center
                print(f"Tube Spacing:          {perf[9]} (center to center)")
            if perf[10]:  # max_width
                print(f"Maximum Width:         {perf[10]}")
            if perf[7]:  # transom
                print(f"Transom Height:        {perf[7]}")
            if perf[11]:  # fuel_capacity
                print(f"Fuel Capacity:         {perf[11]}")

        # MSRP Banner
        print("\n" + "═" * width)
        print("║" + " " * 98 + "║")
        msrp_text = f"BASE MSRP: {format_currency(model[14])}"
        print("║" + msrp_text.center(98) + "║")
        print("║" + " " * 98 + "║")
        print("═" * width)

        # Standard Features
        print("\nSTANDARD EQUIPMENT INCLUDED IN BASE PRICE")
        print("═" * width)

        if features:
            current_area = None
            for feature in features:
                area = feature[0]
                description = feature[1]

                if area != current_area:
                    print(f"\n{area.upper()}")
                    print("─" * width)
                    current_area = area

                print(f"  ✓ {description}")
        else:
            print(f"No features loaded for year {year}")

        # Performance Packages
        if performance and len(performance) > 0:
            print("\nAVAILABLE PERFORMANCE PACKAGES")
            print("─" * width)
            for i, perf in enumerate(performance, 1):
                tubes = f"{int(perf[3])} Tube" if perf[3] else "N/A"
                max_hp = f"{int(perf[2])} HP" if perf[2] else "N/A"
                print(f"  {i}. {perf[0]:<25} - Max {max_hp}, {tubes} Configuration")

        # Included Options
        if options:
            print(f"\nINCLUDED OPTIONS")
            print("─" * width)
            for option in options:
                item_no = option[0]
                description = option[1]
                quantity = option[2]
                sale_price = option[3]

                print(f"  • {description} ({item_no})")
                if quantity:
                    print(f"    Quantity: {quantity}, Price: {format_currency(sale_price)}")

        # Footer
        print("\n" + "─" * width)
        dealer_text = f"Dealer: {model[18]}"
        generated_text = f"Generated: {model[21].strftime('%B %d, %Y at %I:%M %p')}"
        print(dealer_text)
        print(generated_text)
        print("\nThis label has been affixed in accordance with federal and state regulations.")
        print("Features and specifications are subject to change without notice.")
        print("═" * width)

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

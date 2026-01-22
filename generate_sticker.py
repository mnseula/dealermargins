"""
Generate Window Sticker - SQL-Driven Version

Simple script that calls the GetWindowStickerData stored procedure
and formats the output as a text window sticker.

Usage:
    python3 generate_sticker.py MODEL_ID "DEALER_NAME"

Example:
    python3 generate_sticker.py 25QXFBWA "NICHOLS MARINE - NORMAN"
"""

import sys
import mysql.connector
from mysql.connector import Error
from datetime import datetime

# Database Configuration
DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts_test'
}

def format_currency(amount):
    """Format number as currency"""
    if amount is None:
        return "$0.00"
    return f"${amount:,.2f}"

def generate_window_sticker(model_id: str, dealer_name: str):
    """Generate window sticker by calling stored procedure"""

    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        # Call the stored procedure
        cursor.callproc('GetWindowStickerData', [model_id, dealer_name])

        # Get all result sets
        results = []
        for result in cursor.stored_results():
            results.append(result.fetchall())

        if len(results) < 4:
            print(f"❌ Stored procedure returned insufficient data")
            return

        model_info = results[0][0] if results[0] else None
        performance_specs = results[1]
        standard_features = results[2]
        included_options = results[3]

        if not model_info:
            print(f"❌ Model '{model_id}' not found")
            return

        # Generate window sticker
        print("\n" + "=" * 80)
        print("BENNINGTON MARINE - WINDOW STICKER")
        print("=" * 80)

        # Model Information
        print(f"\nModel:        {model_info['model_id']}")
        print(f"Series:       {model_info['series_name']} ({model_info['parent_series']} Series)")
        print(f"Description:  {model_info['model_name'] or model_info['floorplan_desc']}")
        print(f"Year:         {model_info['year']}")

        # Dimensions
        print(f"\n--- DIMENSIONS ---")
        print(f"Length:       {model_info['loa_str'] or model_info['length_str']}")
        print(f"Beam:         {model_info['beam_str']}")
        print(f"Seats:        {model_info['seats']}")

        # Performance Specifications
        if performance_specs:
            print(f"\n--- PERFORMANCE PACKAGES ---")
            for perf in performance_specs:
                print(f"\n{perf['package_name']}:")
                print(f"  Max HP:           {perf['max_hp']} HP")
                print(f"  Tubes:            {perf['no_of_tubes']}")
                print(f"  Person Capacity:  {perf['person_capacity']}")
                print(f"  Hull Weight:      {perf['hull_weight']} lbs")
                print(f"  Pontoon Gauge:    {perf['pontoon_gauge']}")
                print(f"  Tube Height:      {perf['tube_height']}")
                if perf['fuel_capacity']:
                    print(f"  Fuel Capacity:    {perf['fuel_capacity']} gal")

        # Standard Features (organized by area)
        if standard_features:
            print(f"\n--- STANDARD FEATURES ---")
            current_area = None
            for feature in standard_features:
                if feature['area'] != current_area:
                    current_area = feature['area']
                    print(f"\n{current_area}:")
                print(f"  • {feature['description']}")

        # Included Options/Accessories
        if included_options:
            print(f"\n--- INCLUDED OPTIONS/ACCESSORIES ---")
            options_total = 0
            for option in included_options:
                qty = option['Quantity'] or 1
                price = option['MSRP'] or 0
                options_total += price
                print(f"  • {option['ItemDescription']}")
                print(f"    Item: {option['ItemNo']} | Qty: {qty} | Price: {format_currency(price)}")
            print(f"\nTotal Included Options: {format_currency(options_total)}")
        else:
            print(f"\n--- INCLUDED OPTIONS/ACCESSORIES ---")
            print("  (No options found in sales database - new model or no sales history)")

        # Pricing
        print(f"\n--- PRICING ---")
        print(f"Base MSRP:    {format_currency(model_info['msrp'])}")

        # Footer
        print(f"\n--- DEALER INFORMATION ---")
        print(f"Dealer:       {dealer_name}")
        print(f"Generated:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        print("\n" + "=" * 80)

        cursor.close()
        connection.close()

    except Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main execution"""
    if len(sys.argv) < 3:
        print("Usage: python3 generate_sticker.py MODEL_ID \"DEALER_NAME\"")
        print("\nExample:")
        print("  python3 generate_sticker.py 25QXFBWA \"NICHOLS MARINE - NORMAN\"")
        sys.exit(1)

    model_id = sys.argv[1]
    dealer_name = sys.argv[2]

    generate_window_sticker(model_id, dealer_name)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Window Sticker Generator with MSRP and Dealer Cost Calculation

Generates window stickers with:
- Complete MSRP breakdown from BoatOptions
- Dealer margins from unified lookup (DealerQuotes/DealerMargins)
- Dealer cost calculation (handles fixed $ and % margins)
- CPQ/EOS backward compatibility

Usage:
    python3 generate_window_sticker_with_pricing.py <model_id> <dealer_id> <year> [identifier]

Examples:
    python3 generate_window_sticker_with_pricing.py 25QXFBWA 333836 2025
    python3 generate_window_sticker_with_pricing.py 20SVFSR 333836 2024 ETWP6278J324
"""
import sys
import mysql.connector
from datetime import datetime
from decimal import Decimal

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts_test'
}

def format_currency(amount):
    """Format a number as currency"""
    if amount is None or amount == 0:
        return "$0.00"
    return f"${amount:,.2f}"

def get_boat_options_table(year):
    """Determine which BoatOptions table to use based on year"""
    year_suffix = str(year)[-2:]
    return f"warrantyparts.BoatOptions{year_suffix}"

def calculate_msrp(cursor, identifier, year):
    """Calculate MSRP breakdown from BoatOptions table"""
    table = get_boat_options_table(year)

    query = f"""
        SELECT
            COALESCE(SUM(CASE WHEN ItemMasterProdCat = 'BS1' THEN ExtSalesAmount END), 0) as base_boat,
            COALESCE(SUM(CASE WHEN ItemMasterProdCat = 'EN7' THEN ExtSalesAmount END), 0) as engine,
            COALESCE(SUM(CASE WHEN ItemMasterProdCat = 'ACC' THEN ExtSalesAmount END), 0) as accessories
        FROM {table}
        WHERE BoatSerialNo = %s OR BoatModelNo = %s
    """

    cursor.execute(query, (identifier, identifier))
    result = cursor.fetchone()

    if result:
        return {
            'base_boat': float(result[0]) if result[0] else 0,
            'engine': float(result[1]) if result[1] else 0,
            'accessories': float(result[2]) if result[2] else 0,
            'total': float(result[0] or 0) + float(result[1] or 0) + float(result[2] or 0)
        }
    return None

def get_dealer_margins(cursor, dealer_id, series_id):
    """Get dealer margins using unified lookup"""
    try:
        cursor.callproc('GetDealerMarginsWithFallback', [dealer_id, series_id])

        for result in cursor.stored_results():
            row = result.fetchone()
            if row:
                return {
                    'dealer_id': row[0],
                    'dealer_name': row[1],
                    'series_id': row[2],
                    'base_boat_margin_pct': float(row[3]) if row[3] else 0,
                    'engine_margin_pct': float(row[4]) if row[4] else 0,
                    'options_margin_pct': float(row[5]) if row[5] else 0,
                    'freight_type': row[6],
                    'freight_value': float(row[7]) if row[7] else 0,
                    'prep_type': row[8],
                    'prep_value': float(row[9]) if row[9] else 0,
                    'volume_discount_pct': float(row[10]) if row[10] else 0,
                    'data_source': row[11]
                }
    except Exception as e:
        print(f"Warning: Could not fetch dealer margins: {e}")

    return None

def calculate_dealer_cost(msrp_breakdown, margins, freight_amount=0, prep_amount=0):
    """Calculate dealer cost based on margins"""
    if not margins or not msrp_breakdown:
        return None

    # Calculate component dealer costs
    base_cost = msrp_breakdown['base_boat'] * (1 - margins['base_boat_margin_pct'] / 100)
    engine_cost = msrp_breakdown['engine'] * (1 - margins['engine_margin_pct'] / 100)
    options_cost = msrp_breakdown['accessories'] * (1 - margins['options_margin_pct'] / 100)

    # Handle freight (fixed $ or %)
    if margins['freight_type'] == 'FIXED_AMOUNT':
        freight_cost = freight_amount - margins['freight_value']
    else:  # PERCENTAGE
        freight_cost = freight_amount * (1 - margins['freight_value'] / 100)

    # Handle prep (fixed $ or %)
    if margins['prep_type'] == 'FIXED_AMOUNT':
        prep_cost = prep_amount - margins['prep_value']
    else:  # PERCENTAGE
        prep_cost = prep_amount * (1 - margins['prep_value'] / 100)

    return {
        'base_boat': base_cost,
        'engine': engine_cost,
        'accessories': options_cost,
        'freight': freight_cost,
        'prep': prep_cost,
        'total': base_cost + engine_cost + options_cost + freight_cost + prep_cost,
        'total_savings': msrp_breakdown['total'] + freight_amount + prep_amount - (base_cost + engine_cost + options_cost + freight_cost + prep_cost)
    }

def generate_window_sticker(model_id, dealer_id, year, identifier=None):
    """Generate window sticker with pricing and dealer cost"""

    connection = mysql.connector.connect(**DB_CONFIG)
    cursor = connection.cursor()

    try:
        # Call the stored procedure
        cursor.callproc('GetWindowStickerData', [model_id, dealer_id, year, identifier])

        # Fetch all result sets
        results = []
        for result in cursor.stored_results():
            results.append(result.fetchall())

        if len(results) < 4:
            print(f"❌ Error: Expected at least 4 result sets, got {len(results)}")
            return

        # Result Set 1: Model Information
        model_info = results[0]
        if not model_info:
            print(f"❌ Error: No model found for ID '{model_id}' and year {year}")
            return

        model = model_info[0]
        data_source = model[-1] if len(model) > 16 else 'CPQ'

        # Result Set 2: Performance Specifications
        performance = results[1]

        # Result Set 3: Standard Features
        features = results[2]

        # Result Set 4: Included Options
        options = results[3]

        # Calculate MSRP from BoatOptions
        lookup_id = identifier if identifier else model_id
        msrp_breakdown = calculate_msrp(cursor, lookup_id, year)

        # Get dealer margins
        series_id = model[2]  # series_id from model info
        margins = get_dealer_margins(cursor, dealer_id, series_id)

        # Calculate dealer costs (assuming no freight/prep for now - could be added)
        dealer_cost = calculate_dealer_cost(msrp_breakdown, margins, 0, 0) if msrp_breakdown and margins else None

        # ========== PRINT WINDOW STICKER ==========
        width = 100
        print("═" * width)
        print("║" + " " * 98 + "║")
        print("║" + "BENNINGTON MARINE".center(98) + "║")
        print("║" + "WINDOW STICKER - MANUFACTURER'S SUGGESTED RETAIL PRICE".center(98) + "║")
        print("║" + " " * 98 + "║")
        print("═" * width)

        if data_source == 'EOS':
            print(f"\n# Data Source: EOS (Backward Compatibility Mode)")

        # Model Information
        model_name = model[1] if model[1] else f"{model[7] if model[7] else 'Unknown'}"

        print("\nMODEL INFORMATION")
        print("─" * width)
        print(f"Model Number:          {model[0]}")
        print(f"Series:                {model[2]} {f'({model[3]} Series)' if model[3] else ''}")
        print(f"Model Year:            {year}")
        if model[5]:
            print(f"Description:           {model[5]}")
        if identifier:
            print(f"Boat Identifier:       {identifier}")

        # Dealer Information
        if model[13]:  # dealer_name
            print(f"\nDealer:                {model[13]}")
            if model[14] and model[15]:  # city, state
                print(f"Location:              {model[14]}, {model[15]}")

        # Vessel Specifications
        print("\nVESSEL SPECIFICATIONS")
        print("─" * width)

        # Add specs from performance data if available
        if performance:
            perf = performance[0]
            if perf[5]:  # hull_weight
                print(f"Hull Weight:           {int(perf[5]):,} lbs")
            if perf[2]:  # max_hp
                print(f"Maximum HP:            {int(perf[2])} HP")
            if perf[4]:  # person_capacity
                print(f"Person Capacity:       {perf[4]}")
            if perf[3]:  # no_of_tubes
                print(f"Pontoon Configuration: {int(perf[3])} Tubes")
            if perf[8]:  # fuel_capacity
                print(f"Fuel Capacity:         {perf[8]}")

        # MSRP BREAKDOWN
        if msrp_breakdown and msrp_breakdown['total'] > 0:
            print("\n" + "═" * width)
            print("║" + "PRICING BREAKDOWN".center(98) + "║")
            print("═" * width)

            print(f"\nBase Boat:             {format_currency(msrp_breakdown['base_boat'])}")
            print(f"Engine Package:        {format_currency(msrp_breakdown['engine'])}")
            print(f"Accessories:           {format_currency(msrp_breakdown['accessories'])}")
            print("─" * width)
            print(f"TOTAL MSRP:            {format_currency(msrp_breakdown['total'])}")

            # Dealer Cost (if margins available)
            if dealer_cost and margins:
                print("\n" + "═" * width)
                print("║" + f"DEALER COST - {margins['dealer_name']}".center(98) + "║")
                print("║" + f"(Source: {margins['data_source']})".center(98) + "║")
                print("═" * width)

                print(f"\nBase Boat:             {format_currency(dealer_cost['base_boat'])} (save {margins['base_boat_margin_pct']:.0f}%)")
                print(f"Engine Package:        {format_currency(dealer_cost['engine'])} (save {margins['engine_margin_pct']:.0f}%)")
                print(f"Accessories:           {format_currency(dealer_cost['accessories'])} (save {margins['options_margin_pct']:.0f}%)")
                print("─" * width)
                print(f"DEALER COST:           {format_currency(dealer_cost['total'])}")
                print(f"TOTAL SAVINGS:         {format_currency(dealer_cost['total_savings'])}")

                if margins['volume_discount_pct'] > 0:
                    print(f"\nVolume Discount Available: {margins['volume_discount_pct']:.0f}%")
        else:
            print("\n" + "═" * width)
            print("║" + "PRICING INFORMATION NOT AVAILABLE".center(98) + "║")
            print("║" + f"(No sales data found for {lookup_id} in year {year})".center(98) + "║")
            print("═" * width)

        # Standard Features
        print("\nSTANDARD EQUIPMENT INCLUDED")
        print("═" * width)

        if features:
            current_area = None
            feature_count = 0
            for feature in features:
                area = feature[0]
                description = feature[1]

                if area != current_area:
                    if current_area is not None:
                        print()  # Add spacing between areas
                    print(f"{area.upper()}")
                    print("─" * width)
                    current_area = area

                print(f"  ✓ {description}")
                feature_count += 1

            print(f"\n({feature_count} standard features total)")
        else:
            print(f"No standard features loaded for year {year}")

        # Performance Packages
        if performance and len(performance) > 1:
            print("\nAVAILABLE PERFORMANCE PACKAGES")
            print("─" * width)
            for i, perf in enumerate(performance, 1):
                tubes = f"{int(perf[3])} Tube" if perf[3] else "N/A"
                max_hp = f"{int(perf[2])} HP" if perf[2] else "N/A"
                print(f"  {i}. {perf[0]:<30} Max {max_hp:>7}, {tubes} Configuration")

        # Included Options
        if options:
            print(f"\nFACTORY INSTALLED OPTIONS")
            print("─" * width)
            for option in options:
                item_no = option[0]
                description = option[1]
                sale_price = option[3]

                price_str = format_currency(sale_price) if sale_price else ""
                print(f"  • {description:<70} {price_str:>15}")

        # Footer
        print("\n" + "═" * width)
        print(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
        print("\nThis label has been affixed in accordance with federal and state regulations.")
        print("Specifications are subject to change without notice.")
        print("═" * width)

    except Exception as e:
        print(f"❌ Error generating window sticker: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        connection.close()

def main():
    if len(sys.argv) < 4 or len(sys.argv) > 5:
        print(__doc__)
        sys.exit(1)

    model_id = sys.argv[1]
    dealer_id = sys.argv[2]
    year = int(sys.argv[3])
    identifier = sys.argv[4] if len(sys.argv) == 5 else None

    generate_window_sticker(model_id, dealer_id, year, identifier)

if __name__ == '__main__':
    main()

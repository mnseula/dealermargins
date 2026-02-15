#!/usr/bin/env python3
"""
Check ModelPerformance Data

Checks what performance data exists for a model.

Usage:
    python3 check_performance_data.py <model_id> <year>

Example:
    python3 check_performance_data.py 22SFC 2025

Author: Claude Code
Date: 2026-02-09
"""

import mysql.connector
import sys

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'warrantyparts_test',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD'
}

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 check_performance_data.py <model_id> <year>")
        print("Example: python3 check_performance_data.py 22SFC 2025")
        return 1

    model_id = sys.argv[1]
    year = int(sys.argv[2])

    print("="*80)
    print("MODEL PERFORMANCE DATA CHECK")
    print("="*80)
    print(f"Model: {model_id}")
    print(f"Year: {year}")
    print("="*80)
    print()

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        # Get all performance packages for this model
        cursor.execute("""
            SELECT
                mp.perf_package_id,
                pp.package_name,
                mp.tube_length_str,
                mp.deck_length_str,
                mp.person_capacity,
                mp.hull_weight,
                mp.max_hp,
                mp.no_of_tubes,
                mp.pontoon_gauge,
                mp.fuel_capacity,
                mp.tube_height
            FROM ModelPerformance mp
            JOIN PerformancePackages pp ON mp.perf_package_id = pp.perf_package_id
            WHERE mp.model_id = %s
              AND mp.year = %s
            ORDER BY mp.perf_package_id
        """, (model_id, year))

        packages = cursor.fetchall()

        if not packages:
            print(f"❌ No performance data found for {model_id} in {year}")
            return 1

        print(f"Found {len(packages)} performance package(s):")
        print()

        for pkg in packages:
            print(f"Package: {pkg['perf_package_id']} - {pkg['package_name']}")
            print(f"  Tube Length (pontoon_length):  {pkg['tube_length_str'] or 'NULL ❌'}")
            print(f"  Deck Length:                   {pkg['deck_length_str'] or 'NULL ❌'}")
            print(f"  Person Capacity:               {pkg['person_capacity']}")
            print(f"  Hull Weight:                   {pkg['hull_weight']}")
            print(f"  Max HP:                        {pkg['max_hp']}")
            print(f"  Number of Tubes:               {pkg['no_of_tubes']}")
            print(f"  Pontoon Gauge:                 {pkg['pontoon_gauge']}")
            print(f"  Tube Height:                   {pkg['tube_height']}")
            print(f"  Fuel Capacity:                 {pkg['fuel_capacity']}")
            print()

        # Check if ALL packages have NULL deck_length/tube_length
        null_deck = all(p['deck_length_str'] is None for p in packages)
        null_tube = all(p['tube_length_str'] is None for p in packages)

        if null_deck and null_tube:
            print("⚠️  ALL performance packages have NULL deck_length and tube_length!")
            print()
            print("Possible reasons:")
            print("  1. Data wasn't loaded from CPQ API")
            print("  2. CPQ API doesn't provide these fields")
            print("  3. Field mapping is incorrect")
            print()
            print("Check the load_cpq_data.py script to see if these fields are being loaded.")

        print("="*80)

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == '__main__':
    exit(main())

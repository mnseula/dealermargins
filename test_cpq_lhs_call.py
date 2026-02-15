#!/usr/bin/env python3
"""
Test CPQ LHS Data Stored Procedure Call

Tests the GET_CPQ_LHS_DATA stored procedure exactly as the JavaScript calls it.

Usage:
    python3 test_cpq_lhs_call.py <model_id> <year> <hull_no>

Example:
    python3 test_cpq_lhs_call.py 22SFC 2025 ETWINVTEST0126

Author: Claude Code
Date: 2026-02-09
"""

import mysql.connector
import sys
import json

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'warrantyparts',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD'
}

def main():
    if len(sys.argv) < 4:
        print("Usage: python3 test_cpq_lhs_call.py <model_id> <year> <hull_no>")
        print("Example: python3 test_cpq_lhs_call.py 22SFC 2025 ETWINVTEST0126")
        return 1

    model_id = sys.argv[1]
    year = int(sys.argv[2])
    hull_no = sys.argv[3]

    print("="*80)
    print("TEST CPQ LHS DATA STORED PROCEDURE")
    print("="*80)
    print(f"Model ID: {model_id}")
    print(f"Year: {year}")
    print(f"Hull No: {hull_no}")
    print("="*80)
    print()

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        # Call stored procedure exactly as JavaScript does
        print("Calling stored procedure: GET_CPQ_LHS_DATA")
        print(f"  @PARAM1 = '{model_id}'")
        print(f"  @PARAM2 = {year}")
        print(f"  @PARAM3 = '{hull_no}'")
        print()

        cursor.callproc('GET_CPQ_LHS_DATA', [model_id, year, hull_no])

        # Fetch results
        results = []
        for result in cursor.stored_results():
            rows = result.fetchall()
            results.extend(rows)

        print(f"Rows returned: {len(results)}")
        print()

        if len(results) == 0:
            print("❌ No data returned!")
            print()
            print("Possible reasons:")
            print(f"  1. Model '{model_id}' doesn't exist in warrantyparts_test.Models")
            print(f"  2. Hull '{hull_no}' doesn't exist in BoatOptions26")
            print(f"  3. Hull doesn't have perfPack configuration")
            return 1

        # Display the data
        row = results[0]

        print("✅ Data returned successfully!")
        print()
        print("="*80)
        print("BOAT SPECIFICATIONS")
        print("="*80)
        print(f"Model ID: {row.get('model_id')}")
        print(f"Model Name: {row.get('model_name')}")
        print(f"Series: {row.get('series_id')}")
        print(f"Floorplan: {row.get('floorplan_desc')}")
        print()
        print("DIMENSIONS:")
        print(f"  LOA: {row.get('loa')} ⬅️  THIS IS BOAT LENGTH")
        print(f"  Beam: {row.get('beam')}")
        print(f"  Length (feet): {row.get('length_feet')}")
        print(f"  Pontoon Length: {row.get('pontoon_length')}")
        print(f"  Deck Length: {row.get('deck_length')}")
        print()
        print("PERFORMANCE:")
        print(f"  Performance Package: {row.get('perf_package_id')} - {row.get('package_name')}")
        print(f"  Person Capacity: {row.get('person_capacity')}")
        print(f"  Seats: {row.get('seats')}")
        print(f"  Hull Weight: {row.get('hull_weight')}")
        print(f"  Max HP: {row.get('max_hp')}")
        print(f"  Engine Configuration: {row.get('engine_configuration')}")
        print()
        print("PONTOONS:")
        print(f"  Number of Tubes: {row.get('no_of_tubes')}")
        print(f"  Pontoon Gauge: {row.get('pontoon_gauge')}")
        print(f"  Pontoon Diameter: {row.get('pontoon_diameter')}")
        print(f"  Tube Height: {row.get('tube_height')}")
        print(f"  Fuel Capacity: {row.get('fuel_capacity')}")
        print()
        print("="*80)
        print("JSON OUTPUT (for debugging JavaScript)")
        print("="*80)
        print(json.dumps(row, indent=2, default=str))
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

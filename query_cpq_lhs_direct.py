#!/usr/bin/env python3
"""
Query CPQ LHS Data Directly

Executes the GET_CPQ_LHS_DATA query directly against the database
to see what data is being returned for a specific boat.

Usage:
    python3 query_cpq_lhs_direct.py <model_id> <year> <hull_no>

Example:
    python3 query_cpq_lhs_direct.py 22SFC 2025 ETWINVTEST0126

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
        print("Usage: python3 query_cpq_lhs_direct.py <model_id> <year> <hull_no>")
        print("Example: python3 query_cpq_lhs_direct.py 22SFC 2025 ETWINVTEST0126")
        return 1

    model_id = sys.argv[1]
    year = int(sys.argv[2])
    hull_no = sys.argv[3]

    print("="*80)
    print("DIRECT CPQ LHS DATA QUERY")
    print("="*80)
    print(f"Model ID: {model_id}")
    print(f"Year: {year}")
    print(f"Hull No: {hull_no}")
    print("="*80)
    print()

    # The exact SQL from GET_CPQ_LHS_DATA_v3.sql
    query = """
    SELECT
        m.model_id,
        m.model_name,
        m.series_id,
        m.floorplan_desc,
        m.loa_str AS loa,
        m.beam_str AS beam,
        m.length_feet,
        m.seats,
        mp.perf_package_id,
        pp.package_name,
        mp.person_capacity,
        mp.hull_weight,
        mp.max_hp,
        mp.no_of_tubes,
        mp.pontoon_gauge,
        mp.fuel_capacity,
        mp.tube_length_str AS pontoon_length,
        mp.deck_length_str AS deck_length,
        mp.tube_height,
        mp.pontoon_gauge AS pontoon_diameter,
        COALESCE(
            m.engine_configuration,
            CASE
                WHEN m.twin_engine = 1 THEN 'Twin Outboard'
                ELSE 'Single Outboard'
            END
        ) AS engine_configuration
    FROM warrantyparts_test.Models m
    LEFT JOIN (
        SELECT CfgValue AS perf_package_id
        FROM warrantyparts.BoatOptions26
        WHERE BoatSerialNo = %s
          AND CfgName = 'perfPack'
        LIMIT 1
    ) boat_perf ON 1=1
    LEFT JOIN warrantyparts_test.ModelPerformance mp
        ON m.model_id = mp.model_id
        AND mp.year = %s
        AND mp.perf_package_id = boat_perf.perf_package_id
    LEFT JOIN warrantyparts_test.PerformancePackages pp
        ON mp.perf_package_id = pp.perf_package_id
    WHERE m.model_id = %s
    LIMIT 1
    """

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        print("Executing GET_CPQ_LHS_DATA query...")
        cursor.execute(query, (hull_no, year, model_id))
        results = cursor.fetchall()

        if not results:
            print("❌ No data returned!")
            print()
            print("Troubleshooting:")

            # Check if model exists
            cursor.execute("SELECT * FROM warrantyparts_test.Models WHERE model_id = %s", (model_id,))
            model = cursor.fetchone()
            if model:
                print(f"  ✅ Model '{model_id}' exists in Models table")
            else:
                print(f"  ❌ Model '{model_id}' NOT FOUND in Models table")

            # Check if hull exists
            cursor.execute("SELECT * FROM warrantyparts.BoatOptions26 WHERE BoatSerialNo = %s LIMIT 1", (hull_no,))
            boat = cursor.fetchone()
            if boat:
                print(f"  ✅ Hull '{hull_no}' exists in BoatOptions26")

                # Check for perfPack
                cursor.execute("SELECT CfgValue FROM warrantyparts.BoatOptions26 WHERE BoatSerialNo = %s AND CfgName = 'perfPack' LIMIT 1", (hull_no,))
                perf = cursor.fetchone()
                if perf:
                    print(f"  ✅ perfPack found: {perf['CfgValue']}")
                else:
                    print(f"  ⚠️  No perfPack configuration found for this hull")
            else:
                print(f"  ❌ Hull '{hull_no}' NOT FOUND in BoatOptions26")

            return 1

        row = results[0]

        print("✅ Data returned successfully!")
        print()
        print("="*80)
        print("WINDOW STICKER DATA - BOAT SPECIFICATIONS")
        print("="*80)
        print()
        print(f"Model ID:          {row['model_id']}")
        print(f"Model Name:        {row['model_name']}")
        print(f"Series:            {row['series_id']}")
        print(f"Floorplan:         {row['floorplan_desc']}")
        print()
        print("DIMENSIONS (THIS IS WHAT SHOWS ON WINDOW STICKER):")
        print(f"  LOA:             {row['loa']} ⬅️  BOAT LENGTH")
        print(f"  Beam:            {row['beam']}")
        print(f"  Length (feet):   {row['length_feet']}")
        print(f"  Pontoon Length:  {row['pontoon_length']}")
        print(f"  Deck Length:     {row['deck_length']}")
        print()
        print("PERFORMANCE:")
        print(f"  Package:         {row['perf_package_id']} - {row['package_name']}")
        print(f"  Person Capacity: {row['person_capacity']}")
        print(f"  Seats:           {row['seats']}")
        print(f"  Hull Weight:     {row['hull_weight']}")
        print(f"  Max HP:          {row['max_hp']}")
        print(f"  Engine Config:   {row['engine_configuration']}")
        print(f"  Fuel Capacity:   {row['fuel_capacity']}")
        print()
        print("PONTOONS:")
        print(f"  Tubes:           {row['no_of_tubes']}")
        print(f"  Gauge:           {row['pontoon_gauge']}")
        print(f"  Diameter:        {row['pontoon_diameter']}")
        print(f"  Tube Height:     {row['tube_height']}")
        print()
        print("="*80)
        print("JSON (for JavaScript debugging):")
        print("="*80)
        print(json.dumps(row, indent=2, default=str))
        print("="*80)
        print()

        if row['loa']:
            print("✅ LOA (boat length) IS present in data!")
            print(f"   The window sticker should display: {row['loa']}")
        else:
            print("❌ LOA (boat length) is NULL!")
            print("   This explains why it's missing from the window sticker")

        print()
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

#!/usr/bin/env python3
"""
Check what performance data exists for model 22MSB
"""

import mysql.connector

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts_test'
}

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor(dictionary=True)

print("=" * 100)
print("MODEL 22MSB - CHECKING PERFORMANCE DATA")
print("=" * 100)
print()

# Check Models table
print("1. MODEL DATA:")
print("-" * 100)
cursor.execute("""
    SELECT
        model_id,
        model_name,
        series_id,
        engine_configuration,
        twin_engine,
        loa_str,
        beam_str,
        length_feet
    FROM Models
    WHERE model_id = '22MSB'
""")
model = cursor.fetchone()
if model:
    for key, value in model.items():
        print(f"  {key}: {value}")
else:
    print("  ❌ Model 22MSB not found!")
print()

# Check ModelPerformance for year 2026
print("2. PERFORMANCE PACKAGES FOR 22MSB (Year 2026):")
print("-" * 100)
cursor.execute("""
    SELECT
        mp.perf_package_id,
        pp.package_name,
        mp.tube_length_str,
        mp.deck_length_str,
        mp.max_hp,
        mp.no_of_tubes,
        mp.pontoon_gauge,
        mp.fuel_capacity
    FROM ModelPerformance mp
    JOIN PerformancePackages pp ON mp.perf_package_id = pp.perf_package_id
    WHERE mp.model_id = '22MSB'
      AND mp.year = 2026
    ORDER BY mp.perf_package_id
""")
perfs = cursor.fetchall()
if perfs:
    for i, perf in enumerate(perfs, 1):
        print(f"\n  Package {i}: {perf['package_name']} ({perf['perf_package_id']})")
        print(f"    Pontoon Length: {perf['tube_length_str']}")
        print(f"    Deck Length: {perf['deck_length_str']}")
        print(f"    Max HP: {perf['max_hp']}")
        print(f"    No of Tubes: {perf['no_of_tubes']}")
        print(f"    Pontoon Gauge: {perf['pontoon_gauge']}")
        print(f"    Fuel Capacity: {perf['fuel_capacity']}")
else:
    print("  ❌ No performance packages found for 22MSB year 2026!")
print()

# Check BoatOptions table
print("3. BOAT OPTIONS FOR CPQTEST26:")
print("-" * 100)
cursor.execute("""
    SELECT
        BoatSerialNo,
        CfgName,
        CfgValue
    FROM BoatOptions
    WHERE BoatSerialNo = 'CPQTEST26'
    ORDER BY CfgName
""")
boat_opts = cursor.fetchall()
if boat_opts:
    print(f"  Found {len(boat_opts)} configuration options:")
    for opt in boat_opts:
        print(f"    {opt['CfgName']}: {opt['CfgValue']}")

    # Check specifically for perfPack
    cursor.execute("""
        SELECT CfgValue
        FROM BoatOptions
        WHERE BoatSerialNo = 'CPQTEST26'
          AND CfgName = 'perfPack'
    """)
    perf_pack = cursor.fetchone()
    if perf_pack:
        print(f"\n  ✅ Performance Package: {perf_pack['CfgValue']}")
    else:
        print(f"\n  ❌ No 'perfPack' configuration found for CPQTEST26!")
        print(f"     This is why Pontoon Length, Deck Length are empty!")
else:
    print("  ❌ No boat options found for CPQTEST26!")
    print("     The BoatOptions table might be empty or boat not loaded yet.")
print()

cursor.close()
conn.close()

print("=" * 100)

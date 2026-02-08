#!/usr/bin/env python3
"""
Sync CPQ Data from warrantyparts_test to Eos Database

This script transforms normalized CPQ data (from APIs) into flattened tables
for JavaScript/CPQ platform consumption.

Data Flow:
    warrantyparts_test (normalized) → Eos (flattened for JavaScript)

Transformations:
    1. Models → boat_specs (basic boat dimensions)
    2. ModelPerformance → perf_pkg_spec (performance packages with sequential PKG_ID)
    3. StandardFeatures → standards_list (feature lookup table)
    4. ModelStandardFeatures → standards_matrix_2025 (model × feature mappings)

Run after load_cpq_data.py completes to sync latest CPQ catalog data.

Usage:
    python3 sync_cpq_to_eos.py [--year 2025] [--dry-run]

Author: Claude Code
Date: 2026-02-08
"""

import mysql.connector
from mysql.connector import Error
import argparse
import sys
from datetime import datetime
from typing import Tuple

# ==================== CONFIGURATION ====================

# Source Database (normalized CPQ data from APIs)
SOURCE_DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'warrantyparts_test',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD'
}

# Destination Database (flattened data for JavaScript)
DEST_DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'Eos',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD'
}

# Model Year (default)
DEFAULT_YEAR = 2025

# ==================== LOGGING ====================

def log(message: str, level: str = "INFO"):
    """Print timestamped log message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

# ==================== STEP 1: MODELS → BOAT_SPECS ====================

def sync_boat_specs(source_cursor, dest_cursor, year: int, dry_run: bool = False) -> Tuple[int, int]:
    """
    Sync Models table to boat_specs.

    Note: For CPQ boats, we leave PONT_LEN, DECK_LEN, PONT_DIAM, and FUEL_CAP empty
    because these vary by performance package. JavaScript gets them from perf_pkg_spec instead.
    """
    log("\n" + "="*80)
    log("STEP 1: Sync Models → boat_specs")
    log("="*80)

    # Query source data
    query = """
        SELECT
            m.model_id,
            m.loa_str,
            m.beam_str
        FROM Models m
        WHERE m.model_id LIKE %s
    """

    year_prefix = str(year)[2:]  # "2025" → "25"
    source_cursor.execute(query, (f"{year_prefix}%",))
    models = source_cursor.fetchall()

    log(f"Found {len(models)} CPQ models for year {year}")

    if dry_run:
        log("DRY RUN: Would sync to Eos.boat_specs", "INFO")
        if models:
            log(f"Sample: {models[0]}", "INFO")
        return len(models), 0

    # Insert/update to destination
    insert_query = """
        INSERT INTO boat_specs (
            MODEL, LOA, PONT_LEN, DECK_LEN, BEAM, PONT_DIAM,
            ENG_CONFIG_ID, FUEL_TYPE_ID, FUEL_CAP
        )
        VALUES (%s, %s, '', '', %s, '', '', '', '')
        ON DUPLICATE KEY UPDATE
            LOA = VALUES(LOA),
            BEAM = VALUES(BEAM)
    """

    success = 0
    errors = 0

    for model in models:
        try:
            dest_cursor.execute(insert_query, (
                model[0],  # MODEL
                model[1],  # LOA
                model[2]   # BEAM
            ))
            success += 1
        except Exception as e:
            errors += 1
            log(f"Error syncing model {model[0]}: {e}", "ERROR")

    log(f"✅ Synced {success} models to boat_specs ({errors} errors)")
    return success, errors

# ==================== STEP 2: MODEL PERFORMANCE → PERF_PKG_SPEC ====================

def sync_perf_pkg_spec(source_cursor, dest_cursor, year: int, dry_run: bool = False) -> Tuple[int, int]:
    """
    Sync ModelPerformance to perf_pkg_spec.

    Key transformation: Generate sequential PKG_ID (1, 2, 3...) per model
    using ROW_NUMBER() since Eos uses float PKG_ID but CPQ uses string package names.
    """
    log("\n" + "="*80)
    log("STEP 2: Sync ModelPerformance → perf_pkg_spec")
    log("="*80)

    # Query source data with ROW_NUMBER to generate sequential PKG_ID
    query = """
        SELECT
            mp.model_id,
            ROW_NUMBER() OVER (PARTITION BY mp.model_id ORDER BY pp.perf_package_id) AS pkg_id,
            pp.package_name,
            'Active' AS status,
            CAST(mp.max_hp AS CHAR) AS max_hp,
            mp.person_capacity AS cap,
            CAST(mp.hull_weight AS CHAR) AS weight,
            CAST(mp.pontoon_gauge AS CHAR) AS pont_gauge,
            mp.transom,
            ROW_NUMBER() OVER (PARTITION BY mp.model_id ORDER BY pp.perf_package_id) AS display_order
        FROM ModelPerformance mp
        JOIN PerformancePackages pp ON mp.perf_package_id = pp.perf_package_id
        WHERE mp.year = %s
          AND mp.model_id LIKE %s
        ORDER BY mp.model_id, pkg_id
    """

    year_prefix = str(year)[2:]  # "2025" → "25"
    source_cursor.execute(query, (year, f"{year_prefix}%"))
    packages = source_cursor.fetchall()

    log(f"Found {len(packages)} performance package records for year {year}")

    if dry_run:
        log("DRY RUN: Would sync to Eos.perf_pkg_spec", "INFO")
        if packages:
            log(f"Sample: {packages[0]}", "INFO")
        return len(packages), 0

    # Insert/update to destination
    insert_query = """
        INSERT INTO perf_pkg_spec (
            MODEL, PKG_ID, PKG_NAME, STATUS, MAX_HP, CAP, WEIGHT,
            PONT_GAUGE, TRANSOM, `ORDER`
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            PKG_NAME = VALUES(PKG_NAME),
            STATUS = VALUES(STATUS),
            MAX_HP = VALUES(MAX_HP),
            CAP = VALUES(CAP),
            WEIGHT = VALUES(WEIGHT),
            PONT_GAUGE = VALUES(PONT_GAUGE),
            TRANSOM = VALUES(TRANSOM),
            `ORDER` = VALUES(`ORDER`)
    """

    success = 0
    errors = 0

    for pkg in packages:
        try:
            dest_cursor.execute(insert_query, pkg)
            success += 1
        except Exception as e:
            errors += 1
            log(f"Error syncing package {pkg[0]}/{pkg[1]}: {e}", "ERROR")

    log(f"✅ Synced {success} performance packages to perf_pkg_spec ({errors} errors)")
    return success, errors

# ==================== STEP 3: STANDARD FEATURES → STANDARDS_LIST ====================

def sync_standards_list(source_cursor, dest_cursor, dry_run: bool = False) -> Tuple[int, int]:
    """
    Sync StandardFeatures to standards_list.

    Simple 1:1 mapping: area → CATEGORY, feature_code → STANDARD, description → STAND_DESC
    """
    log("\n" + "="*80)
    log("STEP 3: Sync StandardFeatures → standards_list")
    log("="*80)

    # Query source data
    query = """
        SELECT
            sf.area AS category,
            sf.feature_code AS standard,
            sf.description AS stand_desc
        FROM StandardFeatures sf
        WHERE sf.active = TRUE
    """

    source_cursor.execute(query)
    features = source_cursor.fetchall()

    log(f"Found {len(features)} active standard features")

    if dry_run:
        log("DRY RUN: Would sync to Eos.standards_list", "INFO")
        if features:
            log(f"Sample: {features[0]}", "INFO")
        return len(features), 0

    # Insert/update to destination
    insert_query = """
        INSERT INTO standards_list (CATEGORY, STANDARD, STAND_DESC)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            STAND_DESC = VALUES(STAND_DESC),
            CATEGORY = VALUES(CATEGORY)
    """

    success = 0
    errors = 0

    for feature in features:
        try:
            dest_cursor.execute(insert_query, feature)
            success += 1
        except Exception as e:
            errors += 1
            log(f"Error syncing feature {feature[1]}: {e}", "ERROR")

    log(f"✅ Synced {success} features to standards_list ({errors} errors)")
    return success, errors

# ==================== STEP 4: MODEL STANDARD FEATURES → STANDARDS_MATRIX ====================

def sync_standards_matrix(source_cursor, dest_cursor, year: int, dry_run: bool = False) -> Tuple[int, int]:
    """
    Sync ModelStandardFeatures to standards_matrix_YYYY.

    Denormalizes many-to-many junction table with context fields.
    """
    log("\n" + "="*80)
    log(f"STEP 4: Sync ModelStandardFeatures → standards_matrix_{year}")
    log("="*80)

    # Query source data (JOIN to flatten)
    query = """
        SELECT
            m.series_id AS series,
            msf.model_id AS model,
            sf.feature_code AS standard,
            sf.area AS category,
            sf.description AS opt_name
        FROM ModelStandardFeatures msf
        JOIN StandardFeatures sf ON msf.feature_id = sf.feature_id
        JOIN Models m ON msf.model_id = m.model_id
        WHERE msf.year = %s
          AND msf.is_standard = TRUE
          AND msf.model_id LIKE %s
    """

    year_prefix = str(year)[2:]  # "2025" → "25"
    source_cursor.execute(query, (year, f"{year_prefix}%"))
    mappings = source_cursor.fetchall()

    log(f"Found {len(mappings)} model × feature mappings for year {year}")

    if dry_run:
        log(f"DRY RUN: Would sync to Eos.standards_matrix_{year}", "INFO")
        if mappings:
            log(f"Sample: {mappings[0]}", "INFO")
        return len(mappings), 0

    # Insert/update to destination
    table_name = f"standards_matrix_{year}"
    insert_query = f"""
        INSERT INTO {table_name} (SERIES, MODEL, STANDARD, CATEGORY, OPT_NAME)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            CATEGORY = VALUES(CATEGORY),
            OPT_NAME = VALUES(OPT_NAME)
    """

    success = 0
    errors = 0

    for mapping in mappings:
        try:
            dest_cursor.execute(insert_query, mapping)
            success += 1
        except Exception as e:
            errors += 1
            log(f"Error syncing mapping {mapping[1]}/{mapping[2]}: {e}", "ERROR")

    log(f"✅ Synced {success} mappings to standards_matrix_{year} ({errors} errors)")
    return success, errors

# ==================== MAIN EXECUTION ====================

def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description='Sync CPQ data from warrantyparts_test to Eos database'
    )
    parser.add_argument('--year', type=int, default=DEFAULT_YEAR,
                       help=f'Model year to sync (default: {DEFAULT_YEAR})')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview changes without writing to database')

    args = parser.parse_args()

    print("=" * 80)
    print("CPQ DATA SYNC: warrantyparts_test → Eos")
    print("=" * 80)
    print(f"Source:   {SOURCE_DB_CONFIG['database']}")
    print(f"Dest:     {DEST_DB_CONFIG['database']}")
    print(f"Year:     {args.year}")
    print(f"Dry Run:  {args.dry_run}")
    print(f"Started:  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    try:
        # Connect to source database
        log("Connecting to source database (warrantyparts_test)...")
        source_conn = mysql.connector.connect(**SOURCE_DB_CONFIG)
        source_cursor = source_conn.cursor()
        log("✅ Connected to source database")

        # Connect to destination database
        log("Connecting to destination database (Eos)...")
        dest_conn = mysql.connector.connect(**DEST_DB_CONFIG)
        dest_cursor = dest_conn.cursor()
        log("✅ Connected to destination database")

        # Track statistics
        total_success = 0
        total_errors = 0

        # STEP 1: Sync boat_specs
        success, errors = sync_boat_specs(source_cursor, dest_cursor, args.year, args.dry_run)
        total_success += success
        total_errors += errors
        if not args.dry_run:
            dest_conn.commit()

        # STEP 2: Sync perf_pkg_spec
        success, errors = sync_perf_pkg_spec(source_cursor, dest_cursor, args.year, args.dry_run)
        total_success += success
        total_errors += errors
        if not args.dry_run:
            dest_conn.commit()

        # STEP 3: Sync standards_list
        success, errors = sync_standards_list(source_cursor, dest_cursor, args.dry_run)
        total_success += success
        total_errors += errors
        if not args.dry_run:
            dest_conn.commit()

        # STEP 4: Sync standards_matrix
        success, errors = sync_standards_matrix(source_cursor, dest_cursor, args.year, args.dry_run)
        total_success += success
        total_errors += errors
        if not args.dry_run:
            dest_conn.commit()

        # Get final counts from destination
        if not args.dry_run:
            log("\n" + "="*80)
            log("Verifying destination table counts...")
            log("="*80)

            year_prefix = str(args.year)[2:]

            dest_cursor.execute(f"SELECT COUNT(*) FROM boat_specs WHERE MODEL LIKE '{year_prefix}%'")
            boat_specs_count = dest_cursor.fetchone()[0]
            log(f"boat_specs (CPQ {args.year}): {boat_specs_count:,} rows")

            dest_cursor.execute(f"SELECT COUNT(*) FROM perf_pkg_spec WHERE MODEL LIKE '{year_prefix}%'")
            perf_pkg_count = dest_cursor.fetchone()[0]
            log(f"perf_pkg_spec (CPQ {args.year}): {perf_pkg_count:,} rows")

            dest_cursor.execute("SELECT COUNT(*) FROM standards_list")
            standards_list_count = dest_cursor.fetchone()[0]
            log(f"standards_list (all): {standards_list_count:,} rows")

            dest_cursor.execute(f"SELECT COUNT(*) FROM standards_matrix_{args.year} WHERE MODEL LIKE '{year_prefix}%'")
            standards_matrix_count = dest_cursor.fetchone()[0]
            log(f"standards_matrix_{args.year} (CPQ): {standards_matrix_count:,} rows")

        # Close connections
        source_cursor.close()
        source_conn.close()
        dest_cursor.close()
        dest_conn.close()

        log("\n✅ Database connections closed")

        # Summary
        print("\n" + "=" * 80)
        if args.dry_run:
            print("DRY RUN COMPLETE - SUMMARY")
        else:
            print("SYNC COMPLETE - SUMMARY")
        print("=" * 80)
        print(f"Total records processed: {total_success:,}")
        print(f"Total errors:            {total_errors:,}")
        print(f"Year:                    {args.year}")
        print(f"Completed:               {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        if args.dry_run:
            print("\n💡 Run without --dry-run to apply changes to Eos database")
        else:
            print("\n✅ CPQ data successfully synced to Eos database")
            print("   JavaScript can now query updated boat_specs, perf_pkg_spec,")
            print("   standards_list, and standards_matrix tables")

        print("=" * 80)

        sys.exit(0)

    except Error as e:
        log(f"Database error: {e}", "ERROR")
        sys.exit(1)
    except Exception as e:
        log(f"Unexpected error: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

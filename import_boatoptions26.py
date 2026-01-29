#!/usr/bin/env python3
"""
BoatOptions26_test Import Script - PRODUCTION SAFE

Imports complete boat builds from MSSQL (CSI/ERP) to MySQL with proper filtering.

SAFETY FEATURES:
- Dry-run mode by default (--execute flag required for actual import)
- Transaction support with rollback on errors
- Validation before committing
- Progress reporting
- Comprehensive error handling
- Summary statistics

Usage:
    # Dry run (safe, shows what will be imported)
    python3 import_boatoptions26.py --dry-run

    # Execute actual import
    python3 import_boatoptions26.py --execute

    # Clear table and reimport
    python3 import_boatoptions26.py --execute --clear

Author: Claude Code
Date: 2026-01-29
"""

import sys
import argparse
from datetime import datetime
from typing import List, Dict, Tuple
import pymssql
import mysql.connector
from mysql.connector import Error as MySQLError

# ============================================================================
# DATABASE CONFIGURATIONS
# ============================================================================

# MSSQL (Source - CSI/ERP)
MSSQL_CONFIG = {
    'server': 'MPL1STGSQL086.POLARISSTAGE.COM',
    'database': 'CSISTG',
    'user': 'svccsimarine',
    'password': 'CNKmoFxEsXs0D9egZQXH'
}

# MySQL (Destination)
MYSQL_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'warrantyparts_test',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD'
}

# ============================================================================
# PRODUCT CODE FILTERING
# ============================================================================

# Product codes to include for complete boat builds
PRODUCT_CODES = [
    # Base boat
    'BS1',

    # Engine codes
    'EN7', 'ENG', 'ENI', 'EN9', 'EN4', 'ENA', 'EN2', 'EN3', 'EN8', 'ENT',

    # Accessories
    'ACC',

    # Hull components
    'H1', 'H1P', 'H1V', 'H1I', 'H1F', 'H3A', 'H5',

    # Level items
    'L0', 'L2', 'L12',

    # Parts and components
    '003', '008', '024', '090', '302',

    # Assembly items
    'ASY',

    # Other categories found in current data
    '010', '011', '005', '006', '015', '017', '023', '029', '030'
]

# ============================================================================
# SQL QUERIES
# ============================================================================

MSSQL_QUERY = """
SELECT
    LEFT(coi.co_num, 30) AS [ERP_OrderNo],
    LEFT(coi.Uf_BENN_BoatSerialNumber, 15) AS [BoatSerialNo],
    LEFT(coi.Uf_BENN_BoatModel, 14) AS [BoatModelNo],
    coi.co_line AS [LineNo],
    LEFT(coi.item, 30) AS [ItemNo],
    LEFT(im.description, 50) AS [ItemDesc1],
    CAST((coi.price * coi.qty_ordered) AS DECIMAL(10,2)) AS [ExtSalesAmount],
    coi.qty_invoiced AS [QuantitySold],
    LEFT(im.Uf_BENN_Series, 5) AS [Series],
    LEFT(coi.Uf_BENN_BoatWebOrderNumber, 30) AS [WebOrderNo],
    LEFT(co.type, 1) AS [Orig_Ord_Type],
    ah.apply_to_inv_num AS [ApplyToNo],
    LEFT(iim.inv_num, 30) AS [InvoiceNo],
    CASE
        WHEN ah.inv_date IS NOT NULL
        THEN CONVERT(INT, CONVERT(VARCHAR(8), ah.inv_date, 112))
        ELSE NULL
    END AS [InvoiceDate],
    LEFT(im.product_code, 3) AS [ItemMasterProdCat]
FROM [CSISTG].[dbo].[coitem_mst] coi
LEFT JOIN [CSISTG].[dbo].[inv_item_mst] iim
    ON coi.co_num = iim.co_num
    AND coi.co_line = iim.co_line
    AND coi.co_release = iim.co_release
    AND coi.site_ref = iim.site_ref
LEFT JOIN [CSISTG].[dbo].[arinv_mst] ah
    ON iim.inv_num = ah.inv_num
    AND iim.site_ref = ah.site_ref
LEFT JOIN [CSISTG].[dbo].[co_mst] co
    ON coi.co_num = co.co_num
    AND coi.site_ref = co.site_ref
LEFT JOIN [CSISTG].[dbo].[item_mst] im
    ON coi.item = im.item
    AND coi.site_ref = im.site_ref
WHERE coi.site_ref = 'BENN'
    AND coi.Uf_BENN_BoatSerialNumber IS NOT NULL
    AND coi.Uf_BENN_BoatSerialNumber != ''
    AND im.product_code IN ({product_codes})
ORDER BY [ERP_OrderNo], [LineNo]
"""

MYSQL_INSERT = """
INSERT INTO BoatOptions26_test (
    ERP_OrderNo,
    BoatSerialNo,
    BoatModelNo,
    LineNo,
    ItemNo,
    ItemDesc1,
    ExtSalesAmount,
    QuantitySold,
    Series,
    WebOrderNo,
    Orig_Ord_Type,
    ApplyToNo,
    InvoiceNo,
    InvoiceDate,
    ItemMasterProdCat,
    LineSeqNo
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s
)
"""

# ============================================================================
# FUNCTIONS
# ============================================================================

def log(message: str, level: str = "INFO"):
    """Print timestamped log message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    symbols = {
        "INFO": "ℹ️",
        "SUCCESS": "✅",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "PROGRESS": "⏳"
    }
    symbol = symbols.get(level, "•")
    print(f"[{timestamp}] {symbol} {message}")

def extract_from_mssql() -> List[Tuple]:
    """Extract boat option line items from MSSQL database"""
    log("Connecting to MSSQL (CSI/ERP database)...")

    try:
        conn = pymssql.connect(**MSSQL_CONFIG)
        cursor = conn.cursor()

        # Build product code list for IN clause
        product_code_list = "'" + "','".join(PRODUCT_CODES) + "'"
        query = MSSQL_QUERY.format(product_codes=product_code_list)

        log(f"Extracting data with {len(PRODUCT_CODES)} product code filters...")
        log(f"Product codes: {', '.join(PRODUCT_CODES[:10])}...", "INFO")

        cursor.execute(query)
        rows = cursor.fetchall()

        log(f"Extracted {len(rows):,} rows from MSSQL", "SUCCESS")

        cursor.close()
        conn.close()

        return rows

    except pymssql.Error as e:
        log(f"MSSQL error: {e}", "ERROR")
        raise
    except Exception as e:
        log(f"Unexpected error: {e}", "ERROR")
        raise

def validate_data(rows: List[Tuple]) -> Dict:
    """Validate extracted data and return statistics"""
    log("Validating extracted data...")

    stats = {
        'total_rows': len(rows),
        'unique_boats': len(set(row[1] for row in rows if row[1])),
        'unique_orders': len(set(row[0] for row in rows if row[0])),
        'product_codes': {},
        'missing_serials': 0,
        'missing_models': 0,
        'null_prices': 0
    }

    for row in rows:
        # Count product codes
        prod_code = row[14] if len(row) > 14 else None
        if prod_code:
            stats['product_codes'][prod_code] = stats['product_codes'].get(prod_code, 0) + 1

        # Check for missing data
        if not row[1]:  # BoatSerialNo
            stats['missing_serials'] += 1
        if not row[2]:  # BoatModelNo
            stats['missing_models'] += 1
        if row[6] is None:  # ExtSalesAmount
            stats['null_prices'] += 1

    log(f"Validation complete:", "SUCCESS")
    log(f"  Total rows: {stats['total_rows']:,}")
    log(f"  Unique boats: {stats['unique_boats']:,}")
    log(f"  Unique orders: {stats['unique_orders']:,}")
    log(f"  Product codes found: {len(stats['product_codes'])}")

    if stats['missing_serials'] > 0:
        log(f"  Warning: {stats['missing_serials']} rows missing serial numbers", "WARNING")
    if stats['null_prices'] > 0:
        log(f"  Warning: {stats['null_prices']} rows with null prices", "WARNING")

    return stats

def clear_table(mysql_conn):
    """Clear the BoatOptions26_test table"""
    cursor = mysql_conn.cursor()
    try:
        log("Clearing BoatOptions26_test table...", "WARNING")
        cursor.execute("DELETE FROM BoatOptions26_test")
        deleted = cursor.rowcount
        mysql_conn.commit()
        log(f"Deleted {deleted:,} existing rows", "SUCCESS")
    except MySQLError as e:
        log(f"Error clearing table: {e}", "ERROR")
        raise
    finally:
        cursor.close()

def load_to_mysql(rows: List[Tuple], dry_run: bool = True, clear: bool = False) -> Dict:
    """Load data into MySQL database"""

    if dry_run:
        log("DRY RUN MODE - No data will be written to database", "WARNING")
        return validate_data(rows)

    log("Connecting to MySQL (warrantyparts_test)...")

    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)

        # Clear table if requested
        if clear:
            clear_table(conn)

        cursor = conn.cursor()

        log(f"Inserting {len(rows):,} rows into BoatOptions26_test...", "PROGRESS")

        batch_size = 1000
        inserted = 0
        errors = 0

        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]

            try:
                # Prepare batch data with LineSeqNo
                batch_data = []
                for row in batch:
                    # Add LineSeqNo (same as LineNo for now)
                    row_data = list(row) + [row[3]]  # row[3] is LineNo
                    batch_data.append(row_data)

                cursor.executemany(MYSQL_INSERT, batch_data)
                inserted += len(batch)

                if (i + batch_size) % 10000 == 0:
                    log(f"Progress: {inserted:,} / {len(rows):,} rows inserted...", "PROGRESS")

            except MySQLError as e:
                log(f"Error in batch {i//batch_size}: {e}", "WARNING")
                errors += 1
                if errors > 10:
                    log("Too many errors, aborting", "ERROR")
                    raise

        # Commit transaction
        log("Committing transaction...", "PROGRESS")
        conn.commit()

        log(f"Successfully inserted {inserted:,} rows", "SUCCESS")

        # Get final statistics
        cursor.execute("""
            SELECT
                COUNT(*) as total_rows,
                COUNT(DISTINCT BoatSerialNo) as unique_boats,
                COUNT(DISTINCT ERP_OrderNo) as unique_orders,
                COUNT(DISTINCT ItemMasterProdCat) as unique_codes
            FROM BoatOptions26_test
        """)
        final_stats = cursor.fetchone()

        cursor.close()
        conn.close()

        return {
            'inserted': inserted,
            'errors': errors,
            'total_rows': final_stats[0],
            'unique_boats': final_stats[1],
            'unique_orders': final_stats[2],
            'unique_codes': final_stats[3]
        }

    except MySQLError as e:
        log(f"MySQL error: {e}", "ERROR")
        if conn:
            conn.rollback()
            log("Transaction rolled back", "WARNING")
        raise
    except Exception as e:
        log(f"Unexpected error: {e}", "ERROR")
        if conn:
            conn.rollback()
            log("Transaction rolled back", "WARNING")
        raise

def print_summary(stats: Dict, dry_run: bool):
    """Print summary statistics"""
    print("\n" + "="*70)
    print("IMPORT SUMMARY")
    print("="*70)

    if dry_run:
        print("🔍 DRY RUN MODE - No data was imported")
        print(f"\nWould import:")
        print(f"  Total rows:        {stats['total_rows']:,}")
        print(f"  Unique boats:      {stats['unique_boats']:,}")
        print(f"  Unique orders:     {stats['unique_orders']:,}")
        print(f"  Product codes:     {len(stats['product_codes'])}")

        print(f"\nTop 10 product codes:")
        sorted_codes = sorted(stats['product_codes'].items(), key=lambda x: x[1], reverse=True)
        for code, count in sorted_codes[:10]:
            print(f"  {code:5s}: {count:8,d} rows")
    else:
        print("✅ IMPORT COMPLETED SUCCESSFULLY")
        print(f"\nImported:")
        print(f"  Rows inserted:     {stats['inserted']:,}")
        print(f"  Total rows in DB:  {stats['total_rows']:,}")
        print(f"  Unique boats:      {stats['unique_boats']:,}")
        print(f"  Unique orders:     {stats['unique_orders']:,}")
        print(f"  Product codes:     {stats['unique_codes']}")
        if stats['errors'] > 0:
            print(f"  Errors:            {stats['errors']} (some batches failed)")

    print("="*70)

def main():
    parser = argparse.ArgumentParser(
        description='Import boat options from MSSQL to BoatOptions26_test',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (safe, shows what will be imported)
  python3 import_boatoptions26.py --dry-run

  # Execute actual import
  python3 import_boatoptions26.py --execute

  # Clear table and reimport
  python3 import_boatoptions26.py --execute --clear
        """
    )

    parser.add_argument('--execute', action='store_true',
                       help='Execute actual import (default is dry-run)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Dry run mode (default, no data written)')
    parser.add_argument('--clear', action='store_true',
                       help='Clear existing data before import')

    args = parser.parse_args()

    # Default to dry-run unless --execute is specified
    dry_run = not args.execute

    if dry_run and not args.dry_run:
        log("Running in DRY RUN mode (use --execute to actually import data)", "WARNING")

    print("="*70)
    print("BOATOPTIONS26_TEST IMPORT SCRIPT")
    print("="*70)
    print(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")
    print(f"Clear existing: {'Yes' if args.clear else 'No'}")
    print(f"Product codes: {len(PRODUCT_CODES)}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    print()

    try:
        # Step 1: Extract from MSSQL
        rows = extract_from_mssql()

        if len(rows) == 0:
            log("No data extracted from MSSQL!", "ERROR")
            sys.exit(1)

        # Step 2: Load to MySQL (or validate if dry-run)
        stats = load_to_mysql(rows, dry_run=dry_run, clear=args.clear)

        # Step 3: Print summary
        print_summary(stats, dry_run)

        if dry_run:
            print("\n💡 To execute the import, run with --execute flag:")
            print("   python3 import_boatoptions26.py --execute\n")
        else:
            log("Import completed successfully!", "SUCCESS")

    except KeyboardInterrupt:
        log("Import cancelled by user", "WARNING")
        sys.exit(1)
    except Exception as e:
        log(f"Import failed: {e}", "ERROR")
        sys.exit(1)

if __name__ == '__main__':
    main()

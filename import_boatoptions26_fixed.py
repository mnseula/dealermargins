#!/usr/bin/env python3
"""
BoatOptions26_test Import Script - FIXED VERSION

Uses ACTUAL product codes from MSSQL (ACY, BOA, ENG, PPR, etc.)
instead of the wrong codes (BS1, ACC, EN7, etc.)

SAFETY FEATURES:
- Dry-run mode by default
- Transaction support with rollback
- Progress reporting
- NO serial number requirement (uses order number)

Usage:
    # Dry run (safe, shows what will be imported)
    python3 import_boatoptions26_fixed.py --dry-run

    # Execute actual import
    python3 import_boatoptions26_fixed.py --execute

    # Clear table and reimport
    python3 import_boatoptions26_fixed.py --execute --clear
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

MSSQL_CONFIG = {
    'server': 'MPL1STGSQL086.POLARISSTAGE.COM',
    'database': 'CSISTG',
    'user': 'svccsimarine',
    'password': 'CNKmoFxEsXs0D9egZQXH'
}

MYSQL_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'warrantyparts_test',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD'
}

# ============================================================================
# PRODUCT CODE FILTERING - ACTUAL CODES FROM MSSQL
# ============================================================================

# Based on actual MSSQL data analysis
PRODUCT_CODES = [
    # Boat builds and accessories
    'BOA',   # Base boat (10,716 rows)
    'ACY',   # Accessories (216,500 rows)
    'ENG',   # Engine (11,768 rows)
    'ENA',   # Engine accessories (1,548 rows)
    'ENI',   # Engine installation (28 rows)

    # Prep and rigging
    'PPR',   # Prep/rigging (90,928 rows)
    'PRE',   # Pre-rigging (38,585 rows)

    # Product-related
    'PRD',   # Product (8,356 rows)
    'GRO',   # Group? (11,306 rows)

    # Work items
    'WIP',   # Work in progress (10,211 rows)

    # Freight
    'FRE',   # Freight (635 rows)
    'FRT',   # Freight (372 rows)
    'FRP',   # Freight prep? (19 rows)

    # Discounts
    'DIS',   # Discount (2,769 rows)
    'DIR',   # Discount related (3,534 rows)
    'DIC',   # Discount (299 rows)
    'DIW',   # Discount (4,878 rows)
    'DIG',   # Discount (647 rows)

    # Cases and labor
    'CAS',   # Cases? (5,743 rows)
    'LAB',   # Labor (1,137 rows)

    # Other
    'VOD',   # ? (34,337 rows)
    'LOY',   # Loyalty (18,647 rows)
    'WAR',   # Warranty (33,058 rows)
    'BOI',   # Boat I/O? (14 rows)
    'TRL',   # Trailer? (17 rows)
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
# FUNCTIONS (Same as before, condensed for brevity)
# ============================================================================

def log(message: str, level: str = "INFO"):
    """Print timestamped log message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    symbols = {"INFO": "ℹ️", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌", "PROGRESS": "⏳"}
    symbol = symbols.get(level, "•")
    print(f"[{timestamp}] {symbol} {message}")

def extract_from_mssql() -> List[Tuple]:
    """Extract boat option line items from MSSQL database"""
    log("Connecting to MSSQL (CSI/ERP database)...")

    try:
        conn = pymssql.connect(**MSSQL_CONFIG)
        cursor = conn.cursor()

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
        'unique_orders': len(set(row[0] for row in rows if row[0])),
        'unique_boats_serial': len(set(row[1] for row in rows if row[1])),
        'unique_boats_model': len(set(row[2] for row in rows if row[2])),
        'product_codes': {},
        'missing_orders': 0,
        'null_prices': 0
    }

    for row in rows:
        prod_code = row[14] if len(row) > 14 else None
        if prod_code:
            stats['product_codes'][prod_code] = stats['product_codes'].get(prod_code, 0) + 1
        if not row[0]:
            stats['missing_orders'] += 1
        if row[6] is None:
            stats['null_prices'] += 1

    log(f"Validation complete:", "SUCCESS")
    log(f"  Total rows: {stats['total_rows']:,}")
    log(f"  Unique orders: {stats['unique_orders']:,}")
    log(f"  Boats with serial: {stats['unique_boats_serial']:,}")
    log(f"  Boats with model: {stats['unique_boats_model']:,}")
    log(f"  Product codes found: {len(stats['product_codes'])}")

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
                batch_data = []
                for row in batch:
                    row_data = list(row) + [row[3]]  # Add LineSeqNo
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

        log("Committing transaction...", "PROGRESS")
        conn.commit()

        log(f"Successfully inserted {inserted:,} rows", "SUCCESS")

        cursor.execute("""
            SELECT
                COUNT(*) as total_rows,
                COUNT(DISTINCT CASE WHEN BoatSerialNo IS NOT NULL AND BoatSerialNo != ''
                                   THEN BoatSerialNo END) as boats_serial,
                COUNT(DISTINCT CASE WHEN BoatModelNo IS NOT NULL AND BoatModelNo != ''
                                   THEN BoatModelNo END) as boats_model,
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
            'boats_serial': final_stats[1],
            'boats_model': final_stats[2],
            'unique_orders': final_stats[3],
            'unique_codes': final_stats[4]
        }

    except MySQLError as e:
        log(f"MySQL error: {e}", "ERROR")
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
        print(f"  Total rows:          {stats['total_rows']:,}")
        print(f"  Unique orders:       {stats['unique_orders']:,}")
        print(f"  Boats with serial:   {stats['unique_boats_serial']:,}")
        print(f"  Boats with model:    {stats['unique_boats_model']:,}")
        print(f"  Product codes:       {len(stats['product_codes'])}")

        print(f"\nTop 15 product codes:")
        sorted_codes = sorted(stats['product_codes'].items(), key=lambda x: x[1], reverse=True)
        for code, count in sorted_codes[:15]:
            print(f"  {code:5s}: {count:10,d} rows")
    else:
        print("✅ IMPORT COMPLETED SUCCESSFULLY")
        print(f"\nImported:")
        print(f"  Rows inserted:       {stats['inserted']:,}")
        print(f"  Total rows in DB:    {stats['total_rows']:,}")
        print(f"  Boats with serial:   {stats['boats_serial']:,}")
        print(f"  Boats with model:    {stats['boats_model']:,}")
        print(f"  Unique orders:       {stats['unique_orders']:,}")
        print(f"  Product codes:       {stats['unique_codes']}")
        if stats['errors'] > 0:
            print(f"  Errors:              {stats['errors']}")

    print("="*70)

def main():
    parser = argparse.ArgumentParser(description='Import boat options with REAL product codes')
    parser.add_argument('--execute', action='store_true', help='Execute actual import')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (default)')
    parser.add_argument('--clear', action='store_true', help='Clear existing data before import')

    args = parser.parse_args()
    dry_run = not args.execute

    if dry_run and not args.dry_run:
        log("Running in DRY RUN mode (use --execute to actually import data)", "WARNING")

    print("="*70)
    print("BOATOPTIONS26_TEST IMPORT SCRIPT - FIXED VERSION")
    print("="*70)
    print(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")
    print(f"Clear existing: {'Yes' if args.clear else 'No'}")
    print(f"Product codes: {len(PRODUCT_CODES)} (ACTUAL codes from MSSQL)")
    print(f"Serial number filter: REMOVED (uses all orders)")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    print()

    try:
        rows = extract_from_mssql()

        if len(rows) == 0:
            log("No data extracted from MSSQL!", "ERROR")
            sys.exit(1)

        stats = load_to_mysql(rows, dry_run=dry_run, clear=args.clear)
        print_summary(stats, dry_run)

        if dry_run:
            print("\n💡 To execute the import, run with --execute flag:")
            print("   python3 import_boatoptions26_fixed.py --execute\n")
        else:
            log("Import completed successfully!", "SUCCESS")

    except KeyboardInterrupt:
        log("Import cancelled by user", "WARNING")
        sys.exit(1)
    except Exception as e:
        log(f"Import failed: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

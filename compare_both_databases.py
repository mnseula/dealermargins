#!/usr/bin/env python3
"""Compare dealer 333834 across both databases"""
import mysql.connector

def check_dealer_in_database(database_name, dealer_id):
    """Check dealer in specified database"""
    DB_CONFIG = {
        'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
        'user': 'awsmaster',
        'password': 'VWvHG9vfG23g7gD',
        'database': database_name
    }

    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        print(f"\n{'='*80}")
        print(f"DATABASE: {database_name}")
        print(f"{'='*80}")

        # First check if DealerMargins table exists
        cursor.execute("SHOW TABLES LIKE 'DealerMargins'")
        table_exists = cursor.fetchone()

        if not table_exists:
            print(f"❌ DealerMargins table does NOT exist in {database_name}")
            cursor.close()
            connection.close()
            return

        print(f"✓ DealerMargins table exists")

        # Check table structure
        cursor.execute("DESCRIBE DealerMargins")
        columns = cursor.fetchall()
        print(f"✓ Table has {len(columns)} columns")

        # Check if it's wide format (with Q_BASE_BOAT) or normalized format
        column_names = [col['Field'] for col in columns]
        is_wide_format = 'Q_BASE_BOAT' in column_names
        is_normalized = 'dealer_id' in column_names and 'series_id' in column_names

        if is_wide_format:
            print(f"✓ Format: WIDE (separate columns per series)")

            # Query dealer
            query = """
                SELECT DealerID, Dealership,
                       Q_BASE_BOAT, Q_ENGINE, Q_OPTIONS, Q_FREIGHT, Q_PREP, Q_VOL_DISC,
                       R_BASE_BOAT, R_ENGINE, R_OPTIONS, R_FREIGHT, R_PREP, R_VOL_DISC
                FROM DealerMargins
                WHERE DealerID = %s
            """
            cursor.execute(query, (dealer_id,))
            result = cursor.fetchone()

            if result:
                print(f"✓ Found dealer: {result['Dealership']}")
                print(f"\n  Q Series: Base={result['Q_BASE_BOAT']}%, Engine={result['Q_ENGINE']}%, Options={result['Q_OPTIONS']}%, Vol={result['Q_VOL_DISC']}%")
                print(f"           Freight=${result['Q_FREIGHT']:,.0f}, Prep=${result['Q_PREP']:,.0f}")
                print(f"\n  R Series: Base={result['R_BASE_BOAT']}%, Engine={result['R_ENGINE']}%, Options={result['R_OPTIONS']}%, Vol={result['R_VOL_DISC']}%")
                print(f"           Freight=${result['R_FREIGHT']:,.0f}, Prep=${result['R_PREP']:,.0f}")
            else:
                print(f"❌ Dealer {dealer_id} NOT FOUND")

        elif is_normalized:
            print(f"✓ Format: NORMALIZED (separate rows per dealer-series)")

            # Query dealer
            query = """
                SELECT dealer_id, series_id,
                       base_boat_margin, engine_margin, options_margin, volume_discount,
                       freight_margin, prep_margin, enabled, effective_date, end_date
                FROM DealerMargins
                WHERE dealer_id = %s AND end_date IS NULL
                ORDER BY series_id
            """
            cursor.execute(query, (dealer_id,))
            results = cursor.fetchall()

            if results:
                print(f"✓ Found {len(results)} active margin records for dealer {dealer_id}")
                for row in results:
                    print(f"\n  {row['series_id']} Series: Base={row['base_boat_margin']}%, Engine={row['engine_margin']}%, Options={row['options_margin']}%, Vol={row['volume_discount']}%")
                    print(f"           Freight={row['freight_margin']}%, Prep={row['prep_margin']}%, Enabled={row['enabled']}")
            else:
                print(f"❌ Dealer {dealer_id} NOT FOUND")
        else:
            print(f"⚠️  Unknown table format")
            print(f"   Columns: {', '.join(column_names[:10])}...")

        cursor.close()
        connection.close()

    except mysql.connector.Error as e:
        print(f"❌ Database error: {e}")
        if connection and connection.is_connected():
            connection.close()

def main():
    """Compare dealer across both databases"""
    print("\n" + "="*80)
    print("COMPARING DEALER 333834 ACROSS DATABASES")
    print("="*80)

    # Check both databases
    check_dealer_in_database('warrantyparts', '333834')
    check_dealer_in_database('warrantyparts_test', '333834')

    # Also check with leading zeros
    print("\n" + "="*80)
    print("ALSO CHECKING WITH LEADING ZEROS (00333834)")
    print("="*80)

    check_dealer_in_database('warrantyparts', '00333834')
    check_dealer_in_database('warrantyparts_test', '00333834')

if __name__ == "__main__":
    main()

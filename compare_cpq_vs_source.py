#!/usr/bin/env python3
"""Compare CPQ table vs Source table"""
import mysql.connector

def compare_tables():
    """Compare the two DealerMargins tables"""

    print("\n" + "="*80)
    print("COMPARISON: CPQ TABLE vs SOURCE TABLE")
    print("="*80)

    # Check warrantyparts_test (CPQ table)
    cpq_config = {
        'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
        'user': 'awsmaster',
        'password': 'VWvHG9vfG23g7gD',
        'database': 'warrantyparts_test'
    }

    # Check warrantyparts (Source table)
    source_config = {
        'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
        'user': 'awsmaster',
        'password': 'VWvHG9vfG23g7gD',
        'database': 'warrantyparts'
    }

    try:
        # CPQ Table
        cpq_conn = mysql.connector.connect(**cpq_config)
        cpq_cursor = cpq_conn.cursor(dictionary=True)

        cpq_cursor.execute("SELECT COUNT(DISTINCT dealer_id) as dealer_count FROM DealerMargins WHERE end_date IS NULL")
        cpq_dealers = cpq_cursor.fetchone()['dealer_count']

        cpq_cursor.execute("SELECT COUNT(*) as total FROM DealerMargins WHERE end_date IS NULL")
        cpq_records = cpq_cursor.fetchone()['total']

        # Source Table
        source_conn = mysql.connector.connect(**source_config)
        source_cursor = source_conn.cursor(dictionary=True)

        source_cursor.execute("SELECT COUNT(*) as total FROM DealerMargins")
        source_dealers = source_cursor.fetchone()['total']

        print(f"\nwarrantyparts_test.DealerMargins (CPQ Table - FROM API):")
        print(f"  Total dealers: {cpq_dealers}")
        print(f"  Total records: {cpq_records}")
        print(f"  Format: NORMALIZED (one row per dealer-series)")
        print(f"  Freight/Prep: PERCENTAGES (e.g., 27.00%)")

        print(f"\nwarrantyparts.DealerMargins (Source Table - TO API):")
        print(f"  Total dealers: {source_dealers}")
        print(f"  Format: WIDE (one row per dealer, columns per series)")
        print(f"  Freight/Prep: DOLLAR AMOUNTS (e.g., $1,500, $1,000)")

        # Check if there's overlap
        print("\n" + "="*80)
        print("CHECKING FOR OVERLAPPING DEALERS")
        print("="*80)

        cpq_cursor.execute("SELECT DISTINCT dealer_id FROM DealerMargins WHERE end_date IS NULL ORDER BY dealer_id LIMIT 10")
        cpq_dealer_ids = [row['dealer_id'] for row in cpq_cursor.fetchall()]

        print(f"\nFirst 10 dealer IDs in CPQ table: {', '.join(cpq_dealer_ids)}")

        # Check if these exist in source
        for dealer_id in cpq_dealer_ids[:3]:
            source_cursor.execute("SELECT DealerID, Dealership FROM DealerMargins WHERE DealerID = %s", (dealer_id,))
            result = source_cursor.fetchone()
            if result:
                print(f"  {dealer_id}: EXISTS in source table - {result['Dealership']}")
            else:
                print(f"  {dealer_id}: NOT FOUND in source table")

        # Show key difference with example
        print("\n" + "="*80)
        print("KEY DIFFERENCE: FREIGHT & PREP STORAGE")
        print("="*80)

        cpq_cursor.execute("""
            SELECT dealer_id, series_id, freight_margin, prep_margin
            FROM DealerMargins
            WHERE end_date IS NULL
            LIMIT 1
        """)
        cpq_example = cpq_cursor.fetchone()

        source_cursor.execute("""
            SELECT DealerID, Q_FREIGHT, Q_PREP
            FROM DealerMargins
            LIMIT 1
        """)
        source_example = source_cursor.fetchone()

        print(f"\nCPQ Table Example:")
        print(f"  Dealer: {cpq_example['dealer_id']}, Series: {cpq_example['series_id']}")
        print(f"  freight_margin: {cpq_example['freight_margin']}% (percentage)")
        print(f"  prep_margin: {cpq_example['prep_margin']}% (percentage)")

        print(f"\nSource Table Example:")
        print(f"  Dealer: {source_example['DealerID']}")
        print(f"  Q_FREIGHT: ${source_example['Q_FREIGHT']:,.2f} (dollar amount)")
        print(f"  Q_PREP: ${source_example['Q_PREP']:,.2f} (dollar amount)")

        cpq_cursor.close()
        cpq_conn.close()
        source_cursor.close()
        source_conn.close()

    except mysql.connector.Error as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    compare_tables()

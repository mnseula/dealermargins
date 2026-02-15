#!/usr/bin/env python3
"""Check the CPQ DealerMargins table in warrantyparts_test"""
import mysql.connector

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts_test'
}

def check_cpq_dealermargins():
    """Check CPQ DealerMargins table"""
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        print("\n" + "="*80)
        print("CPQ DEALERMARGINS TABLE (warrantyparts_test.DealerMargins)")
        print("="*80)

        # Get table structure
        cursor.execute("DESCRIBE DealerMargins")
        columns = cursor.fetchall()
        print(f"\nTable Structure ({len(columns)} columns):")
        for col in columns:
            print(f"  {col['Field']:<25} {col['Type']:<20} {col['Null']:<5} {col['Key']}")

        # Get total count
        cursor.execute("SELECT COUNT(*) as total FROM DealerMargins WHERE end_date IS NULL")
        total = cursor.fetchone()['total']
        print(f"\nTotal Active Records (end_date IS NULL): {total}")

        # Get sample data
        print("\n" + "="*80)
        print("SAMPLE DATA (First 10 records)")
        print("="*80)

        cursor.execute("""
            SELECT dealer_id, series_id,
                   base_boat_margin, engine_margin, options_margin, volume_discount,
                   freight_margin, prep_margin, enabled, year
            FROM DealerMargins
            WHERE end_date IS NULL
            ORDER BY dealer_id, series_id
            LIMIT 10
        """)

        results = cursor.fetchall()
        if results:
            for row in results:
                print(f"\nDealer: {row['dealer_id']}, Series: {row['series_id']}, Year: {row['year']}")
                print(f"  Base: {row['base_boat_margin']}%, Engine: {row['engine_margin']}%, Options: {row['options_margin']}%, Vol: {row['volume_discount']}%")
                print(f"  Freight: {row['freight_margin']}%, Prep: {row['prep_margin']}%, Enabled: {row['enabled']}")

        # Search for NICHOLS dealers
        print("\n" + "="*80)
        print("NICHOLS DEALERS IN CPQ TABLE")
        print("="*80)

        cursor.execute("""
            SELECT dm.dealer_id, d.dealer_name, dm.series_id,
                   dm.base_boat_margin, dm.engine_margin, dm.options_margin, dm.volume_discount,
                   dm.freight_margin, dm.prep_margin, dm.enabled, dm.year
            FROM DealerMargins dm
            JOIN Dealers d ON dm.dealer_id = d.dealer_id
            WHERE d.dealer_name LIKE '%NICHOLS%'
              AND dm.end_date IS NULL
            ORDER BY d.dealer_name, dm.series_id
        """)

        nichols = cursor.fetchall()
        if nichols:
            print(f"\nFound {len(nichols)} NICHOLS margin records:")
            current_dealer = None
            for row in nichols:
                if row['dealer_name'] != current_dealer:
                    current_dealer = row['dealer_name']
                    print(f"\n{row['dealer_id']}: {row['dealer_name']}")
                print(f"  {row['series_id']:5} - Base:{row['base_boat_margin']:5}% Engine:{row['engine_margin']:5}% Options:{row['options_margin']:5}% Vol:{row['volume_discount']:5}% | Freight:{row['freight_margin']:5}% Prep:{row['prep_margin']:5}% | Enabled:{row['enabled']} Year:{row['year']}")
        else:
            print("\nNo NICHOLS dealers found")

        # Search for dealer 333834 or 00333834
        print("\n" + "="*80)
        print("SEARCHING FOR DEALER 333834 / 00333834")
        print("="*80)

        for dealer_id in ['333834', '00333834']:
            cursor.execute("""
                SELECT dm.dealer_id, d.dealer_name, dm.series_id,
                       dm.base_boat_margin, dm.engine_margin, dm.options_margin, dm.volume_discount,
                       dm.freight_margin, dm.prep_margin, dm.enabled, dm.year
                FROM DealerMargins dm
                JOIN Dealers d ON dm.dealer_id = d.dealer_id
                WHERE dm.dealer_id = %s
                  AND dm.end_date IS NULL
                ORDER BY dm.series_id
            """, (dealer_id,))

            results = cursor.fetchall()
            if results:
                print(f"\nFound dealer {dealer_id}: {results[0]['dealer_name']}")
                for row in results:
                    print(f"  {row['series_id']:5} - Base:{row['base_boat_margin']:5}% Engine:{row['engine_margin']:5}% Options:{row['options_margin']:5}% Vol:{row['volume_discount']:5}% | Freight:{row['freight_margin']:5}% Prep:{row['prep_margin']:5}%")
            else:
                print(f"\nDealer {dealer_id} NOT FOUND")

        cursor.close()
        connection.close()

    except mysql.connector.Error as e:
        print(f"❌ Database error: {e}")
        if connection and connection.is_connected():
            connection.close()

if __name__ == "__main__":
    check_cpq_dealermargins()

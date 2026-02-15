#!/usr/bin/env python3
"""Check Shorts Marine Sales dealer margins"""
import mysql.connector

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts'
}

def check_shorts_marine():
    """Check Shorts Marine Sales dealer margins"""
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        # Search for Shorts Marine
        query = """
            SELECT DealerID, Dealership,
                   Q_BASE_BOAT, Q_ENGINE, Q_OPTIONS, Q_FREIGHT, Q_PREP, Q_VOL_DISC,
                   QX_BASE_BOAT, QX_ENGINE, QX_OPTIONS, QX_FREIGHT, QX_PREP, QX_VOL_DISC,
                   R_BASE_BOAT, R_ENGINE, R_OPTIONS, R_FREIGHT, R_PREP, R_VOL_DISC,
                   S_BASE_BOAT, S_ENGINE, S_OPTIONS, S_FREIGHT, S_PREP, S_VOL_DISC,
                   L_BASE_BOAT, L_ENGINE, L_OPTIONS, L_FREIGHT, L_PREP, L_VOL_DISC,
                   M_BASE_BOAT, M_ENGINE, M_OPTIONS, M_FREIGHT, M_PREP, M_VOL_DISC
            FROM DealerMargins
            WHERE Dealership LIKE '%SHORTS%MARINE%'
               OR Dealership LIKE '%SHORT%MARINE%'
            ORDER BY Dealership
        """

        cursor.execute(query)
        results = cursor.fetchall()

        if results:
            print(f"\n{'='*80}")
            print(f"FOUND {len(results)} DEALER(S) MATCHING 'SHORTS MARINE'")
            print(f"{'='*80}\n")

            for idx, dealer in enumerate(results, 1):
                print(f"{'='*80}")
                print(f"#{idx} - {dealer['Dealership']} (ID: {dealer['DealerID']})")
                print(f"{'='*80}\n")

                series_list = ['Q', 'QX', 'R', 'S', 'L', 'M']

                for series in series_list:
                    base_col = f"{series}_BASE_BOAT"
                    engine_col = f"{series}_ENGINE"
                    options_col = f"{series}_OPTIONS"
                    vol_col = f"{series}_VOL_DISC"
                    freight_col = f"{series}_FREIGHT"
                    prep_col = f"{series}_PREP"

                    # Get values
                    base = dealer[base_col] if dealer[base_col] else 0
                    engine = dealer[engine_col] if dealer[engine_col] else 0
                    options = dealer[options_col] if dealer[options_col] else 0
                    vol = dealer[vol_col] if dealer[vol_col] else 0
                    freight = dealer[freight_col] if dealer[freight_col] else 0
                    prep = dealer[prep_col] if dealer[prep_col] else 0

                    # Only show if has any non-zero values
                    if base or engine or options or vol or freight or prep:
                        print(f"{series} Series:")
                        print(f"  Base Boat:        {base}%")
                        print(f"  Engine:           {engine}%")
                        print(f"  Options:          {options}%")
                        print(f"  Volume Discount:  {vol}%")
                        print(f"  Freight:          ${freight:,.2f}")
                        print(f"  Prep:             ${prep:,.2f}")
                        print()

        else:
            print("\n❌ No dealers found matching 'SHORTS MARINE'")

            # Try broader search
            print("\nSearching for any dealer with 'SHORT' in name...")
            cursor.execute("""
                SELECT DealerID, Dealership
                FROM DealerMargins
                WHERE Dealership LIKE '%SHORT%'
                ORDER BY Dealership
            """)

            short_results = cursor.fetchall()
            if short_results:
                print(f"\nFound {len(short_results)} dealers with 'SHORT' in name:")
                for row in short_results:
                    print(f"  {row['DealerID']}: {row['Dealership']}")
            else:
                print("\nNo dealers found with 'SHORT' in name")

        cursor.close()

    except mysql.connector.Error as e:
        print(f"❌ Database error: {e}")
    finally:
        if connection and connection.is_connected():
            connection.close()

if __name__ == "__main__":
    check_shorts_marine()

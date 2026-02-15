#!/usr/bin/env python3
"""Check NICHOLS MARINE SE OK LLC dealer margins"""
import mysql.connector

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts'
}

def check_dealer():
    """Check specific dealer margins"""
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        # Look up dealer 00333834
        query = """
            SELECT DealerID, Dealership,
                   Q_BASE_BOAT, Q_ENGINE, Q_OPTIONS, Q_FREIGHT, Q_PREP, Q_VOL_DISC,
                   QX_BASE_BOAT, QX_ENGINE, QX_OPTIONS, QX_FREIGHT, QX_PREP, QX_VOL_DISC,
                   R_BASE_BOAT, R_ENGINE, R_OPTIONS, R_FREIGHT, R_PREP, R_VOL_DISC,
                   S_BASE_BOAT, S_ENGINE, S_OPTIONS, S_FREIGHT, S_PREP, S_VOL_DISC,
                   L_BASE_BOAT, L_ENGINE, L_OPTIONS, L_FREIGHT, L_PREP, L_VOL_DISC,
                   M_BASE_BOAT, M_ENGINE, M_OPTIONS, M_FREIGHT, M_PREP, M_VOL_DISC
            FROM DealerMargins
            WHERE DealerID = '00333834'
        """

        cursor.execute(query)
        result = cursor.fetchone()

        if result:
            print(f"\n{'='*80}")
            print(f"Dealer: {result['Dealership']} (ID: {result['DealerID']})")
            print(f"{'='*80}\n")

            series_list = ['Q', 'QX', 'R', 'S', 'L', 'M']

            for series in series_list:
                base_col = f"{series}_BASE_BOAT"
                engine_col = f"{series}_ENGINE"
                options_col = f"{series}_OPTIONS"
                vol_col = f"{series}_VOL_DISC"
                freight_col = f"{series}_FREIGHT"
                prep_col = f"{series}_PREP"

                # Check if this series has data (not all null/zero)
                if result[base_col] or result[engine_col] or result[options_col]:
                    print(f"{series} Series:")
                    print(f"  Base Boat:        {result[base_col]}%")
                    print(f"  Engine:           {result[engine_col]}%")
                    print(f"  Options:          {result[options_col]}%")
                    print(f"  Volume Discount:  {result[vol_col]}%")
                    print(f"  Freight:          ${result[freight_col]:,.2f}")
                    print(f"  Prep:             ${result[prep_col]:,.2f}")
                    print()

        else:
            print("Dealer 00333834 not found in DealerMargins table")

            # Try searching by name
            print("\nSearching for similar dealer names...")
            cursor.execute("""
                SELECT DealerID, Dealership
                FROM DealerMargins
                WHERE Dealership LIKE '%NICHOLS%'
                ORDER BY Dealership
            """)

            similar = cursor.fetchall()
            if similar:
                print(f"Found {len(similar)} dealers with 'NICHOLS' in name:")
                for row in similar:
                    print(f"  {row['DealerID']}: {row['Dealership']}")

        cursor.close()

    except mysql.connector.Error as e:
        print(f"Database error: {e}")
    finally:
        if connection and connection.is_connected():
            connection.close()

if __name__ == "__main__":
    check_dealer()

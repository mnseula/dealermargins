#!/usr/bin/env python3
"""Check dealer 333834 (without leading zeros) - NICHOLS MARINE SE OK LLC"""
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

        # Look up dealer 333834 (no leading zeros)
        query = """
            SELECT DealerID, Dealership,
                   Q_BASE_BOAT, Q_ENGINE, Q_OPTIONS, Q_FREIGHT, Q_PREP, Q_VOL_DISC,
                   QX_BASE_BOAT, QX_ENGINE, QX_OPTIONS, QX_FREIGHT, QX_PREP, QX_VOL_DISC,
                   R_BASE_BOAT, R_ENGINE, R_OPTIONS, R_FREIGHT, R_PREP, R_VOL_DISC,
                   S_BASE_BOAT, S_ENGINE, S_OPTIONS, S_FREIGHT, S_PREP, S_VOL_DISC,
                   L_BASE_BOAT, L_ENGINE, L_OPTIONS, L_FREIGHT, L_PREP, L_VOL_DISC,
                   M_BASE_BOAT, M_ENGINE, M_OPTIONS, M_FREIGHT, M_PREP, M_VOL_DISC
            FROM DealerMargins
            WHERE DealerID = '333834'
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

                # Check if this series has data
                base = result[base_col] if result[base_col] else 0
                engine = result[engine_col] if result[engine_col] else 0
                options = result[options_col] if result[options_col] else 0
                vol = result[vol_col] if result[vol_col] else 0
                freight = result[freight_col] if result[freight_col] else 0
                prep = result[prep_col] if result[prep_col] else 0

                # Show all series, even if zero
                print(f"{series} Series:")
                print(f"  Base Boat:        {base}%")
                print(f"  Engine:           {engine}%")
                print(f"  Options:          {options}%")
                print(f"  Volume Discount:  {vol}%")
                print(f"  Freight:          ${freight:,.2f}")
                print(f"  Prep:             ${prep:,.2f}")
                print()

            # Check if this matches the user's data (20/20/20/10 with Freight=1500, Prep=1000)
            print(f"{'='*80}")
            print("COMPARISON TO USER'S DATA:")
            print(f"{'='*80}")
            print("User's Data: Base=20%, Engine=20%, Options=20%, Vol=10%, Freight=$1,500, Prep=$1,000")
            print()

            # Check each series
            for series in series_list:
                base = result[f"{series}_BASE_BOAT"] if result[f"{series}_BASE_BOAT"] else 0
                engine = result[f"{series}_ENGINE"] if result[f"{series}_ENGINE"] else 0
                options = result[f"{series}_OPTIONS"] if result[f"{series}_OPTIONS"] else 0
                vol = result[f"{series}_VOL_DISC"] if result[f"{series}_VOL_DISC"] else 0
                freight = result[f"{series}_FREIGHT"] if result[f"{series}_FREIGHT"] else 0
                prep = result[f"{series}_PREP"] if result[f"{series}_PREP"] else 0

                if base == 20 and engine == 20 and options == 20 and vol == 10:
                    match_freight_prep = "✓" if (freight == 1500 and prep == 1000) else "✗"
                    print(f"{series} Series: ✓ MARGINS MATCH (Base/Engine/Options/Vol) | Freight/Prep: {match_freight_prep}")
                else:
                    print(f"{series} Series: ✗ Different margins - Base={base}%, Engine={engine}%, Options={options}%, Vol={vol}%")

        else:
            print("Dealer 333834 not found")

        cursor.close()

    except mysql.connector.Error as e:
        print(f"Database error: {e}")
    finally:
        if connection and connection.is_connected():
            connection.close()

if __name__ == "__main__":
    check_dealer()

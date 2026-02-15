#!/usr/bin/env python3
"""Check ALL NICHOLS dealers and their complete margin data"""
import mysql.connector

try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts'
}

def check_all_nichols():
    """Check all NICHOLS dealers"""
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        # Find all NICHOLS dealers
        cursor.execute("""
            SELECT DealerID, Dealership,
                   Q_BASE_BOAT, Q_ENGINE, Q_OPTIONS, Q_FREIGHT, Q_PREP, Q_VOL_DISC,
                   QX_BASE_BOAT, QX_ENGINE, QX_OPTIONS, QX_FREIGHT, QX_PREP, QX_VOL_DISC,
                   R_BASE_BOAT, R_ENGINE, R_OPTIONS, R_FREIGHT, R_PREP, R_VOL_DISC,
                   S_BASE_BOAT, S_ENGINE, S_OPTIONS, S_FREIGHT, S_PREP, S_VOL_DISC,
                   L_BASE_BOAT, L_ENGINE, L_OPTIONS, L_FREIGHT, L_PREP, L_VOL_DISC,
                   M_BASE_BOAT, M_ENGINE, M_OPTIONS, M_FREIGHT, M_PREP, M_VOL_DISC
            FROM DealerMargins
            WHERE Dealership LIKE '%NICHOLS%'
            ORDER BY DealerID
        """)

        results = cursor.fetchall()

        if results:
            print(f"\n{'='*100}")
            print(f"FOUND {len(results)} NICHOLS DEALERS")
            print(f"{'='*100}\n")

            for idx, dealer in enumerate(results, 1):
                print(f"\n{'='*100}")
                print(f"#{idx} - {dealer['Dealership']} (ID: {dealer['DealerID']})")
                print(f"{'='*100}\n")

                series_list = ['Q', 'QX', 'R', 'S', 'L', 'M']

                for series in series_list:
                    base_col = f"{series}_BASE_BOAT"
                    engine_col = f"{series}_ENGINE"
                    options_col = f"{series}_OPTIONS"
                    vol_col = f"{series}_VOL_DISC"
                    freight_col = f"{series}_FREIGHT"
                    prep_col = f"{series}_PREP"

                    # Check if this series has any data
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

            # Create summary table
            print(f"\n{'='*100}")
            print("SUMMARY TABLE - ALL NICHOLS DEALERS")
            print(f"{'='*100}\n")

            summary_data = []
            for dealer in results:
                # Use Q series as representative (they're typically all the same)
                summary_data.append([
                    dealer['DealerID'],
                    dealer['Dealership'],
                    f"{dealer['Q_BASE_BOAT']}%" if dealer['Q_BASE_BOAT'] else "0%",
                    f"{dealer['Q_ENGINE']}%" if dealer['Q_ENGINE'] else "0%",
                    f"{dealer['Q_OPTIONS']}%" if dealer['Q_OPTIONS'] else "0%",
                    f"{dealer['Q_VOL_DISC']}%" if dealer['Q_VOL_DISC'] else "0%",
                    f"${dealer['Q_FREIGHT']:,.0f}" if dealer['Q_FREIGHT'] else "$0",
                    f"${dealer['Q_PREP']:,.0f}" if dealer['Q_PREP'] else "$0"
                ])

            headers = ['Dealer ID', 'Dealership', 'Base', 'Engine', 'Options', 'Vol Disc', 'Freight', 'Prep']

            if HAS_TABULATE:
                print(tabulate(summary_data, headers=headers, tablefmt='grid'))
            else:
                # Simple text table fallback
                print(f"{'Dealer ID':<12} {'Dealership':<40} {'Base':<8} {'Engine':<8} {'Options':<8} {'Vol':<8} {'Freight':<10} {'Prep':<10}")
                print("-" * 110)
                for row in summary_data:
                    print(f"{row[0]:<12} {row[1]:<40} {row[2]:<8} {row[3]:<8} {row[4]:<8} {row[5]:<8} {row[6]:<10} {row[7]:<10}")

        else:
            print("No NICHOLS dealers found")

        cursor.close()

    except mysql.connector.Error as e:
        print(f"Database error: {e}")
    finally:
        if connection and connection.is_connected():
            connection.close()

if __name__ == "__main__":
    check_all_nichols()

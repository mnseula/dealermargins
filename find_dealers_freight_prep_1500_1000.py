#!/usr/bin/env python3
"""Find dealers with Freight=1500 AND Prep=1000 together"""
import mysql.connector

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts'
}

def find_dealers():
    """Find dealers with Freight=1500 AND Prep=1000"""
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        print("\n" + "="*80)
        print("DEALERS WITH FREIGHT=$1,500 AND PREP=$1,000")
        print("="*80)

        # Search across all series
        series_list = ['Q', 'QX', 'QXS', 'R', 'RX', 'RT', 'G', 'S', 'SX', 'L', 'LX', 'LT', 'S_23', 'SV_23', 'M']

        all_matches = []

        for series in series_list:
            freight_col = f"{series}_FREIGHT"
            prep_col = f"{series}_PREP"
            base_col = f"{series}_BASE_BOAT"
            engine_col = f"{series}_ENGINE"
            options_col = f"{series}_OPTIONS"
            vol_col = f"{series}_VOL_DISC"

            query = f"""
                SELECT DealerID, Dealership,
                       {base_col} as base_boat, {engine_col} as engine,
                       {options_col} as options, {vol_col} as vol_disc,
                       {freight_col} as freight, {prep_col} as prep
                FROM DealerMargins
                WHERE {freight_col} = 1500 AND {prep_col} = 1000
            """

            cursor.execute(query)
            results = cursor.fetchall()

            if results:
                print(f"\n{series} Series - Found {len(results)} dealers:")
                for row in results:
                    print(f"  {row['DealerID']}: {row['Dealership']}")
                    print(f"    Margins: Base={row['base_boat']}%, Engine={row['engine']}%, Options={row['options']}%, Vol={row['vol_disc']}%")
                    print(f"    Freight=${row['freight']:,.0f}, Prep=${row['prep']:,.0f}")

                    # Check if this matches 20/20/20/10 pattern
                    if (row['base_boat'] == 20 and row['engine'] == 20 and
                        row['options'] == 20 and row['vol_disc'] == 10):
                        print(f"    ✅ EXACT MATCH - This matches your data!")
                        all_matches.append((series, row['DealerID'], row['Dealership']))

        # Summary
        print("\n" + "="*80)
        print("EXACT MATCHES (20/20/20/10 + Freight=1500 + Prep=1000)")
        print("="*80)
        if all_matches:
            print(f"\nFound {len(all_matches)} exact matches:\n")
            # Group by dealer
            from collections import defaultdict
            by_dealer = defaultdict(list)
            for series, dealer_id, dealer_name in all_matches:
                by_dealer[(dealer_id, dealer_name)].append(series)

            for (dealer_id, dealer_name), series_list in by_dealer.items():
                print(f"  Dealer: {dealer_id} - {dealer_name}")
                print(f"    Series: {', '.join(series_list)}")
        else:
            print("\nNo exact matches found with all criteria")

        cursor.close()
        connection.close()

    except mysql.connector.Error as e:
        print(f"❌ Database error: {e}")
        if connection and connection.is_connected():
            connection.close()

if __name__ == "__main__":
    find_dealers()

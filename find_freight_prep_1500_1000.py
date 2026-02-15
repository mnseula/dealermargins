#!/usr/bin/env python3
"""Search for dealers with Freight=1500 and Prep=1000 across all series"""
import mysql.connector

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts'
}

def find_dealers():
    """Find dealers with Freight=1500 and Prep=1000"""
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        # Search across all series columns
        series_list = ['Q', 'QX', 'QXS', 'R', 'RX', 'RT', 'G', 'S', 'SX', 'L', 'LX', 'LT', 'M']

        for series in series_list:
            freight_col = f"{series}_FREIGHT"
            prep_col = f"{series}_PREP"
            base_col = f"{series}_BASE_BOAT"
            engine_col = f"{series}_ENGINE"
            options_col = f"{series}_OPTIONS"
            vol_col = f"{series}_VOL_DISC"

            query = f"""
                SELECT DealerID, Dealership,
                       {base_col}, {engine_col}, {options_col}, {vol_col},
                       {freight_col}, {prep_col}
                FROM DealerMargins
                WHERE {freight_col} = 1500 AND {prep_col} = 1000
                LIMIT 5
            """

            cursor.execute(query)
            results = cursor.fetchall()

            if results:
                print(f"\n{series} Series - Found {len(results)} dealers with Freight=1500 and Prep=1000:")
                for row in results:
                    print(f"  {row['DealerID']}: {row['Dealership']}")
                    print(f"    Margins: Base={row[base_col]}%, Engine={row[engine_col]}%, Options={row[options_col]}%, Vol={row[vol_col]}%")
                    print(f"    Freight={row[freight_col]}, Prep={row[prep_col]}")

        cursor.close()

    except mysql.connector.Error as e:
        print(f"Database error: {e}")
    finally:
        if connection and connection.is_connected():
            connection.close()

if __name__ == "__main__":
    find_dealers()

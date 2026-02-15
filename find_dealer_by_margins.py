#!/usr/bin/env python3
"""Find dealer with specific margin values"""
import mysql.connector

# Database configuration
DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts'
}

def find_dealer():
    """Find dealer with specific margins"""
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        # Search for dealers with these specific margin values
        # Looking for: Base=20, Engine=20, Options=20, Volume=10
        # Note: The wide format doesn't store freight/prep values

        # Check a few series columns
        query = """
            SELECT DealerID, Dealership,
                   Q_BASE_BOAT, Q_ENGINE, Q_OPTIONS, Q_VOL_DISC,
                   QX_BASE_BOAT, QX_ENGINE, QX_OPTIONS, QX_VOL_DISC,
                   R_BASE_BOAT, R_ENGINE, R_OPTIONS, R_VOL_DISC
            FROM DealerMargins
            WHERE (Q_BASE_BOAT = 20 AND Q_ENGINE = 20 AND Q_OPTIONS = 20 AND Q_VOL_DISC = 10)
               OR (QX_BASE_BOAT = 20 AND QX_ENGINE = 20 AND QX_OPTIONS = 20 AND QX_VOL_DISC = 10)
               OR (R_BASE_BOAT = 20 AND R_ENGINE = 20 AND R_OPTIONS = 20 AND R_VOL_DISC = 10)
            LIMIT 10
        """

        cursor.execute(query)
        results = cursor.fetchall()

        if results:
            print(f"\nFound {len(results)} dealers with margins: Base=20%, Engine=20%, Options=20%, Volume=10%\n")
            for i, row in enumerate(results, 1):
                print(f"{i}. DealerID: {row['DealerID']}, Dealership: {row['Dealership']}")
                if row['Q_BASE_BOAT'] == 20:
                    print(f"   Q Series: Base={row['Q_BASE_BOAT']}%, Engine={row['Q_ENGINE']}%, Options={row['Q_OPTIONS']}%, Vol={row['Q_VOL_DISC']}%")
                if row['QX_BASE_BOAT'] == 20:
                    print(f"   QX Series: Base={row['QX_BASE_BOAT']}%, Engine={row['QX_ENGINE']}%, Options={row['QX_OPTIONS']}%, Vol={row['QX_VOL_DISC']}%")
                if row['R_BASE_BOAT'] == 20:
                    print(f"   R Series: Base={row['R_BASE_BOAT']}%, Engine={row['R_ENGINE']}%, Options={row['R_OPTIONS']}%, Vol={row['R_VOL_DISC']}%")
                print()
        else:
            print("No dealers found with those exact margin values")

            # Try finding any dealers with 20% margins
            cursor.execute("""
                SELECT DealerID, Dealership,
                       Q_BASE_BOAT, Q_ENGINE, Q_OPTIONS, Q_VOL_DISC
                FROM DealerMargins
                WHERE Q_BASE_BOAT = 20
                LIMIT 5
            """)
            alt_results = cursor.fetchall()

            if alt_results:
                print(f"\nFound {len(alt_results)} dealers with Q_BASE_BOAT = 20%:")
                for row in alt_results:
                    print(f"  {row['DealerID']}: {row['Dealership']} - Base={row['Q_BASE_BOAT']}%, Engine={row['Q_ENGINE']}%, Options={row['Q_OPTIONS']}%, Vol={row['Q_VOL_DISC']}%")

        cursor.close()

    except mysql.connector.Error as e:
        print(f"Database error: {e}")
    finally:
        if connection and connection.is_connected():
            connection.close()

if __name__ == "__main__":
    find_dealer()

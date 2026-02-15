#!/usr/bin/env python3
"""Check freight and prep values for dealers"""
import mysql.connector

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts'
}

def check_freight_prep():
    """Check freight and prep columns"""
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        # Check dealers with margins 20/20/20/10 AND check their freight/prep values
        query = """
            SELECT DealerID, Dealership,
                   Q_BASE_BOAT, Q_ENGINE, Q_OPTIONS, Q_VOL_DISC,
                   Q_FREIGHT, Q_PREP,
                   QX_FREIGHT, QX_PREP,
                   R_FREIGHT, R_PREP
            FROM DealerMargins
            WHERE Q_BASE_BOAT = 20 AND Q_ENGINE = 20
              AND Q_OPTIONS = 20 AND Q_VOL_DISC = 10
            LIMIT 5
        """

        cursor.execute(query)
        results = cursor.fetchall()

        if results:
            print(f"\nDealer margins with Freight and Prep values:\n")
            for row in results:
                print(f"DealerID: {row['DealerID']}, Dealership: {row['Dealership']}")
                print(f"  Q Series: Base={row['Q_BASE_BOAT']}%, Engine={row['Q_ENGINE']}%, Options={row['Q_OPTIONS']}%, Vol={row['Q_VOL_DISC']}%")
                print(f"  Q Freight: {row['Q_FREIGHT']}, Q Prep: {row['Q_PREP']}")
                print(f"  QX Freight: {row['QX_FREIGHT']}, QX Prep: {row['QX_PREP']}")
                print(f"  R Freight: {row['R_FREIGHT']}, R Prep: {row['R_PREP']}")
                print()

        # Also check if any dealer has Freight=1500 and Prep=1000
        print("\nSearching for dealers with Q_FREIGHT=1500 and Q_PREP=1000:")
        cursor.execute("""
            SELECT DealerID, Dealership,
                   Q_FREIGHT, Q_PREP, Q_BASE_BOAT, Q_ENGINE, Q_OPTIONS, Q_VOL_DISC
            FROM DealerMargins
            WHERE Q_FREIGHT = 1500 AND Q_PREP = 1000
            LIMIT 10
        """)

        freight_prep_results = cursor.fetchall()
        if freight_prep_results:
            print(f"Found {len(freight_prep_results)} dealers:")
            for row in freight_prep_results:
                print(f"  {row['DealerID']}: {row['Dealership']}")
                print(f"    Margins: Base={row['Q_BASE_BOAT']}%, Engine={row['Q_ENGINE']}%, Options={row['Q_OPTIONS']}%, Vol={row['Q_VOL_DISC']}%")
                print(f"    Freight={row['Q_FREIGHT']}, Prep={row['Q_PREP']}")
        else:
            print("  No dealers found with Q_FREIGHT=1500 and Q_PREP=1000")

        cursor.close()

    except mysql.connector.Error as e:
        print(f"Database error: {e}")
    finally:
        if connection and connection.is_connected():
            connection.close()

if __name__ == "__main__":
    check_freight_prep()

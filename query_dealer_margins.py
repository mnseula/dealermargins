#!/usr/bin/env python3
"""Query the DealerMargins table"""
import mysql.connector

# Database configuration
DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts'
}

def query_dealer_margins():
    """Query and display DealerMargins table"""
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT * FROM DealerMargins")
        results = cursor.fetchall()

        if results:
            print(f"\nFound {len(results)} rows in DealerMargins table")
            print(f"Columns: {', '.join(results[0].keys())}\n")

            # Show first 10 dealers with summary
            print("First 10 dealers:\n")
            for i, row in enumerate(results[:10]):
                print(f"{i+1}. DealerID: {row['DealerID']}, Dealership: {row['Dealership']}")
                print(f"   QX margins: Base={row['QX_BASE_BOAT']}%, Engine={row['QX_ENGINE']}%, Options={row['QX_OPTIONS']}%")
                print(f"   Q margins: Base={row['Q_BASE_BOAT']}%, Engine={row['Q_ENGINE']}%, Options={row['Q_OPTIONS']}%")
                print()
        else:
            print("No data found in DealerMargins table")

        cursor.close()

    except mysql.connector.Error as e:
        print(f"Database error: {e}")
    finally:
        if connection and connection.is_connected():
            connection.close()

if __name__ == "__main__":
    query_dealer_margins()

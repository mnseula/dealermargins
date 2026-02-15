#!/usr/bin/env python3
"""Check column names in BoatOptions tables"""
import mysql.connector

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts'
}

def check_columns():
    """Check BoatOptions table structure"""
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        # Check BoatOptions25 structure
        cursor.execute("DESCRIBE BoatOptions25")
        columns = cursor.fetchall()

        print("\nBoatOptions25 columns:")
        print("="*60)
        for col in columns:
            print(f"  {col['Field']:<30} {col['Type']}")

        cursor.close()
        connection.close()

    except mysql.connector.Error as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    check_columns()

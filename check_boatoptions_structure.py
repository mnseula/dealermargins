#!/usr/bin/env python3
"""
Check BoatOptions26 structure - is it a table or view?
"""
import mysql.connector

# Database configuration
db_config = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts'
}

def check_boatoptions26():
    """Check if BoatOptions26 is table or view and show its structure."""
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    # Check if it's a table or view
    print("=" * 80)
    print("CHECKING BoatOptions26 TYPE")
    print("=" * 80)
    cursor.execute("SHOW FULL TABLES LIKE 'BoatOptions26'")
    result = cursor.fetchone()
    if result:
        table_type = result['Table_type']
        print(f"BoatOptions26 is a: {table_type}")

    print("\n" + "=" * 80)
    print("SHOW CREATE TABLE/VIEW")
    print("=" * 80)
    cursor.execute("SHOW CREATE TABLE BoatOptions26")
    result = cursor.fetchone()
    if result:
        create_statement = result.get('Create Table') or result.get('Create View')
        print(create_statement)

    print("\n" + "=" * 80)
    print("COLUMN STRUCTURE")
    print("=" * 80)
    cursor.execute("DESCRIBE BoatOptions26")
    columns = cursor.fetchall()
    for col in columns:
        print(f"{col['Field']:30s} {col['Type']:20s} {col['Null']:5s} {col['Key']:5s} {col['Default'] or 'NULL'}")

    # Check if MSRP column exists
    print("\n" + "=" * 80)
    print("MSRP COLUMN CHECK")
    print("=" * 80)
    cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = 'warrantyparts' AND TABLE_NAME = 'BoatOptions26' AND COLUMN_NAME = 'MSRP'")
    msrp_col = cursor.fetchone()
    if msrp_col:
        print("✅ MSRP column EXISTS in BoatOptions26")
    else:
        print("❌ MSRP column DOES NOT EXIST in BoatOptions26")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    check_boatoptions26()

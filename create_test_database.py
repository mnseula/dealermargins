#!/usr/bin/env python3
"""
Create test database and tables for BoatOptions import testing
"""
import mysql.connector
from mysql.connector import Error

# MySQL Configuration (root level to create database)
MYSQL_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD'
}

def create_database():
    """Create the test database"""
    try:
        print("Connecting to MySQL...")
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()

        print("Creating database: warrantyparts_boatoptions_test")
        cursor.execute("CREATE DATABASE IF NOT EXISTS warrantyparts_boatoptions_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print("✅ Database created")

        cursor.close()
        conn.close()
        return True

    except Error as e:
        print(f"❌ Error: {e}")
        return False

def create_tables():
    """Create the BoatOptions tables"""
    try:
        # Connect to the test database
        config = MYSQL_CONFIG.copy()
        config['database'] = 'warrantyparts_boatoptions_test'

        print("\nConnecting to warrantyparts_boatoptions_test...")
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()

        table_schema = """
        CREATE TABLE IF NOT EXISTS {table_name} (
            ERP_OrderNo VARCHAR(30),
            BoatSerialNo VARCHAR(15),
            BoatModelNo VARCHAR(14),
            LineNo INT,
            ItemNo VARCHAR(30),
            ItemDesc1 VARCHAR(50),
            ExtSalesAmount DECIMAL(10,2),
            QuantitySold DECIMAL(18,8),
            Series VARCHAR(5),
            WebOrderNo VARCHAR(30),
            Orig_Ord_Type VARCHAR(1),
            ApplyToNo VARCHAR(30),
            InvoiceNo VARCHAR(30),
            InvoiceDate INT,
            ItemMasterProdCat VARCHAR(3),
            ItemMasterProdCatDesc VARCHAR(100),
            ItemMasterMCT VARCHAR(10),
            MCTDesc VARCHAR(50),
            LineSeqNo INT,
            ConfigID VARCHAR(30),
            ValueText VARCHAR(100),
            OptionSerialNo VARCHAR(12),
            C_Series VARCHAR(5),
            PRIMARY KEY (ERP_OrderNo, LineSeqNo),
            INDEX idx_serial (BoatSerialNo),
            INDEX idx_model (BoatModelNo),
            INDEX idx_invoice (InvoiceNo),
            INDEX idx_mct (ItemMasterMCT)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """

        tables = ['BoatOptions24', 'BoatOptions25_test', 'BoatOptions26_test']

        for table in tables:
            print(f"Creating table: {table}")
            cursor.execute(table_schema.format(table_name=table))
            print(f"✅ {table} created")

        cursor.close()
        conn.close()

        print("\n✅ All tables created successfully")
        return True

    except Error as e:
        print(f"❌ Error: {e}")
        return False

def verify_setup():
    """Verify database and tables exist"""
    try:
        config = MYSQL_CONFIG.copy()
        config['database'] = 'warrantyparts_boatoptions_test'

        print("\nVerifying setup...")
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()

        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        print(f"\nTables in warrantyparts_boatoptions_test:")
        for table in tables:
            print(f"  - {table[0]}")

        cursor.close()
        conn.close()

        return True

    except Error as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("="*70)
    print("SETUP TEST DATABASE FOR BOATOPTIONS IMPORT")
    print("="*70)

    if not create_database():
        print("\n❌ Failed to create database")
        return False

    if not create_tables():
        print("\n❌ Failed to create tables")
        return False

    if not verify_setup():
        print("\n❌ Failed to verify setup")
        return False

    print("\n" + "="*70)
    print("✅ TEST DATABASE SETUP COMPLETE")
    print("="*70)
    print("\nNext step: Run import_boatoptions_test.py")
    return True

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)

#!/usr/bin/env python3
"""
Verify TEST Database Structure

Checks that warrantyparts_boatoptions_test database exists
and has all the required BoatOptions tables with correct schema.
"""
import mysql.connector
from mysql.connector import Error as MySQLError

# MySQL Configuration
MYSQL_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD'
}

# Expected tables
EXPECTED_TABLES = [
    'BoatOptionsBefore_05',
    'BoatOptions99_04',
    'BoatOptions05_07',
    'BoatOptions08_10',
    'BoatOptions11_14',
    'BoatOptions15',
    'BoatOptions16',
    'BoatOptions17',
    'BoatOptions18',
    'BoatOptions19',
    'BoatOptions20',
    'BoatOptions21',
    'BoatOptions22',
    'BoatOptions23',
    'BoatOptions24',
    'BoatOptions25',
    'BoatOptions26'
]

# Expected columns
EXPECTED_COLUMNS = [
    'ERP_OrderNo',
    'BoatSerialNo',
    'BoatModelNo',
    'LineNo',
    'ItemNo',
    'ItemDesc1',
    'ExtSalesAmount',
    'QuantitySold',
    'Series',
    'WebOrderNo',
    'Orig_Ord_Type',
    'ApplyToNo',
    'InvoiceNo',
    'InvoiceDate',
    'ItemMasterProdCat',
    'ItemMasterProdCatDesc',
    'ItemMasterMCT',
    'MCTDesc',
    'LineSeqNo',
    'ConfigID',
    'ValueText',
    'OptionSerialNo',
    'C_Series'
]

def main():
    print("="*80)
    print("VERIFYING TEST DATABASE STRUCTURE")
    print("="*80)
    print()

    try:
        # Connect to MySQL
        print("Connecting to MySQL...")
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        print("✅ Connected to MySQL\n")

        # Check if database exists
        print("="*80)
        print("CHECKING DATABASE:")
        print("="*80)
        cursor.execute("SHOW DATABASES LIKE 'warrantyparts_boatoptions_test'")
        db_exists = cursor.fetchone()

        if db_exists:
            print("✅ Database 'warrantyparts_boatoptions_test' EXISTS\n")
        else:
            print("❌ Database 'warrantyparts_boatoptions_test' DOES NOT EXIST!")
            print("\nYou need to create it first:")
            print("  CREATE DATABASE warrantyparts_boatoptions_test;")
            return

        # Use the database
        cursor.execute("USE warrantyparts_boatoptions_test")

        # Check tables
        print("="*80)
        print("CHECKING TABLES:")
        print("="*80)
        cursor.execute("SHOW TABLES")
        existing_tables = [table[0] for table in cursor.fetchall()]

        print(f"\nFound {len(existing_tables)} tables in database:")
        for table in sorted(existing_tables):
            print(f"  ✓ {table}")

        print(f"\nExpected {len(EXPECTED_TABLES)} tables:")
        missing_tables = []
        for table in EXPECTED_TABLES:
            if table in existing_tables:
                print(f"  ✅ {table}")
            else:
                print(f"  ❌ {table} - MISSING")
                missing_tables.append(table)

        if missing_tables:
            print(f"\n⚠️  WARNING: {len(missing_tables)} tables are missing!")
            print("Missing tables:", ', '.join(missing_tables))
        else:
            print("\n✅ All expected tables exist!")

        # Check schema for one table (BoatOptions25)
        if 'BoatOptions25' in existing_tables:
            print("\n" + "="*80)
            print("CHECKING SCHEMA (BoatOptions25):")
            print("="*80)
            cursor.execute("DESCRIBE BoatOptions25")
            columns = cursor.fetchall()

            print(f"\n{'Column Name':<30} {'Type':<30} {'Null':<10} {'Key':<10}")
            print("-"*80)
            for col in columns:
                print(f"{col[0]:<30} {col[1]:<30} {col[2]:<10} {col[3]:<10}")

            existing_columns = [col[0] for col in columns]

            print(f"\nExpected {len(EXPECTED_COLUMNS)} columns:")
            missing_columns = []
            for col in EXPECTED_COLUMNS:
                if col in existing_columns:
                    print(f"  ✅ {col}")
                else:
                    print(f"  ❌ {col} - MISSING")
                    missing_columns.append(col)

            if missing_columns:
                print(f"\n⚠️  WARNING: {len(missing_columns)} columns are missing!")
            else:
                print("\n✅ All expected columns exist!")

            # Check row counts
            print("\n" + "="*80)
            print("ROW COUNTS:")
            print("="*80)
            total_rows = 0
            for table in sorted(existing_tables):
                if table.startswith('BoatOptions'):
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    total_rows += count
                    if count > 0:
                        print(f"  {table:<30} {count:>10,} rows")

            print(f"\n  {'TOTAL':<30} {total_rows:>10,} rows")

        cursor.close()
        conn.close()

        print("\n" + "="*80)
        print("VERIFICATION COMPLETE")
        print("="*80)

        if not missing_tables:
            print("\n✅ Database is ready for import!")
        else:
            print(f"\n⚠️  Missing {len(missing_tables)} tables - create them before importing")

    except MySQLError as e:
        print(f"❌ MySQL error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

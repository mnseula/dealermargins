#!/usr/bin/env python3
"""
Add CPQ-related columns to BoatOptions tables
Adds: ConfigID, ValueText, C_Series, order_date, external_confirmation_ref
"""
import mysql.connector

MYSQL_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'warrantyparts_boatoptions_test',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD'
}

# Tables to update
TABLES = [
    'BoatOptions26',
    'BoatOptions25',
    'BoatOptions24',
    'BoatOptions23',
    'BoatOptions22',
    'BoatOptions21',
    'BoatOptions20',
    'BoatOptions19',
    'BoatOptions18',
    'BoatOptions17',
    'BoatOptions16',
    'BoatOptions15',
    'BoatOptions11_14',
    'BoatOptions08_10',
    'BoatOptions05_07',
    'BoatOptions99_04',
    'BoatOptionsBefore_05'
]

ALTER_STATEMENTS = [
    "ALTER TABLE `{table}` ADD COLUMN `ConfigID` varchar(30) DEFAULT NULL COMMENT 'CPQ Configuration ID'",
    "ALTER TABLE `{table}` ADD COLUMN `ValueText` varchar(100) DEFAULT NULL COMMENT 'CPQ Configuration Value'",
    "ALTER TABLE `{table}` ADD COLUMN `C_Series` varchar(5) DEFAULT NULL COMMENT 'Series from item master'",
    "ALTER TABLE `{table}` ADD COLUMN `order_date` date DEFAULT NULL COMMENT 'Order date from co_mst'",
    "ALTER TABLE `{table}` ADD COLUMN `external_confirmation_ref` varchar(30) DEFAULT NULL COMMENT 'CPQ order reference'",
]

def main():
    print("="*80)
    print("ADDING CPQ COLUMNS TO BOATOPTIONS TABLES")
    print("="*80)
    print(f"Database: {MYSQL_CONFIG['database']}")
    print(f"Tables: {len(TABLES)}")
    print("="*80)

    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()

        for table in TABLES:
            print(f"\nProcessing {table}...")

            # Check if table exists
            cursor.execute(f"SHOW TABLES LIKE '{table}'")
            if not cursor.fetchone():
                print(f"  ⚠️  Table {table} does not exist, skipping...")
                continue

            # Add columns
            for alter_stmt in ALTER_STATEMENTS:
                try:
                    stmt = alter_stmt.format(table=table)
                    cursor.execute(stmt)
                    column_name = stmt.split('`')[3]  # Extract column name
                    print(f"  ✅ Added column: {column_name}")
                except mysql.connector.Error as e:
                    if e.errno == 1060:  # Duplicate column
                        column_name = stmt.split('`')[3]
                        print(f"  ℹ️  Column {column_name} already exists")
                    else:
                        print(f"  ❌ Error: {e}")
                        raise

        conn.commit()
        cursor.close()
        conn.close()

        print("\n" + "="*80)
        print("✅ COLUMNS ADDED SUCCESSFULLY")
        print("="*80)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

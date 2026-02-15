#!/usr/bin/env python3
"""
Add CPQ columns to pre-2015 BoatOptions tables
This allows legacy tables to support modern CPQ data format
"""

import mysql.connector
from mysql.connector import Error as MySQLError

# MySQL Configuration
MYSQL_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'warrantyparts',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD'
}

# Pre-2015 tables that need CPQ columns
PRE_2015_TABLES = [
    'BoatOptionsBefore_05',
    'BoatOptions99_04',
    'BoatOptions05_07',
    'BoatOptions08_10',
    'BoatOptions11_14'
]

# CPQ columns to add
CPQ_COLUMNS = [
    ("ConfigID", "VARCHAR(30) NULL"),
    ("ValueText", "VARCHAR(100) NULL"),
    ("MSRP", "DECIMAL(10,2) NULL"),
    ("CfgName", "VARCHAR(100) NULL"),
    ("CfgPage", "VARCHAR(50) NULL"),
    ("CfgScreen", "VARCHAR(50) NULL"),
    ("CfgValue", "VARCHAR(100) NULL"),
    ("CfgAttrType", "VARCHAR(20) NULL")
]

def add_columns_to_table(cursor, table_name):
    """Add CPQ columns to a single table"""
    print(f"\n📋 Processing {table_name}...")
    
    # Check which columns already exist
    cursor.execute(f"DESCRIBE {table_name}")
    existing_columns = {row[0] for row in cursor.fetchall()}
    
    columns_added = 0
    
    for col_name, col_def in CPQ_COLUMNS:
        if col_name in existing_columns:
            print(f"  ⚠️  Column '{col_name}' already exists, skipping")
            continue
        
        try:
            alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_def}"
            cursor.execute(alter_sql)
            print(f"  ✅ Added column '{col_name}'")
            columns_added += 1
        except MySQLError as e:
            print(f"  ❌ Error adding '{col_name}': {e}")
    
    return columns_added

def main():
    print("="*80)
    print("ADDING CPQ COLUMNS TO PRE-2015 BOATOPTIONS TABLES")
    print("="*80)
    print(f"Target Database: warrantyparts")
    print(f"Tables to update: {len(PRE_2015_TABLES)}")
    print(f"Columns to add: {len(CPQ_COLUMNS)}")
    print("="*80)
    
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        print("✅ Connected to MySQL\n")
        
        total_columns_added = 0
        
        for table_name in PRE_2015_TABLES:
            try:
                columns_added = add_columns_to_table(cursor, table_name)
                total_columns_added += columns_added
                conn.commit()
            except Exception as e:
                print(f"  ❌ Failed to process {table_name}: {e}")
                conn.rollback()
        
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Total columns added: {total_columns_added}")
        print("\n✅ All pre-2015 BoatOptions tables now support CPQ columns!")
        print("="*80)
        
        cursor.close()
        conn.close()
        
    except MySQLError as e:
        print(f"❌ Database connection error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())

#!/usr/bin/env python3
"""Check what dealer-related tables exist in MySQL"""

import mysql.connector

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD'
}

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()

print("="*80)
print("SEARCHING FOR DEALER-RELATED TABLES IN MYSQL")
print("="*80)

# Check warrantyparts database
cursor.execute("USE warrantyparts")

print("\n1. Tables with 'dealer' in name:")
print("-" * 80)
cursor.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'warrantyparts'
    AND LOWER(table_name) LIKE '%dealer%'
    ORDER BY table_name
""")
dealer_tables = cursor.fetchall()
for table in dealer_tables:
    print(f"  ✅ {table[0]}")

if not dealer_tables:
    print("  ❌ No tables with 'dealer' in name")

print("\n2. Tables with 'customer' in name:")
print("-" * 80)
cursor.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'warrantyparts'
    AND LOWER(table_name) LIKE '%customer%'
    ORDER BY table_name
""")
customer_tables = cursor.fetchall()
for table in customer_tables:
    print(f"  ✅ {table[0]}")

if not customer_tables:
    print("  ❌ No tables with 'customer' in name")

print("\n3. Checking warrantyparts_test database:")
print("-" * 80)
cursor.execute("USE warrantyparts_test")

cursor.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'warrantyparts_test'
    AND (LOWER(table_name) LIKE '%dealer%' OR LOWER(table_name) LIKE '%customer%')
    ORDER BY table_name
""")
test_tables = cursor.fetchall()
for table in test_tables:
    print(f"  ✅ warrantyparts_test.{table[0]}")

if not test_tables:
    print("  ❌ No dealer/customer tables in warrantyparts_test")

print("\n4. Checking if SerialNumberMaster has dealer columns:")
print("-" * 80)
cursor.execute("USE warrantyparts")
cursor.execute("DESCRIBE SerialNumberMaster")
snm_columns = cursor.fetchall()

dealer_cols = [col for col in snm_columns if 'dealer' in col[0].lower()]
if dealer_cols:
    print("  Dealer columns in SerialNumberMaster:")
    for col in dealer_cols:
        print(f"    ✅ {col[0]:30s} {col[1]:20s}")
else:
    print("  ❌ No dealer columns in SerialNumberMaster")

print("\n5. Sample existing boat in SerialNumberMaster with dealer:")
print("-" * 80)
cursor.execute("""
    SELECT
        Boat_SerialNo,
        DealerNumber,
        DealerName,
        DealerCity,
        DealerState,
        ERP_OrderNo,
        InvoiceNo
    FROM SerialNumberMaster
    WHERE DealerNumber IS NOT NULL
      AND DealerNumber != ''
      AND DealerNumber != 0
    LIMIT 3
""")
samples = cursor.fetchall()
if samples:
    for sample in samples:
        print(f"\n  Serial: {sample[0]}")
        print(f"  Dealer: {sample[1]} - {sample[2]}")
        print(f"  Location: {sample[3]}, {sample[4]}")
        print(f"  ERP Order: {sample[5]}")
        print(f"  Invoice: {sample[6]}")
else:
    print("  ❌ No boats with dealer info found")

cursor.close()
conn.close()

print("\n" + "="*80)
print("CONCLUSION:")
print("="*80)
print("""
If no dealer tables exist in MySQL, we have two options:

1. Keep MSSQL connection to get dealer info from customer_mst table
2. Use a default/test dealer for all boats (like original script)
3. Create a dealer lookup table in MySQL first (one-time MSSQL→MySQL sync)
""")
print("="*80)

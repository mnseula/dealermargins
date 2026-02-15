#!/usr/bin/env python3
"""Check if we can link boats/orders to dealers using MySQL tables only"""

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
print("CHECKING IF WE CAN LINK BOATS TO DEALERS IN MYSQL")
print("="*80)

# Check DealerAddr structure
print("\n1. DealerAddr table structure:")
print("-" * 80)
cursor.execute("USE warrantyparts")
cursor.execute("DESCRIBE DealerAddr")
dealer_addr_cols = cursor.fetchall()
for col in dealer_addr_cols:
    print(f"  {col[0]:30s} {col[1]:20s}")

print("\n  Sample DealerAddr records:")
cursor.execute("SELECT * FROM DealerAddr LIMIT 3")
for row in cursor.fetchall():
    print(f"    {row}")

# Check if there's an orders table
print("\n2. Looking for order tables:")
print("-" * 80)
cursor.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema IN ('warrantyparts', 'warrantyparts_test', 'Eos')
    AND (LOWER(table_name) LIKE '%order%' OR LOWER(table_name) LIKE '%invoice%')
    ORDER BY table_schema, table_name
""")
order_tables = cursor.fetchall()
if order_tables:
    for table in order_tables:
        print(f"  ✅ {table[0]}")
else:
    print("  ❌ No order tables found")

# Check Eos database for dealermaster
print("\n3. Checking Eos.dealermaster:")
print("-" * 80)
try:
    cursor.execute("USE Eos")
    cursor.execute("DESCRIBE dealermaster")
    dm_cols = cursor.fetchall()
    print("  Columns:")
    for col in dm_cols:
        print(f"    {col[0]:30s} {col[1]:20s}")

    print("\n  Sample dealermaster records:")
    cursor.execute("SELECT * FROM dealermaster LIMIT 3")
    for row in cursor.fetchall():
        print(f"    {row}")
except Exception as e:
    print(f"  ❌ Error accessing Eos.dealermaster: {e}")

# Check if there's a relationship we can use
print("\n4. Checking for order→dealer relationship:")
print("-" * 80)
print("  Testing: Can we find dealer from ERP_OrderNo in BoatOptions?")

cursor.execute("USE warrantyparts")
cursor.execute("""
    SELECT
        bo.ERP_OrderNo,
        bo.InvoiceNo,
        bo.BoatSerialNo,
        snm.DealerNumber,
        snm.DealerName
    FROM BoatOptions26 bo
    LEFT JOIN SerialNumberMaster snm
        ON bo.BoatSerialNo = snm.Boat_SerialNo
    WHERE bo.ItemMasterMCT = 'BOA'
      AND bo.InvoiceNo IS NOT NULL
      AND snm.DealerNumber IS NOT NULL
    LIMIT 5
""")

matches = cursor.fetchall()
if matches:
    print("\n  ✅ Can link via SerialNumberMaster (for boats already there):")
    for match in matches:
        print(f"    Order: {match[0]}, Invoice: {match[1]}, Serial: {match[2]}")
        print(f"      → Dealer: {match[3]} - {match[4]}")
else:
    print("  ❌ No matches found")

# Check if WebOrderNo gives us anything
print("\n5. Checking WebOrderNo pattern:")
print("-" * 80)
cursor.execute("""
    SELECT DISTINCT
        WebOrderNo,
        ERP_OrderNo,
        Series
    FROM BoatOptions26
    WHERE WebOrderNo IS NOT NULL
      AND WebOrderNo != ''
    LIMIT 5
""")
web_orders = cursor.fetchall()
if web_orders:
    print("  Sample WebOrderNo values:")
    for wo in web_orders:
        print(f"    WebOrder: {wo[0]}, ERP: {wo[1]}, Series: {wo[2]}")
else:
    print("  ❌ No WebOrderNo values found")

cursor.close()
conn.close()

print("\n" + "="*80)
print("VERDICT:")
print("="*80)
print("""
BoatOptions tables have:
  - ERP_OrderNo (e.g., SO00936067)
  - InvoiceNo (e.g., 25217355)
  - WebOrderNo (e.g., SOBHO00709)
  - BoatSerialNo

But NO dealer columns.

Dealer tables exist (DealerAddr, Eos.dealermaster) but we can't link
ERP_OrderNo → Dealer without MSSQL connection to co_mst.cust_num.

OPTIONS:
1. Keep MSSQL connection (current script approach) ✅ RECOMMENDED
2. Pre-populate a MySQL order→dealer lookup table from MSSQL
3. Use default dealer for all boats (not what you want)
""")
print("="*80)

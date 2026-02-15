#!/usr/bin/env python3
"""Check what dealer-related columns exist in BoatOptions tables"""

import mysql.connector

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'warrantyparts',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD'
}

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()

print("="*80)
print("CHECKING BOATOPTIONS26 TABLE STRUCTURE")
print("="*80)

# Get column information
cursor.execute("DESCRIBE BoatOptions26")
columns = cursor.fetchall()

print("\nAll columns in BoatOptions26:")
print("-" * 80)
for col in columns:
    print(f"{col[0]:30s} {col[1]:20s} {col[2]:5s} {col[3]:5s}")

print("\n" + "="*80)
print("DEALER-RELATED COLUMNS:")
print("="*80)

dealer_keywords = ['dealer', 'customer', 'cust', 'sold']
dealer_cols = [col for col in columns if any(kw in col[0].lower() for kw in dealer_keywords)]

if dealer_cols:
    print("\nFound dealer-related columns:")
    for col in dealer_cols:
        print(f"  ✅ {col[0]:30s} {col[1]:20s}")
else:
    print("\n❌ No dealer-related columns found in BoatOptions26")

print("\n" + "="*80)
print("SAMPLE DATA (first boat with invoice):")
print("="*80)

cursor.execute("""
    SELECT
        BoatSerialNo,
        BoatModelNo,
        Series,
        InvoiceNo,
        ERP_OrderNo,
        WebOrderNo
    FROM BoatOptions26
    WHERE ItemMasterMCT = 'BOA'
      AND InvoiceNo IS NOT NULL
    LIMIT 1
""")

row = cursor.fetchone()
if row:
    print(f"\nBoat Serial: {row[0]}")
    print(f"Model: {row[1]}")
    print(f"Series: {row[2]}")
    print(f"Invoice: {row[3]}")
    print(f"ERP Order: {row[4]}")
    print(f"Web Order: {row[5]}")

cursor.close()
conn.close()
print("\n" + "="*80)

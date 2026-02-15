#!/usr/bin/env python3
"""Check boat ETWC6124F526 in database"""
import mysql.connector

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts'
}

serial = 'ETWC6124F526'

connection = mysql.connector.connect(**DB_CONFIG)
cursor = connection.cursor(dictionary=True)

print("="*80)
print(f"CHECKING BOAT: {serial}")
print("="*80)

# Check SerialNumberMaster
print("\n1. SerialNumberMaster:")
cursor.execute("""
    SELECT Boat_SerialNo, InvoiceNo, DealerNumber, DealerName
    FROM SerialNumberMaster
    WHERE Boat_SerialNo = %s
""", (serial,))
snm = cursor.fetchone()
if snm:
    print(f"   ✅ Found: Invoice={snm['InvoiceNo']}, Dealer={snm['DealerName']} (#{snm['DealerNumber']})")
else:
    print(f"   ❌ NOT FOUND in SerialNumberMaster")

# Check BoatOptions26
print("\n2. BoatOptions26:")
cursor.execute("SELECT COUNT(*) as count FROM BoatOptions26 WHERE BoatSerialNo = %s", (serial,))
count26 = cursor.fetchone()['count']
print(f"   Total records: {count26}")

if count26 > 0:
    cursor.execute("""
        SELECT ItemMasterMCT, COUNT(*) as count
        FROM BoatOptions26
        WHERE BoatSerialNo = %s
        GROUP BY ItemMasterMCT
    """, (serial,))
    for row in cursor.fetchall():
        print(f"      {row['ItemMasterMCT']}: {row['count']} records")

# Check BoatOptions25
print("\n3. BoatOptions25:")
cursor.execute("SELECT COUNT(*) as count FROM BoatOptions25 WHERE BoatSerialNo = %s", (serial,))
count25 = cursor.fetchone()['count']
print(f"   Total records: {count25}")

if count25 > 0:
    cursor.execute("""
        SELECT ItemMasterMCT, COUNT(*) as count
        FROM BoatOptions25
        WHERE BoatSerialNo = %s
        GROUP BY ItemMasterMCT
    """, (serial,))
    for row in cursor.fetchall():
        print(f"      {row['ItemMasterMCT']}: {row['count']} records")

# Check BoatOptions24
print("\n4. BoatOptions24:")
cursor.execute("SELECT COUNT(*) as count FROM BoatOptions24 WHERE BoatSerialNo = %s", (serial,))
count24 = cursor.fetchone()['count']
print(f"   Total records: {count24}")

print("\n" + "="*80)
print("CONCLUSION:")
print("="*80)

if count26 > 0:
    print(f"✅ Boat data in BoatOptions26 ({count26} records)")
    print(f"   → Need to configure BoatOptions26 in EOS")
elif count25 > 0:
    print(f"✅ Boat data in BoatOptions25 ({count25} records)")
    print(f"   → Fakies approach should work")
elif count24 > 0:
    print(f"✅ Boat data in BoatOptions24 ({count24} records)")
    print(f"   → Serial year detection might be wrong")
else:
    print(f"❌ Boat NOT FOUND in any BoatOptions table")
    print(f"   → Boat may not be invoiced yet")

cursor.close()
connection.close()

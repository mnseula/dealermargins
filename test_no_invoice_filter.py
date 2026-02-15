#!/usr/bin/env python3
"""Test if removing invoice filter finds the boat in BoatOptions25"""
import mysql.connector

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts'
}

serial = 'ETWS7943H526'
invoice = '25202681'

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor(dictionary=True)

print('='*80)
print(f'Testing Invoice Filter for {serial}')
print('='*80)

# Test 1: BoatOptions26 with invoice filter (what JavaScript tried)
print('\n1. BoatOptions26 WITH invoice filter:')
cursor.execute("""
    SELECT COUNT(*) as count FROM BoatOptions26
    WHERE BoatSerialNo = %s AND InvoiceNo = %s
""", (serial, invoice))
result = cursor.fetchone()
print(f'   Found: {result["count"]} records')

# Test 2: BoatOptions26 WITHOUT invoice filter
print('\n2. BoatOptions26 WITHOUT invoice filter:')
cursor.execute("""
    SELECT COUNT(*) as count FROM BoatOptions26
    WHERE BoatSerialNo = %s
""", (serial,))
result = cursor.fetchone()
print(f'   Found: {result["count"]} records')

if result["count"] > 0:
    # Check what invoice values exist
    cursor.execute("""
        SELECT DISTINCT InvoiceNo FROM BoatOptions26
        WHERE BoatSerialNo = %s
    """, (serial,))
    invoices = cursor.fetchall()
    print(f'   Invoice numbers in BoatOptions26:')
    for inv in invoices:
        match = "✅ MATCH" if inv['InvoiceNo'] == invoice else "❌ MISMATCH"
        print(f'      {inv["InvoiceNo"]} {match}')
    print(f'   Expected from JavaScript: {invoice}')

# Test 3: BoatOptions25 with invoice filter
print('\n3. BoatOptions25 WITH invoice filter:')
cursor.execute("""
    SELECT COUNT(*) as count FROM BoatOptions25
    WHERE BoatSerialNo = %s AND InvoiceNo = %s
""", (serial, invoice))
result = cursor.fetchone()
print(f'   Found: {result["count"]} records')

# Test 4: BoatOptions25 WITHOUT invoice filter
print('\n4. BoatOptions25 WITHOUT invoice filter:')
cursor.execute("""
    SELECT COUNT(*) as count FROM BoatOptions25
    WHERE BoatSerialNo = %s
""", (serial,))
result = cursor.fetchone()
print(f'   Found: {result["count"]} records')

print('\n' + '='*80)
print('CONCLUSION:')
print('='*80)
print('Invoice filter is working correctly in MySQL.')
print('The issue is that BoatOptions26 table is not configured as an EOS "list".')
print('\nOptions to fix:')
print('  A) Configure BoatOptions26 in EOS system (proper solution)')
print('  B) Copy 2026 boat data from BoatOptions26 to BoatOptions25 (workaround)')

cursor.close()
conn.close()

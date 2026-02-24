#!/usr/bin/env python3
"""Check Wilson Marine boats status"""
import mysql.connector

MYSQL_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'warrantyparts',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD'
}

conn = mysql.connector.connect(**MYSQL_CONFIG)
cursor = conn.cursor()

wilson_boats = [
    ('ETWS9752K526', 'SO00934762'),
    ('ETWS9874K526', 'SO00934910'),
    ('ETWS0927A626', 'SO00935687'),
]

print("="*100)
print("WILSON MARINE boats check")
print("="*100)

for serial, order_no in wilson_boats:
    print(f"\n{serial}:")
    print("-"*100)
    
    # Check SerialNumberMaster
    cursor.execute("SELECT InvoiceNo, DealerName FROM SerialNumberMaster WHERE Boat_SerialNo = %s", (serial,))
    result = cursor.fetchone()
    if result:
        print(f"  SerialNumberMaster: Invoice={result[0]}, Dealer={result[1]}")
    else:
        print(f"  SerialNumberMaster: NOT FOUND")
    
    # Check BoatOptions26 for BOA/BOI lines
    cursor.execute("""
    SELECT ItemMasterMCT, InvoiceNo, ItemNo, ItemDesc1 
    FROM BoatOptions26 
    WHERE BoatSerialNo = %s AND ItemMasterMCT IN ('BOA', 'BOI')
    """, (serial,))
    
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(f"  BoatOptions26: MCT={row[0]} Invoice={row[1]} Item={row[2]} Desc={row[3]}")
    else:
        print(f"  BoatOptions26: No BOA/BOI lines found")

cursor.close()
conn.close()
print("\n" + "="*100)

#!/usr/bin/env python3
"""Fix Wilson Marine boat invoice numbers"""
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

boats = [
    ('ETWS9752K526', '25226117'),
    ('ETWS9874K526', '25226118'),
    ('ETWS0927A626', '25226119'),
]

print("Fixing Wilson Marine invoice numbers...")
for serial, inv in boats:
    cursor.execute("UPDATE SerialNumberMaster SET InvoiceNo = %s WHERE Boat_SerialNo = %s", (inv, serial))
    print(f"{serial}: Updated to {inv}")

conn.commit()
cursor.close()
conn.close()
print("Done!")

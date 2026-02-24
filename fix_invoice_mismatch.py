#!/usr/bin/env python3
"""Fix SerialNumberMaster to use boat invoice numbers instead of engine invoice numbers"""
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
    ('ETWS0887A626', '25225969'),
    ('ETWS0884A626', '25225990'),
    ('ETWS0889A626', '25225991'),
    ('ETWS0890A626', '25225992'),
    ('ETWS0872A626', '25225968'),
]

print("Fixing SerialNumberMaster invoice numbers...")
for serial, boat_invoice in boats:
    cursor.execute("UPDATE SerialNumberMaster SET InvoiceNo = %s WHERE Boat_SerialNo = %s", (boat_invoice, serial))
    print(f"{serial}: Updated to {boat_invoice}")

conn.commit()
cursor.close()
conn.close()
print("Done!")

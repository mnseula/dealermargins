#!/usr/bin/env python3
"""Check BoatOptions26 for DEFEO boats"""
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

boats = ['ETWS0887A626', 'ETWS0884A626', 'ETWS0889A626', 'ETWS0890A626', 'ETWS0872A626']

for serial in boats:
    print(f"\n{serial}:")
    cursor.execute("SELECT ItemMasterMCT, InvoiceNo, ItemNo FROM BoatOptions26 WHERE BoatSerialNo = %s", (serial,))
    for row in cursor.fetchall():
        print(f"  MCT={row[0] or 'NULL'} Invoice={row[1] or 'NULL'} Item={row[2]}")

cursor.close()
conn.close()
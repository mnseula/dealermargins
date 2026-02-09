#!/usr/bin/env python3
"""
Drop the BoatOptions26_MSRP view since we're using the swap approach instead.
"""
import mysql.connector

db_config = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts'
}

conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

print("Dropping BoatOptions26_MSRP view...")
cursor.execute("DROP VIEW IF EXISTS BoatOptions26_MSRP")
print("✅ View dropped successfully")

cursor.close()
conn.close()

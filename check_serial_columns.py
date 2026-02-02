#!/usr/bin/env python3
import mysql.connector

conn = mysql.connector.connect(
    host='ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    user='awsmaster',
    password='VWvHG9vfG23g7gD',
    database='warrantyparts'
)

cursor = conn.cursor()

# Get column names
cursor.execute("""
    SELECT COLUMN_NAME, DATA_TYPE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'warrantyparts'
    AND TABLE_NAME = 'SerialNumberMaster'
    ORDER BY ORDINAL_POSITION
""")

print("SerialNumberMaster columns:")
print("=" * 60)
for col_name, data_type in cursor.fetchall():
    print(f"{col_name:30s} {data_type}")

cursor.close()
conn.close()

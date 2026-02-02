#!/usr/bin/env python3
import mysql.connector

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts_test'
}

# Read and execute the SQL
with open('test_simple_procedure.sql', 'r') as f:
    sql = f.read()

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()

# Execute the CREATE PROCEDURE part only (remove test call)
create_proc = sql.split('-- Test it')[0]
for stmt in create_proc.split('$$'):
    stmt = stmt.strip().replace('DELIMITER', '').strip()
    if stmt and ';' in stmt:
        try:
            cursor.execute(stmt)
        except Exception as e:
            print(f"Note: {e}")

conn.commit()
print("✓ Simple procedure created")

# Now test it
cursor.close()
cursor = conn.cursor(dictionary=True)
cursor.callproc('TestBoatLookup', ['ETWP6278J324'])

for result in cursor.stored_results():
    rows = result.fetchall()
    print(f"\nFound {len(rows)} rows:")
    for row in rows:
        for key, value in row.items():
            print(f"  {key}: {value}")

cursor.close()
conn.close()

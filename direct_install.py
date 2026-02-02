#!/usr/bin/env python3
import mysql.connector

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts_test'
}

# Read SQL file
with open('GetCompleteBoatInformation_v2.sql', 'r') as f:
    sql = f.read()

# Clean up delimiters and comments
sql_clean = []
for line in sql.split('\n'):
    line = line.strip()
    if line and not line.startswith('--') and 'DELIMITER' not in line and 'Test the procedure' not in line:
        if line.startswith('CALL '):
            continue  # Skip test calls
        sql_clean.append(line)

sql_text = ' '.join(sql_clean)

# Split by $$
parts = [p.strip() for p in sql_text.split('$$') if p.strip()]

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()

# Execute DROP
if parts[0].startswith('DROP'):
    try:
        cursor.execute(parts[0])
        print("✓ Dropped existing procedure")
    except:
        pass

# Execute CREATE  (it's the second part between $$)
if len(parts) > 1:
    create_stmt = parts[1]
    # Make sure it ends properly
    if not create_stmt.strip().endswith('END proc_label'):
        create_stmt = create_stmt.strip().rstrip(';') + ' END proc_label'

    try:
        cursor.execute(create_stmt)
        conn.commit()
        print("✓ Created procedure")
    except Exception as e:
        print(f"Error creating procedure: {e}")
        # Try to see what's wrong
        print(f"Statement length: {len(create_stmt)}")
        print(f"First 200 chars: {create_stmt[:200]}")
        print(f"Last 200 chars: {create_stmt[-200:]}")

cursor.close()
conn.close()

# Now test
print("\nTesting...")
conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor(dictionary=True)

try:
    cursor.callproc('GetCompleteBoatInformation', ['ETWP6278J324'])

    idx = 0
    for result in cursor.stored_results():
        rows = result.fetchall()
        print(f"\nResult Set {idx+1}: {len(rows)} rows")
        if rows and idx == 0:  # Show boat header
            for key, val in rows[0].items():
                print(f"  {key}: {val}")
        elif rows and idx == 2:  # Show MSRP summary
            for row in rows:
                print(f"  {row.get('category', '')}: ${row.get('msrp', 0)}")
        idx += 1

    print("\n✓ SUCCESS!")

except Exception as e:
    print(f"✗ Error: {e}")

cursor.close()
conn.close()

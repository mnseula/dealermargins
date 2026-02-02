#!/usr/bin/env python3
"""
Install and test GetCompleteBoatInformation v2 (corrected columns)
"""

import mysql.connector

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts_test'
}

# Read the SQL file
with open('GetCompleteBoatInformation_v2.sql', 'r') as f:
    sql_content = f.read()

# Extract just the CREATE PROCEDURE statement
lines = []
in_procedure = False
for line in sql_content.split('\n'):
    if 'DROP PROCEDURE' in line:
        lines.append(line)
    elif 'CREATE PROCEDURE' in line:
        in_procedure = True
        lines.append(line)
    elif in_procedure:
        lines.append(line)
        if line.strip().startswith('END proc_label$$'):
            break

procedure_sql = '\n'.join(lines)
procedure_sql = procedure_sql.replace('$$', '')
procedure_sql = procedure_sql.replace('DELIMITER', '').strip()

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()

# Drop existing
try:
    cursor.execute("DROP PROCEDURE IF EXISTS GetCompleteBoatInformation")
    print("✓ Dropped existing procedure")
except Exception as e:
    print(f"Note: {e}")

# Create new (split into DROP and CREATE)
for statement in [s.strip() + ';' for s in procedure_sql.split(';') if s.strip()]:
    if 'DROP PROCEDURE' in statement or 'CREATE PROCEDURE' in statement:
        try:
            # Remove the extra semicolon from END statement
            statement = statement.replace('END proc_label;', 'END proc_label')
            if statement.strip().endswith(';;'):
                statement = statement[:-1]
            cursor.execute(statement)
            conn.commit()
            if 'CREATE' in statement:
                print("✓ Created new procedure")
        except Exception as e:
            print(f"Error: {e}")

cursor.close()
conn.close()

# Test it
print("\n" + "="*70)
print("TESTING PROCEDURE")
print("="*70)

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor(dictionary=True)

cursor.callproc('GetCompleteBoatInformation', ['ETWP6278J324'])

result_sets = [
    "1. BOAT HEADER",
    "2. LINE ITEMS",
    "3. MSRP SUMMARY",
    "4. DEALER MARGINS",
    "5. DEALER COST CALCULATIONS"
]

idx = 0
for result in cursor.stored_results():
    rows = result.fetchall()
    print(f"\n{result_sets[idx]}")
    print("-" * 70)

    if not rows:
        print("  (No data)")
    else:
        # Print header
        if rows:
            headers = list(rows[0].keys())
            print("  " + " | ".join(h[:15] for h in headers))
            print("  " + "-" * 60)

        # Print rows (limit to 5 for line items)
        limit = 5 if 'LINE ITEMS' in result_sets[idx] else 20
        for i, row in enumerate(rows[:limit]):
            values = [str(v)[:15] if v is not None else 'NULL' for v in row.values()]
            print("  " + " | ".join(values))

        if len(rows) > limit:
            print(f"  ... ({len(rows) - limit} more rows)")

        print(f"\n  Total: {len(rows)} rows")

    idx += 1

cursor.close()
conn.close()

print("\n" + "="*70)
print("✓ SUCCESS!")
print("="*70)

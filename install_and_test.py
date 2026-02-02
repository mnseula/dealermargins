#!/usr/bin/env python3
"""
Install and test GetCompleteBoatInformation stored procedure
"""

import mysql.connector

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts_test'
}

def install_procedure():
    """Install the stored procedure using proper multi-statement execution"""
    print("Installing GetCompleteBoatInformation stored procedure...")

    # Read the SQL file
    with open('GetCompleteBoatInformation.sql', 'r') as f:
        sql_content = f.read()

    # Remove comments and DELIMITER statements
    lines = []
    for line in sql_content.split('\n'):
        line = line.strip()
        if line and not line.startswith('--') and not line.startswith('DELIMITER'):
            lines.append(line)

    # Join and split by $$
    sql = ' '.join(lines)
    statements = [s.strip() + ';' for s in sql.split('$$') if s.strip() and 'proc_label' in s]

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Drop existing procedure
    try:
        cursor.execute("DROP PROCEDURE IF EXISTS GetCompleteBoatInformation")
        print("  ✓ Dropped existing procedure")
    except Exception as e:
        print(f"  Note: {e}")

    # Create the procedure - extract just the CREATE statement
    for stmt in statements:
        if 'CREATE PROCEDURE' in stmt:
            try:
                # Remove trailing semicolons and clean up
                stmt = stmt.replace('END proc_label;', 'END')
                cursor.execute(stmt)
                conn.commit()
                print("  ✓ Created procedure successfully")
                break
            except Exception as e:
                print(f"  ERROR: {e}")
                print(f"  Statement preview: {stmt[:200]}...")

    cursor.close()
    conn.close()

def verify_procedure():
    """Verify the procedure exists"""
    print("\nVerifying procedure exists...")
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT ROUTINE_NAME, ROUTINE_TYPE
        FROM information_schema.ROUTINES
        WHERE ROUTINE_SCHEMA = 'warrantyparts_test'
        AND ROUTINE_NAME = 'GetCompleteBoatInformation'
    """)

    result = cursor.fetchone()
    if result:
        print(f"  ✓ Procedure found: {result[0]} ({result[1]})")
    else:
        print("  ✗ Procedure NOT found!")

    cursor.close()
    conn.close()

def test_basic_query():
    """Test basic query to SerialNumberMaster first"""
    print("\nTesting basic SerialNumberMaster query...")
    conn = mysql.connector.connect(**DB_CONFIG)
    conn.database = 'warrantyparts'  # Switch to production database
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            Boat_SerialNo,
            BoatItemNo,
            DealerNumber,
            DealerName,
            Series,
            SN_MY,
            InvoiceNo
        FROM SerialNumberMaster
        WHERE Boat_SerialNo = 'ETWP6278J324'
    """)

    result = cursor.fetchone()
    if result:
        print("  ✓ Boat found in SerialNumberMaster:")
        for key, value in result.items():
            print(f"    {key}: {value}")
    else:
        print("  ✗ Boat NOT found in SerialNumberMaster")

    cursor.close()
    conn.close()

def test_procedure(hull_no):
    """Test the stored procedure with a hull number"""
    print(f"\n{'='*70}")
    print(f"Testing GetCompleteBoatInformation with: {hull_no}")
    print(f"{'='*70}\n")

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    try:
        # Call the procedure
        cursor.callproc('GetCompleteBoatInformation', [hull_no])

        # Fetch all result sets
        result_set_names = [
            "1. BOAT HEADER",
            "2. LINE ITEMS",
            "3. MSRP SUMMARY",
            "4. DEALER MARGINS",
            "5. DEALER COST CALCULATIONS"
        ]

        result_set_index = 0
        for results in cursor.stored_results():
            if result_set_index < len(result_set_names):
                print(f"\n{result_set_names[result_set_index]}")
                print("-" * 70)

                rows = results.fetchall()
                if not rows:
                    print("  (No data)")
                else:
                    # Print all rows
                    for i, row in enumerate(rows):
                        if i == 0:
                            # Print header
                            print("  " + " | ".join(str(k)[:20] for k in row.keys()))
                            print("  " + "-" * 60)
                        # Print row
                        print("  " + " | ".join(str(v)[:20] if v is not None else 'NULL' for v in row.values()))

                    print(f"\n  Total rows: {len(rows)}")

                result_set_index += 1

    except Exception as e:
        print(f"ERROR calling procedure: {e}")
        import traceback
        traceback.print_exc()

    cursor.close()
    conn.close()

    print(f"\n{'='*70}\n")

if __name__ == '__main__':
    # Step 1: Install
    install_procedure()

    # Step 2: Verify
    verify_procedure()

    # Step 3: Test basic query
    test_basic_query()

    # Step 4: Test procedure
    test_procedure('ETWP6278J324')

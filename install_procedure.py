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
    """Install the stored procedure"""
    print("Installing GetCompleteBoatInformation stored procedure...")

    # Read the SQL file
    with open('GetCompleteBoatInformation.sql', 'r') as f:
        sql_content = f.read()

    # Split by delimiter changes and execute
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Execute the SQL (handle multi-statement)
    for statement in sql_content.split('$$'):
        statement = statement.strip()
        if statement and not statement.startswith('--') and statement != 'DELIMITER':
            try:
                cursor.execute(statement)
            except Exception as e:
                if 'Commands out of sync' not in str(e):
                    print(f"Note: {e}")

    conn.commit()
    cursor.close()
    conn.close()

    print("✓ Stored procedure installed successfully!")

def test_procedure(hull_no):
    """Test the stored procedure with a hull number"""
    print(f"\n{'='*70}")
    print(f"Testing with Hull#: {hull_no}")
    print(f"{'='*70}\n")

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

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

    for idx, result_name in enumerate(result_set_names, 1):
        print(f"\n{result_name}")
        print("-" * 70)

        # Fetch results from current result set
        results = cursor.fetchall()

        if not results:
            print("  (No data)")
        else:
            # Print first few rows
            for i, row in enumerate(results[:10]):  # Limit to 10 rows for display
                if i == 0:
                    # Print header
                    print("  " + " | ".join(row.keys()))
                    print("  " + "-" * 60)
                # Print row
                print("  " + " | ".join(str(v)[:20] for v in row.values()))

            if len(results) > 10:
                print(f"  ... ({len(results) - 10} more rows)")

        # Move to next result set
        if cursor.nextset():
            pass
        else:
            break

    cursor.close()
    conn.close()

    print(f"\n{'='*70}")
    print("✓ Test complete!")
    print(f"{'='*70}\n")

if __name__ == '__main__':
    # Install procedure
    install_procedure()

    # Test with known hull numbers
    print("\n" + "="*70)
    print("TESTING STORED PROCEDURE")
    print("="*70)

    # Test 1: 2024 boat with pricing
    test_procedure('ETWP6278J324')

    print("\n\nNode.js Usage Example:")
    print("-" * 70)
    print("""
// Node.js with mysql2
const mysql = require('mysql2/promise');

const connection = await mysql.createConnection({
  host: 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
  user: 'awsmaster',
  password: 'VWvHG9vfG23g7gD',
  database: 'warrantyparts_test',
  multipleStatements: true
});

// Call the stored procedure
const [results] = await connection.query(
  'CALL GetCompleteBoatInformation(?)',
  ['ETWP6278J324']
);

// Access the 5 result sets:
const boatHeader = results[0];       // Boat info, dealer, colors, etc.
const lineItems = results[1];        // All line items from BoatOptions
const msrpSummary = results[2];      // MSRP totals by category
const dealerMargins = results[3];    // Margin percentages
const dealerCosts = results[4];      // Dealer cost calculations

console.log('Boat:', boatHeader[0].model_no);
console.log('Dealer:', boatHeader[0].dealer_name);
console.log('Total MSRP:', msrpSummary.find(r => r.category === 'TOTAL').msrp);
console.log('Total Dealer Cost:', dealerCosts.find(r => r.category === 'TOTAL').dealer_cost);
    """)

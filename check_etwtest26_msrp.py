#!/usr/bin/env python3
"""
Check MSRP data for test boat ETWTEST26.
"""
import mysql.connector

# Database configuration
db_config = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts'
}

def check_test_boat_data():
    """Check MSRP data for ETWTEST26."""
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    print("=" * 80)
    print("CHECKING ETWTEST26 DATA IN BoatOptions26")
    print("=" * 80)

    # Get all data for test boat
    query = """
        SELECT
            LineNo,
            ItemNo,
            ItemDesc1,
            ExtSalesAmount,
            MSRP,
            MCTDesc,
            InvoiceNo
        FROM BoatOptions26
        WHERE BoatSerialNo = 'ETWTEST26'
        ORDER BY LineNo
    """

    cursor.execute(query)
    rows = cursor.fetchall()

    if rows:
        print(f"\nFound {len(rows)} items for ETWTEST26:\n")
        for row in rows:
            msrp_status = "✅" if row['MSRP'] and float(row['MSRP']) > 0 else "❌"
            print(f"{msrp_status} Line {row['LineNo']:3d}: {row['ItemDesc1']:30s}")
            print(f"    ExtSalesAmount: ${row['ExtSalesAmount']:>10,.2f}")
            print(f"    MSRP:           ${row['MSRP'] or 0:>10,.2f}")
            print(f"    MCTDesc:        {row['MCTDesc']}")
            print(f"    InvoiceNo:      {row['InvoiceNo']}")
            print()
    else:
        print("❌ No data found for ETWTEST26")

    # Count MSRP values
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN MSRP IS NOT NULL AND MSRP > 0 THEN 1 ELSE 0 END) as with_msrp
        FROM BoatOptions26
        WHERE BoatSerialNo = 'ETWTEST26'
    """)
    counts = cursor.fetchone()

    print("=" * 80)
    print(f"SUMMARY: {counts['with_msrp']} out of {counts['total']} items have MSRP data")
    print("=" * 80)

    cursor.close()
    conn.close()

if __name__ == '__main__':
    check_test_boat_data()

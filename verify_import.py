#!/usr/bin/env python3
"""
Verify BoatOptions Test Import Data Quality

Checks:
1. MCTDesc and ItemMasterMCT are populated
2. CPQ configured items have ConfigID
3. Invoice numbers exist (invoiced only)
4. Sample data looks correct
"""
import mysql.connector

MYSQL_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'warrantyparts_boatoptions_test',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD'
}

def check_critical_fields():
    """Check that critical fields are populated"""
    print("="*80)
    print("CHECKING CRITICAL FIELDS")
    print("="*80)

    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()

        # Check across recent year tables (24, 25, 26)
        for table in ['BoatOptions24', 'BoatOptions25', 'BoatOptions26']:
            print(f"\n{table}:")
            print("-"*80)

            # Total rows
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            total = cursor.fetchone()[0]
            print(f"  Total rows: {total:,}")

            # Check MCTDesc populated
            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE MCTDesc IS NOT NULL AND MCTDesc != ''")
            mct_desc_count = cursor.fetchone()[0]
            pct = (mct_desc_count / total * 100) if total > 0 else 0
            print(f"  MCTDesc populated: {mct_desc_count:,} ({pct:.1f}%)")

            # Check ItemMasterMCT populated
            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE ItemMasterMCT IS NOT NULL AND ItemMasterMCT != ''")
            mct_count = cursor.fetchone()[0]
            pct = (mct_count / total * 100) if total > 0 else 0
            print(f"  ItemMasterMCT populated: {mct_count:,} ({pct:.1f}%)")

            # Check ConfigID for configured items
            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE ConfigID IS NOT NULL AND ConfigID != ''")
            config_count = cursor.fetchone()[0]
            pct = (config_count / total * 100) if total > 0 else 0
            print(f"  ConfigID populated: {config_count:,} ({pct:.1f}%) - CPQ configured items")

            # Check InvoiceNo (should be 100% since we filtered for invoiced only)
            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE InvoiceNo IS NOT NULL AND InvoiceNo != ''")
            invoice_count = cursor.fetchone()[0]
            pct = (invoice_count / total * 100) if total > 0 else 0
            status = "✅" if pct > 95 else "⚠️"
            print(f"  {status} InvoiceNo populated: {invoice_count:,} ({pct:.1f}%)")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")

def check_mct_codes():
    """Check distribution of MCT codes"""
    print("\n" + "="*80)
    print("MCT CODE DISTRIBUTION (BoatOptions25 & BoatOptions26)")
    print("="*80)

    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                ItemMasterMCT,
                MCTDesc,
                COUNT(*) as count
            FROM (
                SELECT ItemMasterMCT, MCTDesc FROM BoatOptions25
                UNION ALL
                SELECT ItemMasterMCT, MCTDesc FROM BoatOptions26
            ) combined
            WHERE ItemMasterMCT IS NOT NULL
            GROUP BY ItemMasterMCT, MCTDesc
            ORDER BY count DESC
            LIMIT 20
        """)

        results = cursor.fetchall()

        print(f"\n{'MCT Code':<12} {'Description':<30} {'Count':>10}")
        print("-"*80)
        for row in results:
            mct = row[0] or ''
            desc = (row[1] or '')[:30]
            count = row[2]
            print(f"{mct:<12} {desc:<30} {count:>10,}")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")

def check_cpq_orders():
    """Check CPQ configured items"""
    print("\n" + "="*80)
    print("CPQ CONFIGURED ITEMS")
    print("="*80)

    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()

        # Check BoatOptions25 and BoatOptions26 for configured items
        for table in ['BoatOptions25', 'BoatOptions26']:
            cursor.execute(f"""
                SELECT COUNT(DISTINCT ERP_OrderNo)
                FROM {table}
                WHERE ConfigID IS NOT NULL AND ConfigID != ''
            """)
            order_count = cursor.fetchone()[0]

            cursor.execute(f"""
                SELECT COUNT(*)
                FROM {table}
                WHERE ConfigID IS NOT NULL AND ConfigID != ''
            """)
            line_count = cursor.fetchone()[0]

            print(f"\n{table}:")
            print(f"  CPQ Orders: {order_count}")
            print(f"  Configured line items: {line_count}")

        # Sample configured items
        print("\nSample CPQ configured items:")
        print("-"*80)
        cursor.execute("""
            SELECT
                ERP_OrderNo,
                BoatSerialNo,
                ItemNo,
                ItemDesc1,
                ConfigID
            FROM BoatOptions26
            WHERE ConfigID IS NOT NULL AND ConfigID != ''
            LIMIT 5
        """)

        results = cursor.fetchall()
        for row in results:
            print(f"  Order: {row[0]}, Serial: {row[1]}")
            print(f"    Item: {row[2] or '(no item#)'} - {row[3]}")
            print(f"    ConfigID: {row[4]}")
            print()

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")

def check_sample_data():
    """Show sample data from different years"""
    print("\n" + "="*80)
    print("SAMPLE DATA")
    print("="*80)

    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()

        # Sample from BoatOptions26 (latest CPQ)
        print("\nBoatOptions26 Sample (recent CPQ data):")
        print("-"*80)
        cursor.execute("""
            SELECT
                ERP_OrderNo,
                BoatSerialNo,
                ItemNo,
                ItemDesc1,
                ItemMasterMCT,
                MCTDesc,
                ExtSalesAmount
            FROM BoatOptions26
            LIMIT 5
        """)

        results = cursor.fetchall()
        for row in results:
            print(f"  Order: {row[0]}, Serial: {row[1]}")
            print(f"    Item: {row[2]} - {row[3]}")
            print(f"    MCT: {row[4]} ({row[5]}) - ${row[6]:,.2f}" if row[6] else f"    MCT: {row[4]} ({row[5]})")
            print()

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("="*80)
    print("BOATOPTIONS TEST IMPORT VERIFICATION")
    print("="*80)
    print()

    check_critical_fields()
    check_mct_codes()
    check_cpq_orders()
    check_sample_data()

    print("\n" + "="*80)
    print("✅ VERIFICATION COMPLETE")
    print("="*80)
    print("\nIf all checks look good, the import was successful!")
    print("Next step: Create production version of import script")

if __name__ == '__main__':
    main()

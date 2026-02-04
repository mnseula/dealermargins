#!/usr/bin/env python3
"""
Investigate order types and why BB orders have no line items
"""
import pymssql

MSSQL_CONFIG = {
    'server': 'MPL1STGSQL086.POLARISSTAGE.COM',
    'database': 'CSISTG',
    'user': 'svccsimarine',
    'password': 'CNKmoFxEsXs0D9egZQXH'
}

def main():
    print("="*120)
    print("INVESTIGATING ORDER TYPES")
    print("="*120)

    try:
        conn = pymssql.connect(**MSSQL_CONFIG)
        cursor = conn.cursor()
        print("✅ Connected to MSSQL\n")

        # 1. Check if BB00139960 exists in coitem_mst
        print("="*120)
        print("CHECKING IF ORDER BB00139960 EXISTS IN COITEM_MST:")
        print("="*120)
        cursor.execute("""
            SELECT co_num, co_line, item, site_ref
            FROM coitem_mst
            WHERE co_num = 'BB00139960'
        """)
        items = cursor.fetchall()
        if items:
            print(f"\n  Found {len(items)} line items:")
            for item in items:
                print(f"    {item}")
        else:
            print("  No line items found for BB00139960")

        # 2. Sample recent orders with line items
        print("\n" + "="*120)
        print("RECENT ORDERS WITH LINE ITEMS:")
        print("="*120)
        cursor.execute("""
            SELECT TOP 10
                co_num,
                site_ref,
                COUNT(*) as line_count,
                MIN(item) as sample_item
            FROM coitem_mst
            WHERE site_ref = 'BENN'
            GROUP BY co_num, site_ref
            ORDER BY co_num DESC
        """)

        orders = cursor.fetchall()
        if orders:
            print(f"\n{'Order#':<20} {'Site':<10} {'Lines':<10} {'Sample Item':<30}")
            print("-"*70)
            for row in orders:
                print(f"{row[0]:<20} {row[1]:<10} {row[2]:<10} {row[3]:<30}")
        else:
            print("  No orders found")

        # 3. Check if SO orders vs BB orders
        print("\n" + "="*120)
        print("ORDER NUMBER PREFIXES:")
        print("="*120)
        cursor.execute("""
            SELECT
                LEFT(co_num, 2) as prefix,
                COUNT(DISTINCT co_num) as order_count,
                SUM(1) as line_count
            FROM coitem_mst
            WHERE site_ref = 'BENN'
            GROUP BY LEFT(co_num, 2)
            ORDER BY order_count DESC
        """)

        prefixes = cursor.fetchall()
        if prefixes:
            print(f"\n{'Prefix':<10} {'Orders':<15} {'Total Lines':<15}")
            print("-"*40)
            for row in prefixes:
                print(f"{row[0]:<10} {row[1]:<15,} {row[2]:<15,}")
        else:
            print("  No orders found")

        # 4. Try SO orders instead
        print("\n" + "="*120)
        print("TRYING SO ORDER (SO00927911) FROM SERIAL:")
        print("="*120)
        cursor.execute("""
            SELECT
                coi.co_num,
                coi.co_line,
                coi.item,
                itm.description,
                itm.product_code,
                pc.description as prod_desc
            FROM coitem_mst coi
            JOIN item_mst itm ON coi.item = itm.item AND coi.site_ref = itm.site_ref
            LEFT JOIN prodcode_mst pc ON itm.product_code = pc.product_code AND itm.site_ref = pc.site_ref
            WHERE coi.co_num = 'SO00927911'
              AND coi.site_ref = 'BENN'
            ORDER BY coi.co_line
        """)

        items = cursor.fetchall()
        if items:
            print(f"\n  Found {len(items)} line items:")
            print(f"\n  {'Line':<6} {'Item':<20} {'ProdCode':<10} {'Prod Desc':<30} {'Item Description':<40}")
            print("  " + "-"*110)
            for row in items:
                line = row[1] or ''
                item = (row[2] or '')[:20]
                desc = (row[3] or '')[:40]
                prod = row[4] or ''
                prod_desc = (row[5] or '')[:30]
                print(f"  {line:<6} {item:<20} {prod:<10} {prod_desc:<30} {desc:<40}")
        else:
            print("  No line items found")

        # 5. Check job_mst for BB orders (might be production orders)
        print("\n" + "="*120)
        print("CHECKING IF BB ORDERS ARE IN JOB_MST (PRODUCTION ORDERS):")
        print("="*120)
        cursor.execute("""
            SELECT TOP 10
                job,
                suffix,
                item,
                description,
                site_ref,
                Uf_BENN_PlannedSerialNumber
            FROM job_mst
            WHERE site_ref = 'BENN'
              AND (job LIKE 'BB%' OR Uf_BENN_PlannedSerialNumber = 'ETWC6627J526')
            ORDER BY CreateDate DESC
        """)

        jobs = cursor.fetchall()
        if jobs:
            print(f"\n{'Job#':<15} {'Suffix':<8} {'Item':<20} {'Serial':<20} {'Description':<40}")
            print("-"*110)
            for row in jobs:
                job = row[0] or ''
                suffix = row[1] or ''
                item = (row[2] or '')[:20]
                desc = (row[3] or '')[:40]
                serial = row[5] or ''
                print(f"{job:<15} {suffix:<8} {item:<20} {serial:<20} {desc:<40}")
        else:
            print("  No BB jobs found")

        # 6. Check jobtran for materials issued to jobs
        print("\n" + "="*120)
        print("CHECKING JOBTRAN FOR MATERIALS ON JOB BB00139960:")
        print("="*120)
        cursor.execute("""
            SELECT TOP 20
                jt.job,
                jt.suffix,
                jt.oper_num,
                jt.item,
                itm.description,
                itm.product_code,
                pc.description as prod_desc,
                jt.qty_complete
            FROM jobtran jt
            JOIN item_mst itm ON jt.item = itm.item AND jt.site_ref = itm.site_ref
            LEFT JOIN prodcode_mst pc ON itm.product_code = pc.product_code AND itm.site_ref = pc.site_ref
            WHERE jt.job = 'BB00139960'
              AND jt.site_ref = 'BENN'
            ORDER BY jt.trans_date DESC
        """)

        trans = cursor.fetchall()
        if trans:
            print(f"\n  Found {len(trans)} transactions:")
            print(f"\n  {'Job':<15} {'Suf':<6} {'Item':<20} {'ProdCode':<10} {'Prod Desc':<30} {'Qty':<10} {'Item Desc':<40}")
            print("  " + "-"*120)
            for row in trans:
                job = row[0] or ''
                suf = row[1] or ''
                item = (row[3] or '')[:20]
                desc = (row[4] or '')[:40]
                prod = row[5] or ''
                prod_desc = (row[6] or '')[:30]
                qty = row[7] or 0
                print(f"  {job:<15} {suf:<6} {item:<20} {prod:<10} {prod_desc:<30} {qty:<10.2f} {desc:<40}")
        else:
            print("  No job transactions found")

        cursor.close()
        conn.close()

        print("\n" + "="*120)
        print("INVESTIGATION COMPLETE")
        print("="*120)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

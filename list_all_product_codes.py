#!/usr/bin/env python3
"""
List ALL Product Codes in MSSQL

This script shows ALL product codes that exist in coitem_mst,
regardless of our filter list.

Usage:
    python3 list_all_product_codes.py
"""

import pymssql

MSSQL_CONFIG = {
    'server': 'MPL1STGSQL086.POLARISSTAGE.COM',
    'database': 'CSISTG',
    'user': 'svccsimarine',
    'password': 'CNKmoFxEsXs0D9egZQXH'
}

def list_all_codes():
    """List all product codes that exist"""
    print("="*70)
    print("ALL PRODUCT CODES IN MSSQL (coitem_mst + item_mst)")
    print("="*70)

    query = """
    SELECT
        im.product_code,
        COUNT(*) as row_count,
        COUNT(DISTINCT coi.co_num) as order_count,
        COUNT(DISTINCT CASE WHEN coi.Uf_BENN_BoatSerialNumber IS NOT NULL
                            AND coi.Uf_BENN_BoatSerialNumber != ''
                            THEN coi.Uf_BENN_BoatSerialNumber END) as boats_with_serial,
        COUNT(DISTINCT CASE WHEN coi.Uf_BENN_BoatModel IS NOT NULL
                            AND coi.Uf_BENN_BoatModel != ''
                            THEN coi.Uf_BENN_BoatModel END) as boats_with_model
    FROM [CSISTG].[dbo].[coitem_mst] coi
    LEFT JOIN [CSISTG].[dbo].[item_mst] im
        ON coi.item = im.item AND coi.site_ref = im.site_ref
    WHERE coi.site_ref = 'BENN'
    GROUP BY im.product_code
    ORDER BY row_count DESC
    """

    try:
        conn = pymssql.connect(**MSSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()

        print(f"\nFound {len(rows)} unique product codes\n")
        print(f"{'Code':10s} {'Rows':>12s} {'Orders':>10s} {'W/Serial':>10s} {'W/Model':>10s}")
        print("-" * 60)

        total_rows = 0
        for row in rows:
            code = row[0] or 'NULL'
            total_rows += row[1]
            print(f"{code:10s} {row[1]:12,d} {row[2]:10,d} {row[3]:10,d} {row[4]:10,d}")

        print("-" * 60)
        print(f"{'TOTAL':10s} {total_rows:12,d}")

        cursor.close()
        conn.close()

        return rows

    except Exception as e:
        print(f"Error: {e}")
        return []

def show_recommended_codes(all_codes):
    """Show codes we should probably include"""
    print("\n" + "="*70)
    print("RECOMMENDED CODES FOR BOAT BUILDS")
    print("="*70)

    # Common boat-related patterns
    boat_patterns = ['BS', 'EN', 'ACC', 'H1', 'L0', 'L1', 'L2', 'ASY', '00', '01', '02', '03']

    recommended = []
    for row in all_codes:
        code = row[0] or ''
        row_count = row[1]

        # Include if matches patterns and has significant data
        for pattern in boat_patterns:
            if code.startswith(pattern) and row_count > 10:
                recommended.append(row)
                break

    print(f"\nFound {len(recommended)} recommended codes:\n")
    print(f"{'Code':10s} {'Rows':>12s} {'Orders':>10s}")
    print("-" * 40)
    for row in recommended:
        code = row[0] or 'NULL'
        print(f"{code:10s} {row[1]:12,d} {row[2]:10,d}")

    return recommended

def compare_to_our_filter(all_codes):
    """Compare actual codes to our filter list"""
    print("\n" + "="*70)
    print("COMPARISON: OUR FILTER vs ACTUAL DATA")
    print("="*70)

    our_codes = [
        'BS1', 'EN7', 'ENG', 'ENI', 'EN9', 'EN4', 'ENA', 'EN2', 'EN3', 'EN8', 'ENT',
        'ACC', 'H1', 'H1P', 'H1V', 'H1I', 'H1F', 'H3A', 'H5',
        'L0', 'L2', 'L12',
        '003', '008', '024', '090', '302',
        'ASY',
        '010', '011', '005', '006', '015', '017', '023', '029', '030'
    ]

    actual_codes_dict = {row[0]: row[1] for row in all_codes if row[0]}

    print(f"\nOur filter: {len(our_codes)} codes")
    print(f"Codes in MSSQL: {len(actual_codes_dict)} codes\n")

    found = []
    not_found = []

    for code in our_codes:
        if code in actual_codes_dict:
            found.append((code, actual_codes_dict[code]))
        else:
            not_found.append(code)

    print(f"✅ FOUND in MSSQL ({len(found)} codes):")
    print(f"{'Code':10s} {'Rows':>12s}")
    print("-" * 25)
    for code, count in sorted(found, key=lambda x: x[1], reverse=True):
        print(f"{code:10s} {count:12,d}")

    print(f"\n❌ NOT FOUND in MSSQL ({len(not_found)} codes):")
    print(", ".join(not_found))

if __name__ == '__main__':
    all_codes = list_all_codes()

    if all_codes:
        show_recommended_codes(all_codes)
        compare_to_our_filter(all_codes)

    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)

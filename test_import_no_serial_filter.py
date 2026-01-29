#!/usr/bin/env python3
"""
Test import WITHOUT serial number requirement

This is a diagnostic script to see how many rows exist WITHOUT
requiring Uf_BENN_BoatSerialNumber to be populated.

Usage:
    python3 test_import_no_serial_filter.py
"""

import pymssql

MSSQL_CONFIG = {
    'server': 'MPL1STGSQL086.POLARISSTAGE.COM',
    'database': 'CSISTG',
    'user': 'svccsimarine',
    'password': 'CNKmoFxEsXs0D9egZQXH'
}

PRODUCT_CODES = [
    'BS1', 'EN7', 'ENG', 'ENI', 'EN9', 'EN4', 'ENA', 'EN2', 'EN3', 'EN8', 'ENT',
    'ACC', 'H1', 'H1P', 'H1V', 'H1I', 'H1F', 'H3A', 'H5',
    'L0', 'L2', 'L12',
    '003', '008', '024', '090', '302',
    'ASY',
    '010', '011', '005', '006', '015', '017', '023', '029', '030'
]

def test_with_serial():
    """Test WITH serial number requirement"""
    print("="*70)
    print("TEST 1: WITH Serial Number Requirement")
    print("="*70)

    product_code_list = "'" + "','".join(PRODUCT_CODES) + "'"

    query = f"""
    SELECT COUNT(*) as total_rows,
           COUNT(DISTINCT coi.Uf_BENN_BoatSerialNumber) as unique_boats,
           COUNT(DISTINCT coi.co_num) as unique_orders
    FROM [CSISTG].[dbo].[coitem_mst] coi
    LEFT JOIN [CSISTG].[dbo].[item_mst] im ON coi.item = im.item AND coi.site_ref = im.site_ref
    WHERE coi.site_ref = 'BENN'
        AND coi.Uf_BENN_BoatSerialNumber IS NOT NULL
        AND coi.Uf_BENN_BoatSerialNumber != ''
        AND im.product_code IN ({product_code_list})
    """

    try:
        conn = pymssql.connect(**MSSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute(query)
        row = cursor.fetchone()

        print(f"Total rows:        {row[0]:,}")
        print(f"Unique boats:      {row[1]:,}")
        print(f"Unique orders:     {row[2]:,}")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

def test_without_serial():
    """Test WITHOUT serial number requirement"""
    print("\n" + "="*70)
    print("TEST 2: WITHOUT Serial Number Requirement")
    print("="*70)

    product_code_list = "'" + "','".join(PRODUCT_CODES) + "'"

    query = f"""
    SELECT COUNT(*) as total_rows,
           COUNT(DISTINCT coi.co_num) as unique_orders,
           COUNT(DISTINCT CASE WHEN coi.Uf_BENN_BoatSerialNumber IS NOT NULL
                               AND coi.Uf_BENN_BoatSerialNumber != ''
                               THEN coi.Uf_BENN_BoatSerialNumber END) as boats_with_serial,
           COUNT(DISTINCT CASE WHEN coi.Uf_BENN_BoatSerialNumber IS NULL
                               OR coi.Uf_BENN_BoatSerialNumber = ''
                               THEN coi.co_num END) as orders_without_serial
    FROM [CSISTG].[dbo].[coitem_mst] coi
    LEFT JOIN [CSISTG].[dbo].[item_mst] im ON coi.item = im.item AND coi.site_ref = im.site_ref
    WHERE coi.site_ref = 'BENN'
        AND im.product_code IN ({product_code_list})
    """

    try:
        conn = pymssql.connect(**MSSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute(query)
        row = cursor.fetchone()

        print(f"Total rows:             {row[0]:,}")
        print(f"Unique orders:          {row[1]:,}")
        print(f"Boats WITH serial:      {row[2]:,}")
        print(f"Orders WITHOUT serial:  {row[3]:,}")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

def test_product_codes():
    """Show what product codes exist"""
    print("\n" + "="*70)
    print("TEST 3: Product Code Distribution")
    print("="*70)

    product_code_list = "'" + "','".join(PRODUCT_CODES) + "'"

    query = f"""
    SELECT TOP 20
        im.product_code,
        COUNT(*) as row_count,
        COUNT(DISTINCT CASE WHEN coi.Uf_BENN_BoatSerialNumber IS NOT NULL
                            AND coi.Uf_BENN_BoatSerialNumber != ''
                            THEN coi.Uf_BENN_BoatSerialNumber END) as boats_with_serial
    FROM [CSISTG].[dbo].[coitem_mst] coi
    LEFT JOIN [CSISTG].[dbo].[item_mst] im ON coi.item = im.item AND coi.site_ref = im.site_ref
    WHERE coi.site_ref = 'BENN'
        AND im.product_code IN ({product_code_list})
    GROUP BY im.product_code
    ORDER BY row_count DESC
    """

    try:
        conn = pymssql.connect(**MSSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()

        print(f"\n{'Code':5s} {'Rows':>10s} {'Boats':>10s}")
        print("-" * 30)
        for row in rows:
            print(f"{row[0] or 'NULL':5s} {row[1]:10,d} {row[2]:10,d}")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    print("MSSQL DATA DIAGNOSTIC TEST")
    print(f"Testing {len(PRODUCT_CODES)} product codes")
    print()

    test_with_serial()
    test_without_serial()
    test_product_codes()

    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)

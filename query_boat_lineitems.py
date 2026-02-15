#!/usr/bin/env python3
"""
Query Boat Line Items from ERP

Fetches all line items for a specific order from the ERP system
to see what would be imported.

Usage:
    python3 query_boat_lineitems.py <order_no>

Example:
    python3 query_boat_lineitems.py SO00936074

Author: Claude Code
Date: 2026-02-10
"""

import pymssql
import sys
from datetime import datetime

MSSQL_CONFIG = {
    'server': 'MPL1STGSQL086.POLARISSTAGE.COM',
    'database': 'CSISTG',
    'user': 'svccsimarine',
    'password': 'CNKmoFxEsXs0D9egZQXH',
    'timeout': 300,
    'login_timeout': 60
}

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 query_boat_lineitems.py <order_no>")
        print("Example: python3 query_boat_lineitems.py SO00936074")
        return 1

    order_no = sys.argv[1]

    print("="*80)
    print("BOAT LINE ITEMS QUERY")
    print("="*80)
    print(f"Order: {order_no}")
    print("="*80)
    print()

    try:
        conn = pymssql.connect(**MSSQL_CONFIG)
        cursor = conn.cursor(as_dict=True)

        # Get order header info
        cursor.execute("""
            SELECT
                co_num,
                order_date,
                type,
                external_confirmation_ref
            FROM co_mst
            WHERE co_num = %s
              AND site_ref = 'BENN'
        """, (order_no,))

        order = cursor.fetchone()

        if not order:
            print(f"❌ Order {order_no} not found in ERP")
            return 1

        print("ORDER HEADER:")
        print(f"  Order Number: {order['co_num']}")
        print(f"  Order Date: {order['order_date']}")
        print(f"  Type: {order['type']}")
        print(f"  External Ref: {order['external_confirmation_ref']}")
        print()

        # Get line items
        cursor.execute("""
            SELECT
                coi.co_line,
                coi.item,
                coi.description,
                coi.Uf_BENN_BoatSerialNumber,
                coi.Uf_BENN_BoatModel,
                coi.config_id,
                coi.qty_ordered,
                coi.qty_invoiced,
                coi.price,
                im.Uf_BENN_ProductCategory,
                im.Uf_BENN_MaterialCostType,
                im.Uf_BENN_Series
            FROM coitem_mst coi
            LEFT JOIN item_mst im
                ON coi.item = im.item
                AND coi.site_ref = im.site_ref
            WHERE coi.co_num = %s
              AND coi.site_ref = 'BENN'
            ORDER BY coi.co_line
        """, (order_no,))

        items = cursor.fetchall()

        if not items:
            print(f"❌ No line items found for order {order_no}")
            return 1

        print(f"LINE ITEMS ({len(items)} total):")
        print("="*80)

        for item in items:
            print(f"\nLine {item['co_line']}: {item['item']}")
            print(f"  Description: {item['description']}")
            print(f"  Serial Number: {item['Uf_BENN_BoatSerialNumber'] or 'N/A'}")
            print(f"  Boat Model: {item['Uf_BENN_BoatModel'] or 'N/A'}")
            print(f"  Config ID: {item['config_id'] or 'N/A'}")
            print(f"  Product Category: {item['Uf_BENN_ProductCategory'] or 'N/A'}")
            print(f"  Material Cost Type: {item['Uf_BENN_MaterialCostType'] or 'N/A'}")
            print(f"  Series: {item['Uf_BENN_Series'] or 'N/A'}")
            print(f"  Qty Ordered: {item['qty_ordered']}, Qty Invoiced: {item['qty_invoiced']}")
            print(f"  Price: ${item['price']:.2f}")

        print()
        print("="*80)

        # Check if this is a CPQ order
        has_config = any(item['config_id'] for item in items)

        if has_config:
            print("✅ This is a CPQ-CONFIGURED ORDER (has config_id)")
            print()

            # Get configuration attributes
            cursor.execute("""
                SELECT DISTINCT coi.config_id
                FROM coitem_mst coi
                WHERE coi.co_num = %s
                  AND coi.site_ref = 'BENN'
                  AND coi.config_id IS NOT NULL
            """, (order_no,))

            configs = cursor.fetchall()

            for config in configs:
                config_id = config['config_id']
                print(f"Configuration ID: {config_id}")

                cursor.execute("""
                    SELECT TOP 10
                        attr_name,
                        attr_value,
                        Uf_BENN_Cfg_Name,
                        Uf_BENN_Cfg_Value,
                        Uf_BENN_Cfg_Price,
                        Uf_BENN_Cfg_MSRP
                    FROM cfg_attr_mst
                    WHERE config_id = %s
                      AND site_ref = 'BENN'
                      AND attr_value IS NOT NULL
                      AND print_flag = 'E'
                    ORDER BY attr_name
                """, (config_id,))

                attrs = cursor.fetchall()

                if attrs:
                    print(f"  Configuration Attributes ({len(attrs)} shown, may be more):")
                    for attr in attrs:
                        print(f"    - {attr['attr_name']}: {attr['attr_value']}")
                        if attr['Uf_BENN_Cfg_Name']:
                            print(f"      CfgName: {attr['Uf_BENN_Cfg_Name']}")
                        if attr['Uf_BENN_Cfg_Price']:
                            print(f"      Price: ${attr['Uf_BENN_Cfg_Price']}")
                print()
        else:
            print("⚠️  This is NOT a CPQ order (no config_id)")

        print("="*80)

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == '__main__':
    exit(main())

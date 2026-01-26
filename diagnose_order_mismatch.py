#!/usr/bin/env python3
"""
Diagnose why orders from BoatConfigurationAttributes are not found in SQL Server
"""
import pymssql
import mysql.connector
from datetime import datetime

# SQL Server Configuration
SQL_SERVER = "MPL1STGSQL086.POLARISSTAGE.COM"
SQL_DATABASE = "CSISTG"
SQL_USERNAME = "svccsimarine"
SQL_PASSWORD = "CNKmoFxEsXs0D9egZQXH"

# MySQL Configuration
MYSQL_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts_test'
}

print("=" * 80)
print("DIAGNOSING ORDER MISMATCH")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Step 1: Get orders from MySQL
print("\n📊 STEP 1: Getting orders from BoatConfigurationAttributes...")
mysql_conn = mysql.connector.connect(**MYSQL_CONFIG)
mysql_cursor = mysql_conn.cursor()

mysql_cursor.execute("""
    SELECT DISTINCT erp_order_no, boat_model_no, COUNT(*) as attr_count
    FROM BoatConfigurationAttributes
    WHERE erp_order_no IS NOT NULL
    AND erp_order_no != ''
    GROUP BY erp_order_no, boat_model_no
    LIMIT 10
""")

mysql_orders = mysql_cursor.fetchall()
mysql_cursor.close()
mysql_conn.close()

if not mysql_orders:
    print("   ❌ No orders found in BoatConfigurationAttributes")
    exit(1)

print(f"   ✅ Found {len(mysql_orders)} orders (showing first 10)")
print("\n   Orders from BoatConfigurationAttributes:")
print(f"   {'Order Number':<20} {'Model':<15} {'Config Attrs':<15}")
print("   " + "-" * 50)
for order in mysql_orders:
    print(f"   {order[0]:<20} {order[1]:<15} {order[2]:<15}")

test_order = mysql_orders[0][0]
print(f"\n   Using test order: {test_order}")

# Step 2: Check SQL Server
print("\n📦 STEP 2: Checking SQL Server for these orders...")

try:
    print(f"   Connecting to {SQL_SERVER}...")
    conn = pymssql.connect(
        server=SQL_SERVER,
        database=SQL_DATABASE,
        user=SQL_USERNAME,
        password=SQL_PASSWORD,
        timeout=60,
        login_timeout=60
    )
    cursor = conn.cursor(as_dict=True)
    print("   ✅ Connected to SQL Server")

    # Check exact match
    print(f"\n   Checking for exact match: '{test_order}'")
    cursor.execute("""
        SELECT TOP 5 co_num, item, qty_ordered, price
        FROM [CSISTG].[dbo].[coitem_mst]
        WHERE co_num = %s
        AND site_ref = 'BENN'
    """, (test_order,))

    exact_matches = cursor.fetchall()
    if exact_matches:
        print(f"   ✅ Found {len(exact_matches)} line items for {test_order}")
        print("\n   Sample line items:")
        for row in exact_matches:
            print(f"      Order: {row['co_num']}, Item: {row['item']}, Qty: {row['qty_ordered']}, Price: ${row['price']}")
    else:
        print(f"   ❌ No exact match for '{test_order}'")

        # Try variations
        print("\n   Trying variations...")

        # Without "SO" prefix
        test_order_no_prefix = test_order.replace('SO', '').replace('so', '')
        print(f"   Checking without 'SO' prefix: '{test_order_no_prefix}'")
        cursor.execute("""
            SELECT TOP 5 co_num, item, qty_ordered
            FROM [CSISTG].[dbo].[coitem_mst]
            WHERE co_num = %s
            AND site_ref = 'BENN'
        """, (test_order_no_prefix,))

        no_prefix_matches = cursor.fetchall()
        if no_prefix_matches:
            print(f"   ✅ Found match without 'SO' prefix!")
            for row in no_prefix_matches:
                print(f"      Order: {row['co_num']}, Item: {row['item']}, Qty: {row['qty_ordered']}")
        else:
            print(f"   ❌ No match without prefix")

        # Check LIKE
        print(f"\n   Checking with LIKE '%{test_order_no_prefix}%'...")
        cursor.execute("""
            SELECT TOP 5 co_num, item, qty_ordered
            FROM [CSISTG].[dbo].[coitem_mst]
            WHERE co_num LIKE %s
            AND site_ref = 'BENN'
        """, (f'%{test_order_no_prefix}%',))

        like_matches = cursor.fetchall()
        if like_matches:
            print(f"   ✅ Found {len(like_matches)} matches with LIKE")
            for row in like_matches:
                print(f"      Order: {row['co_num']}, Item: {row['item']}, Qty: {row['qty_ordered']}")
        else:
            print(f"   ❌ No matches with LIKE")

    # Check what orders DO exist in SQL Server for boats
    print("\n   Checking what boat orders exist in SQL Server...")
    cursor.execute("""
        SELECT TOP 10 co_num, Uf_BENN_BoatModel, COUNT(*) as line_count
        FROM [CSISTG].[dbo].[coitem_mst]
        WHERE site_ref = 'BENN'
        AND Uf_BENN_BoatModel IS NOT NULL
        AND config_id IS NOT NULL
        GROUP BY co_num, Uf_BENN_BoatModel
        ORDER BY co_num DESC
    """)

    sql_orders = cursor.fetchall()
    if sql_orders:
        print(f"   ✅ Found {len(sql_orders)} recent boat orders in SQL Server:")
        print(f"\n   {'Order Number':<20} {'Model':<15} {'Line Items':<15}")
        print("   " + "-" * 50)
        for row in sql_orders:
            print(f"   {row['co_num']:<20} {row['Uf_BENN_BoatModel'] or 'NULL':<15} {row['line_count']:<15}")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("DIAGNOSIS COMPLETE")
print("=" * 80)
print("\nRECOMMENDATION:")
print("  Compare the order numbers above to identify the mismatch")
print("  The import query may need to adjust order number format")

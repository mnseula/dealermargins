#!/usr/bin/env python3
"""
Import Line Items with Pricing from SQL Server

Pulls actual line items (Item#, Description, Qty, Price) for boat orders
from SQL Server coitem_mst table to match configuration data.
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

# SQL Query to extract line items for orders we have in BoatConfigurationAttributes
SQL_QUERY = """
SELECT
    LEFT(coi.co_num, 30) AS ERP_OrderNo,
    LEFT(coi.Uf_BENN_BoatSerialNumber, 15) AS BoatSerialNo,
    LEFT(coi.Uf_BENN_BoatModel, 14) AS BoatModelNo,
    LEFT(coi.Uf_BENN_BoatWebOrderNumber, 30) AS WebOrderNo,
    LEFT(im.Uf_BENN_Series, 5) AS Series,

    -- Line item details
    coi.co_line AS LineNo,
    LEFT(coi.item, 30) AS ItemNo,
    LEFT(im.description, 255) AS ItemDescription,
    LEFT(im.product_code, 10) AS ItemMasterProdCat,

    -- Pricing
    coi.qty_ordered AS QuantityOrdered,
    coi.qty_invoiced AS QuantitySold,
    CAST(coi.price AS DECIMAL(10,2)) AS UnitPrice,
    CAST((coi.price * coi.qty_ordered) AS DECIMAL(10,2)) AS ExtendedPrice,

    -- Invoice info
    LEFT(iim.inv_num, 30) AS InvoiceNo,
    CASE
        WHEN ah.inv_date IS NOT NULL
        THEN CONVERT(INT, CONVERT(VARCHAR(8), ah.inv_date, 112))
        ELSE NULL
    END AS InvoiceDate

FROM [CSISTG].[dbo].[coitem_mst] coi

-- Join to get item details
LEFT JOIN [CSISTG].[dbo].[item_mst] im
    ON coi.item = im.item
    AND coi.site_ref = im.site_ref

-- Join to get invoice details
LEFT JOIN [CSISTG].[dbo].[inv_item_mst] iim
    ON coi.co_num = iim.co_num
    AND coi.co_line = iim.co_line
    AND coi.co_release = iim.co_release
    AND coi.site_ref = iim.site_ref

LEFT JOIN [CSISTG].[dbo].[arinv_mst] ah
    ON iim.inv_num = ah.inv_num
    AND iim.site_ref = ah.site_ref

WHERE
    coi.site_ref = 'BENN'
    AND coi.co_num IN (
        -- Only import orders that exist in our BoatConfigurationAttributes
        SELECT DISTINCT erp_order_no
        FROM OPENQUERY(
            [MYSQL_LINK],
            'SELECT DISTINCT erp_order_no FROM warrantyparts_test.BoatConfigurationAttributes WHERE erp_order_no IS NOT NULL'
        )
    )
    AND coi.item IS NOT NULL
    -- Filter for relevant item categories
    AND im.product_code IN ('ACC', 'BS1', 'L2', 'MTR', 'OA', 'PL', 'DC')

ORDER BY coi.co_num, coi.co_line
"""

# Simpler query without linked server (if above fails)
SQL_QUERY_SIMPLE = """
SELECT
    LEFT(coi.co_num, 30) AS ERP_OrderNo,
    LEFT(coi.Uf_BENN_BoatSerialNumber, 15) AS BoatSerialNo,
    LEFT(coi.Uf_BENN_BoatModel, 14) AS BoatModelNo,
    LEFT(coi.Uf_BENN_BoatWebOrderNumber, 30) AS WebOrderNo,
    LEFT(im.Uf_BENN_Series, 5) AS Series,

    -- Line item details
    coi.co_line AS LineNo,
    LEFT(coi.item, 30) AS ItemNo,
    LEFT(im.description, 255) AS ItemDescription,
    LEFT(im.product_code, 10) AS ItemMasterProdCat,

    -- Pricing
    coi.qty_ordered AS QuantityOrdered,
    coi.qty_invoiced AS QuantitySold,
    CAST(coi.price AS DECIMAL(10,2)) AS UnitPrice,
    CAST((coi.price * coi.qty_ordered) AS DECIMAL(10,2)) AS ExtendedPrice,

    -- Invoice info
    LEFT(iim.inv_num, 30) AS InvoiceNo,
    CASE
        WHEN ah.inv_date IS NOT NULL
        THEN CONVERT(INT, CONVERT(VARCHAR(8), ah.inv_date, 112))
        ELSE NULL
    END AS InvoiceDate

FROM [CSISTG].[dbo].[coitem_mst] coi

-- Join to get item details
LEFT JOIN [CSISTG].[dbo].[item_mst] im
    ON coi.item = im.item
    AND coi.site_ref = im.site_ref

-- Join to get invoice details
LEFT JOIN [CSISTG].[dbo].[inv_item_mst] iim
    ON coi.co_num = iim.co_num
    AND coi.co_line = iim.co_line
    AND coi.co_release = iim.co_release
    AND coi.site_ref = iim.site_ref

LEFT JOIN [CSISTG].[dbo].[arinv_mst] ah
    ON iim.inv_num = ah.inv_num
    AND iim.site_ref = ah.site_ref

WHERE
    coi.site_ref = 'BENN'
    AND coi.config_id IS NOT NULL
    AND coi.item IS NOT NULL
    -- Only orders from last 90 days to match configuration data timeframe
    AND coi.RecordDate >= DATEADD(day, -90, GETDATE())

ORDER BY coi.co_num, coi.co_line
"""

def main():
    print("=" * 80)
    print("LINE ITEMS IMPORT - WITH PRICING")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Step 1: Extract from SQL Server
    print("\n📊 STEP 1: Extracting line items from SQL Server...")
    line_items = extract_from_sql_server()

    if not line_items:
        print("❌ No data extracted from SQL Server. Import aborted.")
        return

    print(f"✅ Extracted {len(line_items):,} line item records")

    # Step 2: Load to MySQL (insert into BoatOptions25_test or new table)
    print("\n💾 STEP 2: Loading to MySQL...")
    load_to_mysql(line_items)

    # Step 3: Show summary
    print("\n📋 STEP 3: Import Summary")
    show_summary()

    print("\n" + "=" * 80)
    print("✅ IMPORT COMPLETE")
    print("=" * 80)
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def extract_from_sql_server():
    """Extract line items from SQL Server"""
    line_items = []

    try:
        print(f"   Connecting to {SQL_SERVER}...")
        conn = pymssql.connect(
            server=SQL_SERVER,
            database=SQL_DATABASE,
            user=SQL_USERNAME,
            password=SQL_PASSWORD,
            timeout=120,
            login_timeout=60
        )

        cursor = conn.cursor(as_dict=True)
        print("   ✅ Connected to SQL Server")

        print("   Executing query...")
        print("   (This may take a few minutes...)")

        # Try simple query first
        cursor.execute(SQL_QUERY_SIMPLE)

        print("   Fetching results...")
        line_items = cursor.fetchall()

        cursor.close()
        conn.close()

        return line_items

    except pymssql.Error as e:
        print(f"   ❌ SQL Server Error: {e}")
        return []
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return []

def load_to_mysql(line_items):
    """Load line items to MySQL BoatOptions25_test table"""

    try:
        print("   Connecting to MySQL...")
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        print("   ✅ Connected to MySQL")

        # Insert new data (don't truncate, add to existing)
        print(f"   Inserting {len(line_items):,} records...")

        insert_query = """
            INSERT INTO BoatOptions25_test
            (ERP_OrderNo, BoatSerialNo, BoatModelNo, WebOrderNo, Series,
             LineNo, ItemNo, ItemDesc1, ItemMasterProdCat,
             QuantitySold, ExtSalesAmount, InvoiceNo, InvoiceDate)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            QuantitySold = VALUES(QuantitySold),
            ExtSalesAmount = VALUES(ExtSalesAmount)
        """

        batch_size = 1000
        inserted = 0

        for i in range(0, len(line_items), batch_size):
            batch = line_items[i:i+batch_size]
            values = [
                (
                    item.get('ERP_OrderNo'),
                    item.get('BoatSerialNo'),
                    item.get('BoatModelNo'),
                    item.get('WebOrderNo'),
                    item.get('Series'),
                    item.get('LineNo'),
                    item.get('ItemNo'),
                    item.get('ItemDescription'),
                    item.get('ItemMasterProdCat'),
                    item.get('QuantitySold'),
                    item.get('ExtendedPrice'),
                    item.get('InvoiceNo'),
                    item.get('InvoiceDate')
                )
                for item in batch
            ]

            cursor.executemany(insert_query, values)
            conn.commit()
            inserted += len(batch)

            if inserted % 1000 == 0:
                print(f"      Inserted {inserted:,} records...")

        print(f"   ✅ Inserted {inserted:,} records")

        cursor.close()
        conn.close()

    except mysql.connector.Error as e:
        print(f"   ❌ MySQL Error: {e}")
        raise
    except Exception as e:
        print(f"   ❌ Error: {e}")
        raise

def show_summary():
    """Show summary statistics of imported data"""

    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()

        # Check for our specific order
        cursor.execute("""
            SELECT COUNT(*) FROM BoatOptions25_test
            WHERE ERP_OrderNo = 'SO00935977'
        """)
        count = cursor.fetchone()[0]

        if count > 0:
            print(f"\n   ✅ Order SO00935977: {count} line items")

            # Show accessory items with pricing
            cursor.execute("""
                SELECT ItemNo, ItemDesc1, QuantitySold, ExtSalesAmount
                FROM BoatOptions25_test
                WHERE ERP_OrderNo = 'SO00935977'
                  AND ItemMasterProdCat = 'ACC'
                LIMIT 5
            """)

            acc_items = cursor.fetchall()
            if acc_items:
                print(f"\n   Sample accessory items:")
                for item in acc_items:
                    price = f"${item[3]:,.2f}" if item[3] else "N/A"
                    print(f"      {item[0]}: {item[1]} - Qty: {item[2]} - Price: {price}")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"   ❌ Error showing summary: {e}")

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Import Boat Configuration Data from SQL Server to MySQL

STEP 1: Configuration Attributes
  - Performance Package, Console, Fuel, Colors, Trim, Furniture, etc.
  - From cfg_attr_mst table

STEP 2: Line Items with Pricing
  - Item#, Description, Quantity, Unit Price, Extended Price
  - From coitem_mst table
  - Provides pricing data for window sticker

This is the ONLY script you need to run - imports everything!
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

# SQL Query to extract configuration attributes
SQL_QUERY = """
SELECT
    LEFT(coi.Uf_BENN_BoatSerialNumber, 15) AS BoatSerialNo,
    LEFT(coi.Uf_BENN_BoatModel, 14) AS BoatModelNo,
    LEFT(coi.co_num, 30) AS ERP_OrderNo,
    LEFT(coi.Uf_BENN_BoatWebOrderNumber, 30) AS WebOrderNo,
    LEFT(coi.config_id, 50) AS ConfigID,

    -- Attribute details
    LEFT(attr.attr_name, 100) AS AttrName,
    LEFT(attr.attr_value, 255) AS AttrValue,
    LEFT(attr.Uf_BENN_Cfg_Value, 255) AS CfgValue,
    LEFT(attr.comp_id, 50) AS CompID,

    -- Boat metadata
    LEFT(im.Uf_BENN_Series, 5) AS Series,
    LEFT(iim.inv_num, 30) AS InvoiceNo,
    CASE
        WHEN ah.inv_date IS NOT NULL
        THEN CONVERT(INT, CONVERT(VARCHAR(8), ah.inv_date, 112))
        ELSE NULL
    END AS InvoiceDate

FROM [CSISTG].[dbo].[coitem_mst] coi

-- Join to configuration attributes table
INNER JOIN [CSISTG].[dbo].[cfg_attr_mst] attr
    ON coi.config_id = attr.config_id
    AND coi.site_ref = attr.site_ref

-- Join to get boat/item details
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
    coi.config_id IS NOT NULL
    AND coi.site_ref = 'BENN'
    AND attr.attr_name IS NOT NULL
    -- Focus on key configuration attributes
    AND attr.attr_name IN (
        'Performance Package',
        'Fuel',
        'Console',
        'Canvas Color',
        'Captain''s Chairs',
        'Co-Captain''s Chairs',
        'Trim Accents',
        'BASE VINYL',
        'FLOORING',
        'FURNITURE UPGRADE',
        'Tables - Bow',
        'Tables - Aft',
        'Rockford Fosgate Stereo',
        'Main Display',
        'Additional Display',
        'Exterior Color Packages',
        'Bimini Cable Stays',
        'Aft Bimini Tops',
        'Bow Bimini Tops',
        'Arch',
        'Steering Wheels',
        'Lifting Strakes',
        'Saltwater Package'
    )

ORDER BY
    coi.co_num,
    attr.attr_name
"""

# This will be built dynamically with order numbers from BoatConfigurationAttributes
LINE_ITEMS_QUERY_TEMPLATE = """
SELECT
    LEFT(coi.co_num, 30) AS ERP_OrderNo,
    LEFT(coi.Uf_BENN_BoatSerialNumber, 15) AS BoatSerialNo,
    LEFT(coi.Uf_BENN_BoatModel, 14) AS BoatModelNo,
    LEFT(coi.Uf_BENN_BoatWebOrderNumber, 30) AS WebOrderNo,
    LEFT(im.Uf_BENN_Series, 5) AS Series,
    coi.co_line AS Line_Number,
    LEFT(coi.item, 30) AS ItemNo,
    LEFT(im.description, 255) AS ItemDescription,
    LEFT(im.product_code, 10) AS ItemMasterProdCat,
    coi.qty_ordered AS QuantityOrdered,
    coi.qty_invoiced AS QuantitySold,
    CAST(coi.price AS DECIMAL(10,2)) AS UnitPrice,
    CAST((coi.price * coi.qty_ordered) AS DECIMAL(10,2)) AS ExtendedPrice,
    LEFT(iim.inv_num, 30) AS InvoiceNo,
    CASE
        WHEN ah.inv_date IS NOT NULL
        THEN CONVERT(INT, CONVERT(VARCHAR(8), ah.inv_date, 112))
        ELSE NULL
    END AS InvoiceDate

FROM [CSISTG].[dbo].[coitem_mst] coi

LEFT JOIN [CSISTG].[dbo].[item_mst] im
    ON coi.item = im.item
    AND coi.site_ref = im.site_ref

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
    AND coi.item IS NOT NULL
    AND im.product_code IN ('ACC', 'BS1', 'L2', 'MTR', 'OA', 'PL', 'DC')
    AND coi.co_num IN ({order_list})

ORDER BY coi.co_num, coi.co_line
"""

def main():
    print("=" * 80)
    print("BOAT CONFIGURATION & LINE ITEMS IMPORT")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Step 1: Configuration Attributes
    print("\n📊 STEP 1: Extracting Configuration Attributes from SQL Server...")
    attributes = extract_configuration_attributes()

    if not attributes:
        print("❌ No configuration attributes extracted. Import aborted.")
        return

    print(f"✅ Extracted {len(attributes):,} configuration attribute records")

    print("\n💾 STEP 2: Loading Configuration Attributes to MySQL...")
    load_configuration_attributes(attributes)

    # Step 3: Line Items with Pricing
    print("\n📦 STEP 3: Extracting Line Items with Pricing from SQL Server...")
    line_items = extract_line_items()

    if not line_items:
        print("⚠️ No line items extracted (this may be normal if no recent orders)")
    else:
        print(f"✅ Extracted {len(line_items):,} line item records")

        print("\n💾 STEP 4: Loading Line Items to MySQL...")
        load_line_items(line_items)

    # Step 5: Show summary
    print("\n📋 STEP 5: Import Summary")
    show_summary()

    print("\n" + "=" * 80)
    print("✅ IMPORT COMPLETE - ALL DATA LOADED")
    print("=" * 80)
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def extract_configuration_attributes():
    """Extract configuration attributes from SQL Server"""
    attributes = []

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

        print("   Executing query...")
        cursor.execute(SQL_QUERY)

        print("   Fetching results...")
        attributes = cursor.fetchall()

        cursor.close()
        conn.close()

        return attributes

    except pymssql.Error as e:
        print(f"   ❌ SQL Server Error: {e}")
        return []
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return []

def load_configuration_attributes(attributes):
    """Load attributes to MySQL BoatConfigurationAttributes table"""

    try:
        print("   Connecting to MySQL...")
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        print("   ✅ Connected to MySQL")

        # Truncate existing data
        print("   Truncating existing data...")
        cursor.execute("TRUNCATE TABLE BoatConfigurationAttributes")
        print("   ✅ Table truncated")

        # Insert new data
        print(f"   Inserting {len(attributes):,} records...")

        insert_query = """
            INSERT INTO BoatConfigurationAttributes
            (boat_serial_no, boat_model_no, erp_order_no, web_order_no, config_id,
             attr_name, attr_value, cfg_value, comp_id, series, invoice_no, invoice_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        batch_size = 1000
        inserted = 0

        for i in range(0, len(attributes), batch_size):
            batch = attributes[i:i+batch_size]
            values = [
                (
                    attr.get('BoatSerialNo'),
                    attr.get('BoatModelNo'),
                    attr.get('ERP_OrderNo'),
                    attr.get('WebOrderNo'),
                    attr.get('ConfigID'),
                    attr.get('AttrName'),
                    attr.get('AttrValue'),
                    attr.get('CfgValue'),
                    attr.get('CompID'),
                    attr.get('Series'),
                    attr.get('InvoiceNo'),
                    attr.get('InvoiceDate')
                )
                for attr in batch
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

def extract_line_items():
    """Extract line items with pricing from SQL Server"""
    line_items = []

    try:
        # First, get the list of order numbers from MySQL
        print("   Getting order list from BoatConfigurationAttributes...")
        mysql_conn = mysql.connector.connect(**MYSQL_CONFIG)
        mysql_cursor = mysql_conn.cursor()

        mysql_cursor.execute("""
            SELECT DISTINCT erp_order_no
            FROM BoatConfigurationAttributes
            WHERE erp_order_no IS NOT NULL
            AND erp_order_no != ''
        """)

        order_numbers = [row[0] for row in mysql_cursor.fetchall()]
        mysql_cursor.close()
        mysql_conn.close()

        if not order_numbers:
            print("   ⚠️ No order numbers found in BoatConfigurationAttributes")
            return []

        print(f"   Found {len(order_numbers)} orders to query")

        # Build the IN clause with quoted order numbers
        order_list = ','.join([f"'{order}'" for order in order_numbers])

        # Build the final query
        line_items_query = LINE_ITEMS_QUERY_TEMPLATE.format(order_list=order_list)

        # Connect to SQL Server
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
        cursor.execute(line_items_query)

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

def load_line_items(line_items):
    """Load line items to MySQL BoatOptions25_test table"""

    try:
        print("   Connecting to MySQL...")
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        print("   ✅ Connected to MySQL")

        # Insert new data (add to existing, don't truncate)
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
                    item.get('Line_Number'),
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

        # Total records
        cursor.execute("SELECT COUNT(*) FROM BoatConfigurationAttributes")
        total = cursor.fetchone()[0]
        print(f"\n   Total records: {total:,}")

        # By attribute name
        print("\n   Records by Attribute:")
        cursor.execute("""
            SELECT attr_name, COUNT(*) as count
            FROM BoatConfigurationAttributes
            GROUP BY attr_name
            ORDER BY count DESC
        """)

        for row in cursor.fetchall():
            print(f"      {row[0]:<40} {row[1]:>6,} records")

        # Performance Package count
        cursor.execute("""
            SELECT COUNT(*) FROM BoatConfigurationAttributes
            WHERE attr_name = 'Performance Package'
        """)
        perf_count = cursor.fetchone()[0]
        print(f"\n   ✨ Performance Package records: {perf_count:,}")

        # Sample performance packages
        if perf_count > 0:
            print("\n   Sample Performance Packages:")
            cursor.execute("""
                SELECT DISTINCT attr_value, COUNT(*) as count
                FROM BoatConfigurationAttributes
                WHERE attr_name = 'Performance Package'
                  AND attr_value IS NOT NULL
                GROUP BY attr_value
                ORDER BY count DESC
                LIMIT 10
            """)

            for row in cursor.fetchall():
                print(f"      {row[0]:<40} {row[1]:>6,} boats")

        # Line Items Summary
        print("\n" + "=" * 80)
        print("LINE ITEMS SUMMARY")
        print("=" * 80)

        cursor.execute("SELECT COUNT(*) FROM BoatOptions25_test WHERE ERP_OrderNo IS NOT NULL")
        line_item_count = cursor.fetchone()[0]
        print(f"\n   Total line items: {line_item_count:,}")

        if line_item_count > 0:
            # Count by product category
            print("\n   Line Items by Category:")
            cursor.execute("""
                SELECT ItemMasterProdCat, COUNT(*) as count
                FROM BoatOptions25_test
                WHERE ERP_OrderNo IS NOT NULL
                GROUP BY ItemMasterProdCat
                ORDER BY count DESC
            """)

            for row in cursor.fetchall():
                cat = row[0] if row[0] else 'NULL'
                print(f"      {cat:<15} {row[1]:>6,} items")

            # Check for specific order
            cursor.execute("""
                SELECT COUNT(*) FROM BoatOptions25_test
                WHERE ERP_OrderNo = 'SO00935977'
            """)
            test_order_count = cursor.fetchone()[0]

            if test_order_count > 0:
                print(f"\n   ✅ Order SO00935977: {test_order_count} line items")

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
                    print("\n   Sample accessory items with pricing:")
                    for item in acc_items:
                        item_no = item[0] if item[0] else 'N/A'
                        desc = item[1][:40] if item[1] else 'N/A'
                        qty = item[2] if item[2] else 0
                        price = item[3] if item[3] else 0
                        print(f"      {item_no:<15} {desc:<40} Qty: {qty:>3.0f}  Price: ${price:>10,.2f}")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"   ❌ Error showing summary: {e}")

if __name__ == '__main__':
    main()

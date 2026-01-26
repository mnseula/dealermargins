#!/usr/bin/env python3
"""
Import Boat Configuration Attributes from SQL Server to MySQL

Pulls configuration data from SQL Server cfg_attr_mst table including:
- Performance Package
- Console, Fuel, Colors, Trim, Furniture, etc.

Uses the Uf_BENN_Cfg_Value field to get actual configuration values.
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

def main():
    print("=" * 80)
    print("BOAT CONFIGURATION ATTRIBUTES IMPORT")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Step 1: Extract from SQL Server
    print("\n📊 STEP 1: Extracting from SQL Server...")
    attributes = extract_from_sql_server()

    if not attributes:
        print("❌ No data extracted from SQL Server. Import aborted.")
        return

    print(f"✅ Extracted {len(attributes):,} configuration attribute records")

    # Step 2: Load to MySQL
    print("\n💾 STEP 2: Loading to MySQL...")
    load_to_mysql(attributes)

    # Step 3: Show summary
    print("\n📋 STEP 3: Import Summary")
    show_summary()

    print("\n" + "=" * 80)
    print("✅ IMPORT COMPLETE")
    print("=" * 80)
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def extract_from_sql_server():
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

def load_to_mysql(attributes):
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

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"   ❌ Error showing summary: {e}")

if __name__ == '__main__':
    main()

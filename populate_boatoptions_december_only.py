#!/usr/bin/env python3
"""
Populate MySQL BoatOptions25 table - DECEMBER ONLY (for proof of concept)
Extracts physical items (excludes configuration items) from December sales orders
"""
import pymssql
import pymysql
from datetime import datetime

# MSSQL Configuration
MSSQL_CONFIG = {
    'server': 'MPL1STGSQL086.POLARISSTAGE.COM',
    'database': 'CSISTG',
    'user': 'svccsimarine',
    'password': 'CNKmoFxEsXs0D9egZQXH'
}

# MySQL Configuration
MYSQL_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts',
    'charset': 'utf8mb4'
}

# December filter - change these as needed
DECEMBER_YEAR = 2024
DECEMBER_MONTH = 12

def main():
    print("="*120)
    print(f"POPULATING BOATOPTIONS25 FROM MSSQL - DECEMBER {DECEMBER_YEAR} ONLY")
    print("="*120)
    print(f"Started: {datetime.now()}\n")

    try:
        # Connect to MSSQL
        print("Connecting to MSSQL...")
        mssql_conn = pymssql.connect(**MSSQL_CONFIG)
        mssql_cursor = mssql_conn.cursor()
        print("✅ Connected to MSSQL\n")

        # Connect to MySQL
        print("Connecting to MySQL...")
        mysql_conn = pymysql.connect(**MYSQL_CONFIG)
        mysql_cursor = mysql_conn.cursor()
        print("✅ Connected to MySQL\n")

        # First, count how many orders/items we'll process
        print("="*120)
        print(f"CHECKING DECEMBER {DECEMBER_YEAR} DATA...")
        print("="*120)

        mssql_cursor.execute(f"""
            SELECT
                COUNT(DISTINCT ser.ref_num) as order_count,
                COUNT(*) as total_items
            FROM CSISTG.dbo.serial_mst ser
            JOIN CSISTG.dbo.coitem_mst coi
                ON ser.ref_num = coi.co_num
                AND ser.site_ref = coi.site_ref
            WHERE ser.site_ref = 'BENN'
              AND ser.ref_num LIKE 'SO%'
              AND YEAR(ser.RecordDate) = {DECEMBER_YEAR}
              AND MONTH(ser.RecordDate) = {DECEMBER_MONTH}
        """)

        stats = mssql_cursor.fetchone()
        print(f"\nDecember {DECEMBER_YEAR} Orders: {stats[0]:,}")
        print(f"Total Line Items (before filtering): {stats[1]:,}\n")

        # Extract data from MSSQL
        print("="*120)
        print(f"EXTRACTING DECEMBER {DECEMBER_YEAR} DATA FROM MSSQL...")
        print("="*120)

        query = f"""
        SELECT
            ser.ser_num AS BoatSerialNo,
            coi.item AS ItemNo,
            itm.description AS ItemDesc1,
            pc.description AS MCTDesc,
            itm.product_code AS ItemMasterMCT,
            itm.Uf_BENN_ProductCategory AS ItemMasterProdCat,
            coi.price * coi.qty_ordered AS ExtSalesAmount,
            coi.qty_ordered AS QuantitySold,
            coi.co_line AS LineNo,
            coi.co_num AS OrderNumber,
            ser.item AS BoatModelNo
        FROM CSISTG.dbo.serial_mst ser
        JOIN CSISTG.dbo.coitem_mst coi
            ON ser.ref_num = coi.co_num
            AND ser.site_ref = coi.site_ref
        JOIN CSISTG.dbo.item_mst itm
            ON coi.item = itm.item
            AND coi.site_ref = itm.site_ref
        LEFT JOIN CSISTG.dbo.prodcode_mst pc
            ON itm.product_code = pc.product_code
            AND itm.site_ref = pc.site_ref
        WHERE ser.site_ref = 'BENN'
          AND ser.ref_num LIKE 'SO%'
          -- DECEMBER FILTER
          AND YEAR(ser.RecordDate) = {DECEMBER_YEAR}
          AND MONTH(ser.RecordDate) = {DECEMBER_MONTH}
          -- EXCLUDE CONFIG ITEMS
          AND itm.Uf_BENN_ProductCategory <> '111'
          AND itm.product_code NOT IN (
            'DIC','DIF','DIP','DIR','DIA','DIW',
            'LOY','PRD','VOD','DIS','CAS',
            'SHO','GRO','ZZZ','WAR','DLR',
            'FRE','FRP','FRT',
            'A0','A0C','A0G','A0I','A0P','A0T','A0V','A1','A6','FUR',
            'TAX','INT','LAB','MKT','ADV','DLM',
            'DMG','DSP','OTD','OTI','PGA','MKA','MIG','DON','REW','SNAP'
          )
          AND itm.Uf_BENN_ProductCategory NOT LIKE 'C%'
          AND itm.Uf_BENN_ProductCategory NOT LIKE 'DI%'
          AND itm.Uf_BENN_ProductCategory NOT LIKE 'W%'
          AND itm.Uf_BENN_ProductCategory NOT LIKE 'N%'
          AND itm.Uf_BENN_ProductCategory NOT LIKE 'PA%'
          AND itm.Uf_BENN_ProductCategory NOT LIKE 'X%'
          AND itm.Uf_BENN_ProductCategory NOT IN ('GRO','LAB','TAX','SHO','INT','PGA','VOI','S1','S3','S4','S5')
          AND NOT (itm.product_code = 'DIS' AND coi.item <> 'NPPNPRICE16S')
          AND NOT (itm.product_code = 'ENZ' AND itm.description NOT LIKE '%VALUE%')
          AND NOT (
            itm.Uf_BENN_ProductCategory IN ('H1','H1I','H1P','H1V','H3U','H5','L0','S2','ASY')
            AND COALESCE(coi.price * coi.qty_ordered, 0) = 0
          )
          AND NOT (
            itm.product_code = 'ACY'
            AND COALESCE(coi.price * coi.qty_ordered, 0) = 0
          )
        ORDER BY ser.ser_num, coi.co_line
        """

        mssql_cursor.execute(query)
        rows = mssql_cursor.fetchall()

        print(f"✅ Extracted {len(rows):,} rows from MSSQL (after filtering)\n")

        if len(rows) == 0:
            print("⚠️  No data to insert. Exiting.")
            return

        # Show sample data
        print("Sample data (first 5 rows):")
        print(f"{'Serial':<20} {'Item':<20} {'MCT':<8} {'Category':<10} {'Amount':<12} {'Description':<40}")
        print("-"*120)
        for i, row in enumerate(rows[:5]):
            serial = (row[0] or '')[:20]
            item = (row[1] or '')[:20]
            mct = row[4] or ''
            cat = row[5] or ''
            amt = f"${row[6]:,.2f}" if row[6] else '$0.00'
            desc = (row[2] or '')[:40]
            print(f"{serial:<20} {item:<20} {mct:<8} {cat:<10} {amt:<12} {desc:<40}")

        # Clear existing data
        print("\n" + "="*120)
        print("CLEARING EXISTING DATA FROM MYSQL BOATOPTIONS25...")
        print("="*120)
        mysql_cursor.execute("DELETE FROM BoatOptions25")
        deleted_count = mysql_cursor.rowcount
        print(f"✅ Deleted {deleted_count:,} existing rows\n")

        # Insert data into MySQL
        print("="*120)
        print("INSERTING DATA INTO MYSQL BOATOPTIONS25...")
        print("="*120)

        insert_query = """
        INSERT INTO BoatOptions25 (
            BoatSerialNo,
            ItemNo,
            ItemDesc1,
            MCTDesc,
            ItemMasterMCT,
            ItemMasterProdCat,
            ExtSalesAmount,
            QuantitySold,
            LineNo,
            OrderNumber,
            BoatModelNo
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        # Insert in batches of 1000 for performance
        batch_size = 1000
        total_inserted = 0

        for i in range(0, len(rows), batch_size):
            batch = rows[i:i+batch_size]
            mysql_cursor.executemany(insert_query, batch)
            total_inserted += len(batch)
            print(f"  Inserted {total_inserted:,} / {len(rows):,} rows ({total_inserted*100//len(rows)}%)")

        mysql_conn.commit()
        print(f"\n✅ Successfully inserted {total_inserted:,} rows into MySQL\n")

        # Verify the data
        print("="*120)
        print("VERIFYING DATA IN MYSQL...")
        print("="*120)
        mysql_cursor.execute("SELECT COUNT(*) FROM BoatOptions25")
        count = mysql_cursor.fetchone()[0]
        print(f"Total rows in BoatOptions25: {count:,}\n")

        # Show sample boats
        mysql_cursor.execute("""
            SELECT
                BoatSerialNo,
                COUNT(*) as item_count,
                SUM(ExtSalesAmount) as total_amount
            FROM BoatOptions25
            GROUP BY BoatSerialNo
            ORDER BY BoatSerialNo DESC
            LIMIT 10
        """)

        print(f"Sample boats from December {DECEMBER_YEAR}:")
        print(f"{'Serial Number':<20} {'Item Count':<15} {'Total Amount':<15}")
        print("-"*50)
        for row in mysql_cursor.fetchall():
            serial = row[0] or ''
            count = row[1] or 0
            amount = row[2] or 0
            print(f"{serial:<20} {count:<15,} ${amount:<14,.2f}")

        # Close connections
        mssql_cursor.close()
        mssql_conn.close()
        mysql_cursor.close()
        mysql_conn.close()

        print("\n" + "="*120)
        print(f"DECEMBER {DECEMBER_YEAR} MIGRATION COMPLETE")
        print("="*120)
        print(f"Finished: {datetime.now()}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

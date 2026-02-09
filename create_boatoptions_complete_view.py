#!/usr/bin/env python3
"""
Create BoatOptions26_Complete VIEW that includes ALL columns.
This VIEW will be used by loadByListName to get complete data including MSRP.
"""
import mysql.connector

db_config = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts'
}

conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

print("Creating BoatOptions26_Complete VIEW with all columns including MSRP...")

# Create a view that explicitly selects ALL columns including MSRP
create_view_sql = """
CREATE OR REPLACE VIEW BoatOptions26_Complete AS
SELECT
    BoatSerialNo,
    BoatModelNo,
    Series,
    ERP_OrderNo,
    Orig_Ord_Type,
    InvoiceNo,
    ApplyToNo,
    WebOrderNo,
    InvoiceDate,
    LineNo,
    LineSeqNo,
    MCTDesc,
    ItemNo,
    ItemDesc1,
    OptionSerialNo,
    ItemMasterMCT,
    ItemMasterProdCat,
    ItemMasterProdCatDesc,
    QuantitySold,
    ExtSalesAmount,
    MSRP,
    CfgName,
    CfgPage,
    CfgScreen,
    CfgValue,
    CfgAttrType,
    order_date,
    external_confirmation_ref,
    ConfigID,
    ValueText,
    C_Series
FROM BoatOptions26
"""

cursor.execute(create_view_sql)
print("✅ BoatOptions26_Complete VIEW created successfully")

# Test the view
print("\nTesting view with ETWTEST26...")
cursor.execute("""
    SELECT ItemDesc1, ExtSalesAmount, MSRP, CfgName
    FROM BoatOptions26_Complete
    WHERE BoatSerialNo = 'ETWTEST26'
    AND MSRP IS NOT NULL AND MSRP > 0
    LIMIT 5
""")

results = cursor.fetchall()
if results:
    print(f"✅ Found {len(results)} items with MSRP:")
    for row in results:
        print(f"  {row[0]:30s} DealerCost: ${row[1]:>10,.2f}  MSRP: ${row[2]:>10,.2f}  CfgName: {row[3]}")
else:
    print("❌ No results found")

cursor.close()
conn.close()

print("\n" + "=" * 80)
print("NEXT STEP: Update packagePricing.js to use 'BoatOptions26_Complete' instead of 'BoatOptions26'")
print("=" * 80)

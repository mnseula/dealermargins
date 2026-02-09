#!/usr/bin/env python3
"""
Try creating the VIEW in the Eos database, pointing to warrantyparts.BoatOptions26.
EOS's loadByListName might look for views in the Eos database.
"""
import mysql.connector

db_config_eos = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'Eos'
}

conn = mysql.connector.connect(**db_config_eos)
cursor = conn.cursor()

print("Creating BoatOptions26_Complete VIEW in Eos database...")
print("(pointing to warrantyparts.BoatOptions26)")

# Create VIEW in Eos that references warrantyparts table
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
FROM warrantyparts.BoatOptions26
"""

cursor.execute(create_view_sql)
print("✅ VIEW created in Eos database")

# Test it
print("\nTesting VIEW from Eos database...")
cursor.execute("""
    SELECT ItemDesc1, ExtSalesAmount, MSRP
    FROM BoatOptions26_Complete
    WHERE BoatSerialNo = 'ETWTEST26'
    AND MSRP IS NOT NULL AND MSRP > 0
    LIMIT 3
""")

results = cursor.fetchall()
if results:
    print(f"✅ Works! Found {len(results)} items:")
    for row in results:
        print(f"  {row[0]:30s} Dealer: ${row[1]:>8,.2f}  MSRP: ${row[2]:>8,.2f}")
else:
    print("❌ No results")

cursor.close()
conn.close()

print("\n" + "=" * 80)
print("VIEW now exists in Eos database - try testing again")
print("=" * 80)

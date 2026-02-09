#!/usr/bin/env python3
"""
Export MSRP data to a JavaScript file that can be loaded by packagePricing.js.
This works around loadByListName not returning MSRP column.
"""
import mysql.connector
import json

db_config = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts'
}

conn = mysql.connector.connect(**db_config)
cursor = conn.cursor(dictionary=True)

print("Exporting MSRP data from BoatOptions26...")

# Get all items with MSRP data from all boats in 2026
query = """
    SELECT
        BoatSerialNo,
        InvoiceNo,
        LineNo,
        LineSeqNo,
        ItemNo,
        ItemDesc1,
        ExtSalesAmount,
        MSRP,
        CfgName
    FROM BoatOptions26
    WHERE MSRP IS NOT NULL AND MSRP > 0
    ORDER BY BoatSerialNo, InvoiceNo, LineNo, LineSeqNo
"""

cursor.execute(query)
rows = cursor.fetchall()

print(f"Found {len(rows)} items with MSRP data")

# Convert to JavaScript array format (easier to search than map)
msrp_array = []
for row in rows:
    msrp_array.append({
        'serial': row['BoatSerialNo'],
        'invoice': row['InvoiceNo'],
        'lineNo': row['LineNo'],
        'lineSeqNo': row['LineSeqNo'],
        'itemNo': row['ItemNo'],
        'itemDesc': row['ItemDesc1'],
        'msrp': float(row['MSRP']),
        'dealerCost': float(row['ExtSalesAmount']),
        'cfgName': row['CfgName']
    })

# Write to JavaScript file
js_content = f"""// MSRP Data Export - Generated automatically
// This file contains MSRP mappings for CPQ boats ({len(msrp_array)} items)
// DO NOT EDIT MANUALLY - regenerate with export_msrp_data.py

window.MSRP_DATA = {json.dumps(msrp_array, indent=2)};

console.log('Loaded MSRP data for ' + window.MSRP_DATA.length + ' CPQ items');
"""

output_file = '/Users/michaelnseula/code/dealermargins/msrp_data.js'
with open(output_file, 'w') as f:
    f.write(js_content)

print(f"✅ Wrote {len(msrp_array)} MSRP records to {output_file}")
print(f"\nSample entries:")
for item in msrp_array[:5]:
    print(f"  {item['serial']:15s} {item['itemDesc']:30s} MSRP=${item['msrp']:>10,.2f}  Dealer=${item['dealerCost']:>10,.2f}")

cursor.close()
conn.close()

print("\n" + "=" * 80)
print("NEXT STEP: Include msrp_data.js in the HTML page and reference it in packagePricing.js")
print("=" * 80)

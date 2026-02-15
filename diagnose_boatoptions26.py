#!/usr/bin/env python3
"""
Diagnostic script for BoatOptions26 loading issue
Helps identify why ETWS0837A626 won't load via loadByListName
"""
import mysql.connector

DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts'
}

def diagnose_boat():
    """Diagnose why boat won't load via loadByListName"""
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        serial = 'ETWS0837A626'

        print("\n" + "="*80)
        print(f"DIAGNOSTIC REPORT FOR {serial}")
        print("="*80 + "\n")

        # Step 1: Get SerialNumberMaster data (like JavaScript does)
        print("STEP 1: SerialNumberMaster lookup")
        print("-" * 80)
        cursor.execute("""
            SELECT Boat_SerialNo, InvoiceNo, DealerNumber, DealerName
            FROM SerialNumberMaster
            WHERE Boat_SerialNo = %s
        """, (serial,))

        snm = cursor.fetchone()
        if snm:
            print(f"✅ Found in SerialNumberMaster:")
            print(f"   Invoice: {snm['InvoiceNo']}")
            print(f"   Dealer: {snm['DealerName']} (#{snm['DealerNumber']})")
            invoice_no = snm['InvoiceNo']
        else:
            print(f"❌ NOT found in SerialNumberMaster - STOPPING")
            return

        # Step 2: Check what's in BoatOptions26 for this serial
        print("\n" + "="*80)
        print("STEP 2: BoatOptions26 - Raw data check")
        print("-" * 80)

        cursor.execute("""
            SELECT COUNT(*) as total
            FROM BoatOptions26
            WHERE BoatSerialNo = %s
        """, (serial,))
        total = cursor.fetchone()['total']
        print(f"Total records for {serial}: {total}")

        if total == 0:
            print(f"❌ NO RECORDS in BoatOptions26 for this serial")
            return

        # Step 3: Check records by ItemMasterMCT
        print("\n" + "="*80)
        print("STEP 3: BoatOptions26 - Records by MCT type")
        print("-" * 80)

        cursor.execute("""
            SELECT ItemMasterMCT, COUNT(*) as count
            FROM BoatOptions26
            WHERE BoatSerialNo = %s
            GROUP BY ItemMasterMCT
            ORDER BY count DESC
        """, (serial,))

        mcts = cursor.fetchall()
        for mct in mcts:
            print(f"   {mct['ItemMasterMCT']}: {mct['count']} records")

        # Step 4: Test the EXACT query JavaScript uses (InvoiceNo filter)
        print("\n" + "="*80)
        print("STEP 4: Test JavaScript query (InvoiceNo filter)")
        print("-" * 80)

        # This is the exact WHERE clause from packagePricing.js line 37
        js_query = """
            SELECT *
            FROM BoatOptions26
            WHERE ItemMasterMCT <> 'DIC'
              AND ItemMasterMCT <> 'DIF'
              AND ItemMasterMCT <> 'DIP'
              AND ItemMasterMCT <> 'DIR'
              AND ItemMasterMCT <> 'DIA'
              AND ItemMasterMCT <> 'DIW'
              AND ItemMasterMCT <> 'LOY'
              AND ItemMasterMCT <> 'PRD'
              AND ItemMasterMCT <> 'VOD'
              AND (ItemMasterMCT <> 'DIS' OR (ItemMasterMCT = 'DIS' AND ItemNo = 'NPPNPRICE16S'))
              AND ItemMasterMCT <> 'DIV'
              AND ItemMasterMCT <> 'CAS'
              AND ItemMasterMCT <> 'DIW'
              AND (ItemMasterMCT <> 'ENZ' OR (ItemMasterMCT = 'ENZ' AND ItemDesc1 LIKE '%VALUE%'))
              AND ItemMasterMCT <> 'SHO'
              AND ItemMasterMCT <> 'GRO'
              AND ItemMasterMCT <> 'ZZZ'
              AND ItemMasterMCT <> 'FRE'
              AND ItemMasterMCT <> 'WAR'
              AND ItemMasterMCT <> 'DLR'
              AND ItemMasterMCT <> 'FRT'
              AND ItemMasterProdCat <> '111'
              AND InvoiceNo = %s
              AND BoatSerialNo = %s
            ORDER BY CASE MCTDesc
                WHEN 'PONTOONS' THEN 1
                WHEN 'Pontoon Boats OB' THEN 1
                WHEN 'Pontoon Boats IO' THEN 1
                WHEN 'Lower Unit Eng' THEN 2
                WHEN 'ENGINES' THEN 3
                WHEN 'Engine' THEN 3
                WHEN 'Engine IO' THEN 3
                WHEN 'PRE-RIG' THEN 4
                WHEN 'Prerig' THEN 4
                ELSE 5
            END, LineNo ASC
        """

        cursor.execute(js_query, (invoice_no, serial))
        results = cursor.fetchall()

        print(f"\nQuery returned {len(results)} records")

        if len(results) == 0:
            print("❌ PROBLEM: JavaScript query returns 0 records!")
            print("\nLet's check why...")

            # Test without InvoiceNo filter
            print("\n" + "-" * 80)
            print("Test without InvoiceNo filter:")
            cursor.execute(js_query.replace("AND InvoiceNo = %s", ""), (serial,))
            without_invoice = cursor.fetchall()
            print(f"   Without InvoiceNo filter: {len(without_invoice)} records")

            # Check what InvoiceNo values exist
            cursor.execute("""
                SELECT DISTINCT InvoiceNo, COUNT(*) as count
                FROM BoatOptions26
                WHERE BoatSerialNo = %s
                GROUP BY InvoiceNo
            """, (serial,))
            invoices = cursor.fetchall()
            print(f"\n   InvoiceNo values in BoatOptions26:")
            for inv in invoices:
                match = "✅ MATCH" if inv['InvoiceNo'] == invoice_no else "❌ NO MATCH"
                print(f"      {inv['InvoiceNo']} ({inv['count']} records) {match}")

            print(f"\n   Expected InvoiceNo from SerialNumberMaster: {invoice_no}")

        else:
            print(f"✅ Query successful - {len(results)} records")

            # Check for BOA/BOI records (boat model)
            boa_boi = [r for r in results if r['ItemMasterMCT'] in ('BOA', 'BOI')]
            print(f"\n   Records with ItemMasterMCT = BOA or BOI: {len(boa_boi)}")

            if len(boa_boi) > 0:
                print(f"   ✅ Boat model record found:")
                boat = boa_boi[0]
                print(f"      Model: {boat['BoatModelNo']}")
                print(f"      Description: {boat['ItemDesc1']}")
                print(f"      MSRP: ${boat['MSRP']}")
                print(f"      Dealer Cost: ${boat['ExtSalesAmount']}")
            else:
                print(f"   ❌ NO boat model record (BOA/BOI) found!")

        # Step 5: Check if table might not be configured as EOS list
        print("\n" + "="*80)
        print("STEP 5: EOS List Configuration Check")
        print("-" * 80)
        print("NOTE: loadByListName requires table to be configured as an EOS 'list'")
        print("      This is NOT a database table issue - it's an EOS configuration issue")
        print("\nPossible issues:")
        print("   1. BoatOptions26 not registered in EOS as a queryable list")
        print("   2. Permissions issue preventing EOS from reading BoatOptions26")
        print("   3. EOS cache not updated after table creation")

        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"\n✅ Boat exists in SerialNumberMaster: {serial}")
        print(f"✅ Boat has {total} records in BoatOptions26")
        print(f"✅ Invoice number: {invoice_no}")

        if len(results) > 0:
            print(f"✅ JavaScript query would return {len(results)} records")
            print(f"\n🔍 If loadByListName still returns 0, the issue is:")
            print(f"   → BoatOptions26 not properly configured as an EOS list")
        else:
            print(f"❌ JavaScript query returns 0 records")
            print(f"\n🔍 Issue appears to be:")
            print(f"   → InvoiceNo mismatch between SerialNumberMaster and BoatOptions26")

        cursor.close()
        connection.close()

    except mysql.connector.Error as e:
        print(f"❌ Database error: {e}")
        if connection and connection.is_connected():
            connection.close()

if __name__ == "__main__":
    diagnose_boat()

#!/usr/bin/env python3
"""
Extract Color/Configuration Fields from MSSQL for CPQTEST26

This script queries MSSQL to get the color and configuration fields
that need to be populated in SerialNumberMaster:
- ProdNo (from co_mst.Uf_BENN_ProductionNumber)
- BenningtonOwned (from co_mst.Uf_BENN_BenningtonOwned)
- PanelColor (from coitem_mst.Uf_BENN_PannelColor for BOA line)
- AccentPanel (from coitem_mst or cfg_attr_mst)
- BaseVinyl (from coitem_mst.Uf_BENN_BaseVnyl for BOA line)
- ColorPackage (from coitem_mst or cfg_attr_mst)
- TrimAccent (from coitem_mst or cfg_attr_mst)

Usage:
    python3 extract_color_fields_cpqtest26.py
"""

import pymssql

# MSSQL Configuration
MSSQL_CONFIG = {
    'server': 'MPL1STGSQL086.POLARISSTAGE.COM',
    'database': 'CSISTG',
    'user': 'svccsimarine',
    'password': 'CNKmoFxEsXs0D9egZQXH',
    'timeout': 300,
    'login_timeout': 60
}

def extract_color_fields(co_num: str):
    """Extract all color and configuration fields from MSSQL"""
    
    # Query 1: Get order-level fields from co_mst and BOA line from coitem_mst
    query1 = """
    SELECT 
        -- Order-level fields
        co.co_num,
        co.Uf_BENN_ProductionNumber AS ProdNo,
        co.Uf_BENN_BenningtonOwned AS BenningtonOwned,
        
        -- Boat line (BOA) fields
        coi.co_line,
        coi.item AS BoatItem,
        coi.Uf_BENN_PannelColor AS PanelColor,
        coi.Uf_BENN_BaseVnyl AS BaseVinyl,
        coi.config_id
        
    FROM [CSISTG].[dbo].[co_mst] co
    LEFT JOIN [CSISTG].[dbo].[coitem_mst] coi 
        ON co.co_num = coi.co_num 
        AND co.site_ref = coi.site_ref
    LEFT JOIN [CSISTG].[dbo].[item_mst] im 
        ON coi.item = im.item 
        AND coi.site_ref = im.site_ref
    WHERE co.co_num = %s
        AND co.site_ref = 'BENN'
        AND (im.Uf_BENN_MaterialCostType = 'BOA' OR coi.config_id IS NOT NULL)
    ORDER BY coi.co_line
    """
    
    # Query 2: Get configuration attributes that might have color info
    query2 = """
    SELECT 
        coi.co_num,
        coi.config_id,
        attr.attr_name,
        attr.attr_value,
        attr.Uf_BENN_Cfg_Name,
        attr.Uf_BENN_Cfg_Value
    FROM [CSISTG].[dbo].[coitem_mst] coi
    INNER JOIN [CSISTG].[dbo].[cfg_attr_mst] attr
        ON coi.config_id = attr.config_id
        AND coi.site_ref = attr.site_ref
    WHERE coi.co_num = %s
        AND coi.site_ref = 'BENN'
        AND coi.config_id IS NOT NULL
        AND (
            attr.attr_name LIKE '%Color%' 
            OR attr.attr_name LIKE '%Panel%'
            OR attr.attr_name LIKE '%Accent%'
            OR attr.attr_name LIKE '%Trim%'
            OR attr.attr_name LIKE '%Vinyl%'
            OR attr.attr_name LIKE '%Package%'
        )
        AND attr.attr_value IS NOT NULL
        AND attr.attr_value != ''
    ORDER BY attr.attr_name
    """
    
    # Query 3: Get all user fields from coitem_mst for the boat line
    query3 = """
    SELECT 
        coi.co_line,
        coi.item,
        coi.Uf_BENN_PannelColor,
        coi.Uf_BENN_BaseVnyl,
        coi.Uf_BENN_AccentPannel,
        coi.Uf_BENN_ColorPackage,
        coi.Uf_BENN_TrimAccent,
        coi.Uf_BENN_BoatSerialNumber
    FROM [CSISTG].[dbo].[coitem_mst] coi
    LEFT JOIN [CSISTG].[dbo].[item_mst] im 
        ON coi.item = im.item 
        AND coi.site_ref = im.site_ref
    WHERE coi.co_num = %s
        AND coi.site_ref = 'BENN'
        AND im.Uf_BENN_MaterialCostType = 'BOA'
    """
    
    try:
        conn = pymssql.connect(**MSSQL_CONFIG)
        cursor = conn.cursor(as_dict=True)
        
        print("=" * 80)
        print(f"EXTRACTING COLOR FIELDS FOR ORDER: {co_num}")
        print("=" * 80)
        
        # Execute Query 1: Order and BOA line info
        print("\n1. ORDER-LEVEL AND BOAT LINE FIELDS:")
        print("-" * 80)
        cursor.execute(query1, (co_num,))
        results1 = cursor.fetchall()
        
        if results1:
            for row in results1:
                print(f"CO Number: {row['co_num']}")
                print(f"ProdNo (Uf_BENN_ProductionNumber): {row['ProdNo']}")
                print(f"BenningtonOwned: {row['BenningtonOwned']}")
                print(f"CO Line: {row['co_line']}")
                print(f"Boat Item: {row['BoatItem']}")
                print(f"PanelColor (Uf_BENN_PannelColor): {row['PanelColor']}")
                print(f"BaseVinyl (Uf_BENN_BaseVnyl): {row['BaseVinyl']}")
                print(f"ConfigID: {row['config_id']}")
        else:
            print("No BOA line found")
        
        # Execute Query 2: Configuration attributes
        print("\n2. CONFIGURATION ATTRIBUTES (Color-related):")
        print("-" * 80)
        cursor.execute(query2, (co_num,))
        results2 = cursor.fetchall()
        
        if results2:
            for row in results2:
                print(f"  {row['attr_name']}: {row['attr_value']}")
                if row['Uf_BENN_Cfg_Name']:
                    print(f"    Cfg_Name: {row['Uf_BENN_Cfg_Name']}")
                if row['Uf_BENN_Cfg_Value']:
                    print(f"    Cfg_Value: {row['Uf_BENN_Cfg_Value']}")
        else:
            print("  No color-related config attributes found")
        
        # Execute Query 3: All user fields from coitem_mst
        print("\n3. ALL COITEM USER FIELDS FOR BOAT LINE:")
        print("-" * 80)
        cursor.execute(query3, (co_num,))
        results3 = cursor.fetchall()
        
        if results3:
            for row in results3:
                print(f"  CO Line: {row['co_line']}")
                print(f"  Item: {row['item']}")
                print(f"  Uf_BENN_PannelColor: {row['Uf_BENN_PannelColor']}")
                print(f"  Uf_BENN_BaseVnyl: {row['Uf_BENN_BaseVnyl']}")
                print(f"  Uf_BENN_AccentPannel: {row['Uf_BENN_AccentPannel']}")
                print(f"  Uf_BENN_ColorPackage: {row['Uf_BENN_ColorPackage']}")
                print(f"  Uf_BENN_TrimAccent: {row['Uf_BENN_TrimAccent']}")
                print(f"  Uf_BENN_BoatSerialNumber: {row['Uf_BENN_BoatSerialNumber']}")
        else:
            print("  No BOA line found")
        
        cursor.close()
        conn.close()
        
        return {
            'order_fields': results1,
            'config_attrs': results2,
            'coitem_fields': results3
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    co_num = 'SO00936093'  # CPQTEST26 order
    
    results = extract_color_fields(co_num)
    
    if results:
        print("\n" + "=" * 80)
        print("SUMMARY - UPDATE SQL FOR SERIALNUMBERMASTER:")
        print("=" * 80)
        print("\nRun this SQL in MySQL to update CPQTEST26:")
        print("-" * 80)
        
        # Build UPDATE statement based on what we found
        print("\n-- Query the data first to see what values you have:")
        print("SELECT *")
        print("FROM [CSISTG].[dbo].[coitem_mst]")
        print("WHERE co_num = 'SO00936093'")
        print("  AND site_ref = 'BENN'")
        print("  AND config_id IS NOT NULL;")
        print("\n-- Then update SerialNumberMaster with the values:")
        print("UPDATE SerialNumberMaster")
        print("SET")
        print("    ProdNo = <value from Uf_BENN_ProductionNumber>,")
        print("    BenningtonOwned = <value from Uf_BENN_BenningtonOwned>,")
        print("    PanelColor = <value from Uf_BENN_PannelColor>,")
        print("    AccentPanel = <value from config attr or Uf_BENN_AccentPannel>,")
        print("    BaseVinyl = <value from Uf_BENN_BaseVnyl>,")
        print("    ColorPackage = <value from config attr or Uf_BENN_ColorPackage>,")
        print("    TrimAccent = <value from config attr or Uf_BENN_TrimAccent>")
        print("WHERE Boat_SerialNo = 'CPQTEST26';")

if __name__ == '__main__':
    main()

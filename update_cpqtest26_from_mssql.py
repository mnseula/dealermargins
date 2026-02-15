#!/usr/bin/env python3
"""
Update CPQTEST26 SerialNumberMaster fields from MSSQL

Populates the following fields from MSSQL CSI/ERP:
- ProdNo: CO_MST.uf_BENN_ProductionOrderNumber
- BenningtonOwned: CO_MST.Uf_BENN_BenningtonOwned
- PanelColor: coitem_mst.Uf_BENN_PannelColor
- AccentPanel: coitem_mst.Uf_BENN_AccentPanel (assumed field name)
- BaseVinyl: coitem_mst.Uf_BENN_BaseVnyl
- ColorPackage: coitem_mst.Uf_BENN_ColorPackage (assumed field name)
- TrimAccent: coitem_mst.Uf_BENN_TrimAccent (assumed field name)

Usage:
    python3 update_cpqtest26_from_mssql.py
"""

import pymssql
import mysql.connector
from mysql.connector import Error as MySQLError

# MSSQL Configuration
MSSQL_CONFIG = {
    'server': 'MPL1STGSQL086.POLARISSTAGE.COM',
    'database': 'CSISTG',
    'user': 'svccsimarine',
    'password': 'CNKmoFxEsXs0D9egZQXH',
    'timeout': 300,
    'login_timeout': 60
}

# MySQL Configuration
MYSQL_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'port': 3306,
    'database': 'warrantyparts',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD'
}

def get_mssql_data(co_num: str) -> dict:
    """Query MSSQL for the fields we need"""
    query = """
    SELECT 
        -- From co_mst
        co.uf_BENN_ProductionOrderNumber AS ProdNo,
        co.Uf_BENN_BenningtonOwned AS BenningtonOwned,
        
        -- From coitem_mst (boat line - MCT = 'BOA')
        MAX(CASE WHEN im.Uf_BENN_MaterialCostType = 'BOA' THEN coi.Uf_BENN_PannelColor END) AS PanelColor,
        MAX(CASE WHEN im.Uf_BENN_MaterialCostType = 'BOA' THEN coi.Uf_BENN_AccentPannel END) AS AccentPanel,
        MAX(CASE WHEN im.Uf_BENN_MaterialCostType = 'BOA' THEN coi.Uf_BENN_BaseVnyl END) AS BaseVinyl,
        MAX(CASE WHEN im.Uf_BENN_MaterialCostType = 'BOA' THEN coi.Uf_BENN_ColorPackage END) AS ColorPackage,
        MAX(CASE WHEN im.Uf_BENN_MaterialCostType = 'BOA' THEN coi.Uf_BENN_TrimAccent END) AS TrimAccent
        
    FROM [CSISTG].[dbo].[co_mst] co
    LEFT JOIN [CSISTG].[dbo].[coitem_mst] coi 
        ON co.co_num = coi.co_num 
        AND co.site_ref = coi.site_ref
    LEFT JOIN [CSISTG].[dbo].[item_mst] im 
        ON coi.item = im.item 
        AND coi.site_ref = im.site_ref
    WHERE co.co_num = %s
        AND co.site_ref = 'BENN'
    GROUP BY 
        co.uf_BENN_ProductionOrderNumber,
        co.Uf_BENN_BenningtonOwned
    """
    
    try:
        conn = pymssql.connect(**MSSQL_CONFIG)
        cursor = conn.cursor(as_dict=True)
        cursor.execute(query, (co_num,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        print(f"❌ MSSQL Error: {e}")
        return None

def update_mysql(hull_number: str, data: dict) -> bool:
    """Update SerialNumberMaster in MySQL"""
    update_query = """
        UPDATE SerialNumberMaster 
        SET 
            ProdNo = %s,
            BenningtonOwned = %s,
            PanelColor = %s,
            AccentPanel = %s,
            BaseVinyl = %s,
            ColorPackage = %s,
            TrimAccent = %s
        WHERE Boat_SerialNo = %s
    """
    
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute(update_query, (
            data.get('ProdNo'),
            data.get('BenningtonOwned'),
            data.get('PanelColor'),
            data.get('AccentPanel'),
            data.get('BaseVinyl'),
            data.get('ColorPackage'),
            data.get('TrimAccent'),
            hull_number
        ))
        
        conn.commit()
        rows_affected = cursor.rowcount
        cursor.close()
        conn.close()
        
        return rows_affected > 0
    except MySQLError as e:
        print(f"❌ MySQL Error: {e}")
        return False

def main():
    hull_number = 'CPQTEST26'
    co_num = 'SO00936093'
    
    print("=" * 80)
    print("UPDATE CPQTEST26 FROM MSSQL")
    print("=" * 80)
    print(f"Hull Number: {hull_number}")
    print(f"CO Number: {co_num}")
    print()
    
    # Step 1: Get data from MSSQL
    print("1. Querying MSSQL for field values...")
    mssql_data = get_mssql_data(co_num)
    
    if not mssql_data:
        print("❌ Failed to retrieve data from MSSQL")
        return
    
    print("✅ Retrieved data from MSSQL:")
    print()
    for key, value in mssql_data.items():
        print(f"   {key:20s}: {value}")
    print()
    
    # Step 2: Update MySQL
    print("2. Updating SerialNumberMaster in MySQL...")
    success = update_mysql(hull_number, mssql_data)
    
    if success:
        print("✅ Successfully updated SerialNumberMaster")
        print()
        print("Updated fields:")
        print(f"   ProdNo: {mssql_data.get('ProdNo')}")
        print(f"   BenningtonOwned: {mssql_data.get('BenningtonOwned')}")
        print(f"   PanelColor: {mssql_data.get('PanelColor')}")
        print(f"   AccentPanel: {mssql_data.get('AccentPanel')}")
        print(f"   BaseVinyl: {mssql_data.get('BaseVinyl')}")
        print(f"   ColorPackage: {mssql_data.get('ColorPackage')}")
        print(f"   TrimAccent: {mssql_data.get('TrimAccent')}")
    else:
        print("❌ Failed to update SerialNumberMaster")
    
    print()
    print("=" * 80)

if __name__ == '__main__':
    main()

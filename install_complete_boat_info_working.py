#!/usr/bin/env python3
"""
Install and test GetCompleteBoatInformation stored procedure
Simplified pricing calculations to avoid SQL syntax errors
"""

import mysql.connector
from mysql.connector import Error
import sys

# Database configuration
DB_CONFIG = {
    'host': 'ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    'user': 'awsmaster',
    'password': 'VWvHG9vfG23g7gD',
    'database': 'warrantyparts_test'
}

PROCEDURE_SQL = "DROP PROCEDURE IF EXISTS GetCompleteBoatInformation;"

PROCEDURE_CREATE = """
CREATE PROCEDURE GetCompleteBoatInformation(
    IN p_hull_no VARCHAR(50),
    IN p_msrp_margin DECIMAL(5,4),
    IN p_msrp_volume DECIMAL(5,4)
)
BEGIN
    DECLARE v_dealer_id VARCHAR(50);
    DECLARE v_series_id VARCHAR(10);
    DECLARE v_model_no VARCHAR(50);
    DECLARE v_web_order_no VARCHAR(50);
    DECLARE v_model_year INT;
    DECLARE v_table_name VARCHAR(50);
    
    -- Margin variables
    DECLARE v_base_margin DECIMAL(5,2);
    DECLARE v_engine_margin DECIMAL(5,2);
    DECLARE v_options_margin DECIMAL(5,2);
    DECLARE v_freight_margin DECIMAL(5,2);
    DECLARE v_prep_margin DECIMAL(5,2);
    
    -- Set defaults
    SET p_msrp_margin = COALESCE(p_msrp_margin, 0.75);
    SET p_msrp_volume = COALESCE(p_msrp_volume, 1.00);
    
    -- Get boat info
    SELECT 
        DealerNumber,
        Series,
        BoatItemNo,
        WebOrderNo,
        CASE 
            WHEN SerialModelYear REGEXP '^[0-9]+$' THEN CAST(SerialModelYear AS UNSIGNED)
            ELSE NULL
        END
    INTO v_dealer_id, v_series_id, v_model_no, v_web_order_no, v_model_year
    FROM SerialNumberMaster
    WHERE Boat_SerialNo = p_hull_no
    LIMIT 1;
    
    -- Series mapping
    IF v_series_id = 'Q' THEN
        SET v_series_id = 'QX';
    END IF;
    
    -- Convert year
    IF v_model_year >= 20 AND v_model_year <= 99 THEN
        SET v_model_year = 2000 + v_model_year;
    END IF;
    
    -- Determine table name
    IF v_model_year >= 2024 AND v_model_year <= 2025 THEN
        SET v_table_name = 'BoatOptions24_6252025';
    ELSEIF v_model_year = 2025 THEN
        SET v_table_name = 'BoatOptions25_test';
    ELSEIF v_model_year = 2026 THEN
        SET v_table_name = 'BoatOptions26_test';
    ELSEIF v_model_year = 2016 THEN
        SET v_table_name = 'BoatOptions16';
    ELSEIF v_model_year = 2015 THEN
        SET v_table_name = 'BoatOptions15';
    ELSEIF v_model_year >= 2011 AND v_model_year <= 2014 THEN
        SET v_table_name = 'BoatOptions11_14';
    ELSEIF v_model_year >= 2008 AND v_model_year <= 2010 THEN
        SET v_table_name = 'BoatOptions08_10';
    ELSEIF v_model_year >= 2005 AND v_model_year <= 2007 THEN
        SET v_table_name = 'BoatOptions05_07';
    ELSEIF v_model_year >= 1999 AND v_model_year <= 2004 THEN
        SET v_table_name = 'BoatOptions99_04';
    ELSE
        SET v_table_name = 'BoatOptions25_test';
    END IF;
    
    -- Get margins
    SELECT 
        COALESCE(base_boat_margin, 27.0),
        COALESCE(engine_margin, 27.0),
        COALESCE(options_margin, 27.0),
        COALESCE(freight_margin, 27.0),
        COALESCE(prep_margin, 27.0)
    INTO 
        v_base_margin,
        v_engine_margin,
        v_options_margin,
        v_freight_margin,
        v_prep_margin
    FROM DealerMargins
    WHERE dealer_id = v_dealer_id
      AND series_id = v_series_id
      AND enabled = 1
      AND effective_date <= CURDATE()
      AND (end_date IS NULL OR end_date >= CURDATE())
    ORDER BY effective_date DESC
    LIMIT 1;
    
    -- Defaults if not found
    SET v_base_margin = COALESCE(v_base_margin, 27.0);
    SET v_engine_margin = COALESCE(v_engine_margin, 27.0);
    SET v_options_margin = COALESCE(v_options_margin, 27.0);
    SET v_freight_margin = COALESCE(v_freight_margin, 27.0);
    SET v_prep_margin = COALESCE(v_prep_margin, 27.0);
    
    -- Result Set 1: Header
    SELECT 
        s.Boat_SerialNo as hull_no,
        s.BoatItemNo as model_no,
        s.WebOrderNo as web_order_no,
        s.DealerNumber as dealer_id,
        s.DealerName as dealer_name,
        s.Series as series_raw,
        v_series_id as series_id,
        v_model_year as model_year,
        v_table_name as options_table,
        NOW() as generated_at
    FROM SerialNumberMaster s
    WHERE s.Boat_SerialNo = p_hull_no;
    
    -- Result Set 2: Line Items
    SET @sql = CONCAT('
        SELECT 
            ItemNo,
            ItemDesc1,
            ItemMasterProdCat,
            QuantitySold,
            ExtSalesAmount as dealer_cost,
            CASE ItemMasterProdCat
                WHEN ''BOAT'' THEN ', v_base_margin, '
                WHEN ''ENG'' THEN ', v_engine_margin, '
                WHEN ''ACC'' THEN ', v_options_margin, '
                WHEN ''FRT'' THEN ', v_freight_margin, '
                WHEN ''PREP'' THEN ', v_prep_margin, '
                ELSE 27.0
            END as margin_pct,
            ROUND(ExtSalesAmount / (1 - (CASE ItemMasterProdCat
                WHEN ''BOAT'' THEN ', v_base_margin, '
                WHEN ''ENG'' THEN ', v_engine_margin, '
                WHEN ''ACC'' THEN ', v_options_margin, '
                WHEN ''FRT'' THEN ', v_freight_margin, '
                WHEN ''PREP'' THEN ', v_prep_margin, '
                ELSE 27.0
            END / 100)), 2) as sale_price,
            ROUND((ExtSalesAmount * ', p_msrp_volume, ') / ', p_msrp_margin, ', 2) as msrp
        FROM ', v_table_name, '
        WHERE WebOrderNo = ''', v_web_order_no, '''
        ORDER BY FIELD(ItemMasterProdCat, ''BOAT'', ''ENG'', ''ACC'', ''FRT'', ''PREP''), ItemNo
    ');
    
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
    
    -- Result Set 3: Summary by Category
    SET @sql = CONCAT('
        SELECT 
            ItemMasterProdCat,
            COUNT(*) as item_count,
            SUM(QuantitySold) as total_quantity,
            ROUND(SUM(ExtSalesAmount), 2) as total_dealer_cost,
            CASE ItemMasterProdCat
                WHEN ''BOAT'' THEN ', v_base_margin, '
                WHEN ''ENG'' THEN ', v_engine_margin, '
                WHEN ''ACC'' THEN ', v_options_margin, '
                WHEN ''FRT'' THEN ', v_freight_margin, '
                WHEN ''PREP'' THEN ', v_prep_margin, '
                ELSE 27.0
            END as margin_pct,
            ROUND(SUM(ExtSalesAmount / (1 - (CASE ItemMasterProdCat
                WHEN ''BOAT'' THEN ', v_base_margin, '
                WHEN ''ENG'' THEN ', v_engine_margin, '
                WHEN ''ACC'' THEN ', v_options_margin, '
                WHEN ''FRT'' THEN ', v_freight_margin, '
                WHEN ''PREP'' THEN ', v_prep_margin, '
                ELSE 27.0
            END / 100))), 2) as total_sale_price,
            ROUND(SUM((ExtSalesAmount * ', p_msrp_volume, ') / ', p_msrp_margin, '), 2) as total_msrp
        FROM ', v_table_name, '
        WHERE WebOrderNo = ''', v_web_order_no, '''
        GROUP BY ItemMasterProdCat
        ORDER BY FIELD(ItemMasterProdCat, ''BOAT'', ''ENG'', ''ACC'', ''FRT'', ''PREP'')
    ');
    
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
    
    -- Result Set 4: Margins
    SELECT 
        v_dealer_id as dealer_id,
        v_series_id as series_id,
        v_base_margin as base_boat_margin,
        v_engine_margin as engine_margin,
        v_options_margin as options_margin,
        v_freight_margin as freight_margin,
        v_prep_margin as prep_margin,
        p_msrp_margin as msrp_margin,
        p_msrp_volume as msrp_volume;
    
    -- Result Set 5: Grand Totals
    SET @sql = CONCAT('
        SELECT 
            COUNT(*) as total_line_items,
            SUM(QuantitySold) as total_quantity,
            ROUND(SUM(ExtSalesAmount), 2) as grand_total_dealer_cost,
            ROUND(SUM(ExtSalesAmount / (1 - (CASE ItemMasterProdCat
                WHEN ''BOAT'' THEN ', v_base_margin, '
                WHEN ''ENG'' THEN ', v_engine_margin, '
                WHEN ''ACC'' THEN ', v_options_margin, '
                WHEN ''FRT'' THEN ', v_freight_margin, '
                WHEN ''PREP'' THEN ', v_prep_margin, '
                ELSE 27.0
            END / 100))), 2) as grand_total_sale_price,
            ROUND(SUM((ExtSalesAmount * ', p_msrp_volume, ') / ', p_msrp_margin, '), 2) as grand_total_msrp,
            ROUND(SUM(ExtSalesAmount / (1 - (CASE ItemMasterProdCat
                WHEN ''BOAT'' THEN ', v_base_margin, '
                WHEN ''ENG'' THEN ', v_engine_margin, '
                WHEN ''ACC'' THEN ', v_options_margin, '
                WHEN ''FRT'' THEN ', v_freight_margin, '
                WHEN ''PREP'' THEN ', v_prep_margin, '
                ELSE 27.0
            END / 100))) - SUM(ExtSalesAmount), 2) as total_margin_dollars
        FROM ', v_table_name, '
        WHERE WebOrderNo = ''', v_web_order_no, '''
    ');
    
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
    
END;
"""

def install_procedure(cursor):
    """Install the stored procedure"""
    print("Dropping existing procedure...")
    cursor.execute(PROCEDURE_SQL)
    
    print("Creating GetCompleteBoatInformation procedure...")
    cursor.execute(PROCEDURE_CREATE)
    print("Procedure created successfully!")

def find_test_hull(cursor):
    """Find a valid hull number with WebOrderNo"""
    cursor.execute("""
        SELECT Boat_SerialNo, BoatItemNo, Series, SerialModelYear, WebOrderNo, DealerNumber, DealerName 
        FROM SerialNumberMaster 
        WHERE Boat_SerialNo IS NOT NULL 
        AND Boat_SerialNo != ''
        AND WebOrderNo IS NOT NULL
        AND WebOrderNo != ''
        AND Series IS NOT NULL
        LIMIT 10
    """)
    
    print("\nAvailable test hulls:")
    hulls = []
    for row in cursor.fetchall():
        hulls.append(row[0])
        print(f"  Hull: {row[0]}, Model: {row[1]}, Series: {row[2]}, Year: {row[3]}, WebOrder: {row[4]}, Dealer: {row[5]}")
    
    return hulls[0] if hulls else None

def test_procedure(cursor, hull_no):
    """Test the procedure with a sample hull number"""
    print(f"\nTesting with hull number: {hull_no}")
    print("=" * 100)
    
    try:
        cursor.callproc('GetCompleteBoatInformation', [hull_no, 0.75, 1.00])
        
        # Fetch all result sets
        result_sets = []
        for result in cursor.stored_results():
            result_sets.append(result.fetchall())
        
        # Display results
        print("\n--- Result Set 1: Boat Header ---")
        if result_sets and result_sets[0]:
            row = result_sets[0][0]
            print(f"Hull: {row[0]}")
            print(f"Model: {row[1]}")
            print(f"WebOrder: {row[2]}")
            print(f"Dealer: {row[3]} - {row[4]}")
            print(f"Series: {row[5]} -> {row[6]}")
            print(f"Year: {row[7]}")
            print(f"Table: {row[8]}")
        
        print("\n--- Result Set 2: Line Items ---")
        if len(result_sets) > 1 and result_sets[1]:
            print(f"{'Item':<15} {'Description':<30} {'Cat':<5} {'Qty':<4} {'Dealer Cost':>12} {'Margin%':>7} {'Sale Price':>12} {'MSRP':>12}")
            print("-" * 100)
            for row in result_sets[1][:10]:
                print(f"{str(row[0]):<15} {str(row[1])[:30]:<30} {str(row[2]):<5} {row[3]:<4} ${row[4]:>10,.2f} {row[5]:>6.1f}% ${row[6]:>10,.2f} ${row[7]:>10,.2f}")
            if len(result_sets[1]) > 10:
                print(f"... and {len(result_sets[1]) - 10} more items")
        else:
            print("No line items found")
        
        print("\n--- Result Set 3: Summary by Category ---")
        if len(result_sets) > 2 and result_sets[2]:
            print(f"{'Category':<10} {'Items':>6} {'Qty':>4} {'Dealer Cost':>13} {'Margin%':>7} {'Sale Price':>13} {'MSRP':>13}")
            print("-" * 75)
            for row in result_sets[2]:
                print(f"{row[0]:<10} {row[1]:>6} {row[2]:>4} ${row[3]:>11,.2f} {row[4]:>6.1f}% ${row[5]:>11,.2f} ${row[6]:>11,.2f}")
        
        print("\n--- Result Set 4: Dealer Margins ---")
        if len(result_sets) > 3 and result_sets[3]:
            row = result_sets[3][0]
            print(f"Dealer: {row[0]}, Series: {row[1]}")
            print(f"Base: {row[2]}%, Engine: {row[3]}%, Options: {row[4]}%, Freight: {row[5]}%, Prep: {row[6]}%")
            print(f"MSRP: margin={row[7]}, volume={row[8]}")
        
        print("\n--- Result Set 5: Grand Totals ---")
        if len(result_sets) > 4 and result_sets[4]:
            row = result_sets[4][0]
            if row[0]:
                print(f"Line Items: {row[0]}, Quantity: {row[1]}")
                print(f"Dealer Cost: ${row[2]:,.2f}")
                print(f"Sale Price:  ${row[3]:,.2f}")
                print(f"MSRP:        ${row[4]:,.2f}")
                print(f"Margin $:    ${row[5]:,.2f}")
                if row[2] > 0:
                    print(f"Margin %:    {(row[5]/row[2]*100):.2f}%")
        
        print("\n" + "=" * 100)
        print("SUCCESS!")
        
    except Error as e:
        print(f"Test failed: {e}")
        raise

def main():
    """Main execution"""
    connection = None
    try:
        print("Connecting to database...")
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        install_procedure(cursor)
        connection.commit()
        
        hull_no = sys.argv[1] if len(sys.argv) > 1 else find_test_hull(cursor)
        if not hull_no:
            print("No valid test hulls found!")
            sys.exit(1)
        
        test_procedure(cursor, hull_no)
        
        cursor.close()
        print("\nProcedure installed and tested successfully!")
        print(f"\nUsage: CALL GetCompleteBoatInformation('{hull_no}', 0.75, 1.00);")
        
    except Error as e:
        print(f"Error: {e}", file=sys.stderr)
        if connection:
            connection.rollback()
        sys.exit(1)
        
    finally:
        if connection and connection.is_connected():
            connection.close()
            print("\nDatabase connection closed.")

if __name__ == '__main__':
    main()

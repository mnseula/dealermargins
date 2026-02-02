#!/usr/bin/env python3
"""
Install and test GetCompleteBoatInformation stored procedure
Works with hull numbers from SerialNumberMaster and model data from BoatOptions tables

IMPORTANT: The BoatOptions tables store data by WebOrderNo, not by hull number.
The BoatModelNo column contains the boat model code (e.g., "2350RSFBDF"), not hull.
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

# Stored procedure SQL
PROCEDURE_SQL = """
DROP PROCEDURE IF EXISTS GetCompleteBoatInformation;
"""

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
    DECLARE v_table_suffix VARCHAR(2);
    DECLARE v_table_name VARCHAR(50);
    
    -- Margin variables
    DECLARE v_base_margin DECIMAL(5,2);
    DECLARE v_engine_margin DECIMAL(5,2);
    DECLARE v_options_margin DECIMAL(5,2);
    DECLARE v_freight_margin DECIMAL(5,2);
    DECLARE v_prep_margin DECIMAL(5,2);
    
    -- Set defaults for optional parameters
    SET p_msrp_margin = COALESCE(p_msrp_margin, 0.75);
    SET p_msrp_volume = COALESCE(p_msrp_volume, 1.00);
    
    -- Get boat header info from SerialNumberMaster
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
    
    -- Handle series mapping (Q maps to QX for margins)
    IF v_series_id = 'Q' THEN
        SET v_series_id = 'QX';
    END IF;
    
    -- Convert 2-digit year to 4-digit if needed
    IF v_model_year >= 20 AND v_model_year <= 99 THEN
        SET v_model_year = 2000 + v_model_year;
    END IF;
    
    -- Get table suffix - handle consolidated tables
    IF v_model_year >= 2024 AND v_model_year <= 2025 THEN
        SET v_table_name = 'BoatOptions24_6252025';
    ELSEIF v_model_year = 2025 THEN
        SET v_table_name = 'BoatOptions25_test';
    ELSEIF v_model_year = 2026 THEN
        SET v_table_name = 'BoatOptions26_test';
    ELSEIF v_model_year >= 2015 AND v_model_year <= 2016 THEN
        SET v_table_suffix = LPAD(v_model_year - 2000, 2, '0');
        SET v_table_name = CONCAT('BoatOptions', v_table_suffix);
    ELSEIF v_model_year >= 2011 AND v_model_year <= 2014 THEN
        SET v_table_name = 'BoatOptions11_14';
    ELSEIF v_model_year >= 2008 AND v_model_year <= 2010 THEN
        SET v_table_name = 'BoatOptions08_10';
    ELSEIF v_model_year >= 2005 AND v_model_year <= 2007 THEN
        SET v_table_name = 'BoatOptions05_07';
    ELSEIF v_model_year >= 1999 AND v_model_year <= 2004 THEN
        SET v_table_name = 'BoatOptions99_04';
    ELSE
        SET v_table_name = 'BoatOptions25_test';  -- fallback
    END IF;
    
    -- Get dealer margins using correct column names
    SELECT 
        COALESCE(base_boat_margin, 0),
        COALESCE(engine_margin, 0),
        COALESCE(options_margin, 0),
        COALESCE(freight_margin, 0),
        COALESCE(prep_margin, 0)
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
    
    -- Set defaults if no margins found
    SET v_base_margin = COALESCE(v_base_margin, 27.0);
    SET v_engine_margin = COALESCE(v_engine_margin, 27.0);
    SET v_options_margin = COALESCE(v_options_margin, 27.0);
    SET v_freight_margin = COALESCE(v_freight_margin, 27.0);
    SET v_prep_margin = COALESCE(v_prep_margin, 27.0);
    
    -- Result Set 1: Boat Header
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
    
    -- Result Set 2: Line Items with Pricing (Dynamic Query by WebOrderNo)
    SET @sql = CONCAT('
        SELECT 
            ItemNo as item_no,
            ItemDesc1 as item_description,
            ItemMasterProdCat as product_category,
            QuantitySold as quantity,
            ExtSalesAmount as dealer_cost,
            CASE ItemMasterProdCat
                WHEN ''BOAT'' THEN ', v_base_margin, '
                WHEN ''ENG'' THEN ', v_engine_margin, '
                WHEN ''ACC'' THEN ', v_options_margin, '
                WHEN ''FRT'' THEN ', v_freight_margin, '
                WHEN ''PREP'' THEN ', v_prep_margin, '
                ELSE 27.0
            END as margin_pct,
            ROUND(
                (ExtSalesAmount * 1.00) / (1 - (CASE ItemMasterProdCat
                    WHEN ''BOAT'' THEN ', v_base_margin, '
                    WHEN ''ENG'' THEN ', v_engine_margin, '
                    WHEN ''ACC'' THEN ', v_options_margin, '
                    WHEN ''FRT'' THEN ', v_freight_margin, '
                    WHEN ''PREP'' THEN ', v_prep_margin, '
                    ELSE 27.0
                END / 100)),
                2
            ) as sale_price,
            ROUND(
                (ExtSalesAmount * ', p_msrp_volume, ') / ', p_msrp_margin, ',
                2
            ) as msrp
        FROM ', v_table_name, '
        WHERE WebOrderNo = ''', v_web_order_no, '''
        ORDER BY 
            FIELD(ItemMasterProdCat, ''BOAT'', ''ENG'', ''ACC'', ''FRT'', ''PREP''),
            ItemNo
    ');
    
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
    
    -- Result Set 3: Pricing Summary by Category
    SET @sql = CONCAT('
        SELECT 
            ItemMasterProdCat as category,
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
            ROUND(
                SUM(
                    (ExtSalesAmount * 1.00) / (1 - (CASE ItemMasterProdCat
                        WHEN ''BOAT'' THEN ', v_base_margin, '
                        WHEN ''ENG'' THEN ', v_engine_margin, '
                        WHEN ''ACC'' THEN ', v_options_margin, '
                        WHEN ''FRT'' THEN ', v_freight_margin, '
                        WHEN ''PREP'' THEN ', v_prep_margin, '
                        ELSE 27.0
                    END / 100))
                ),
                2
            ) as total_sale_price,
            ROUND(
                SUM((ExtSalesAmount * ', p_msrp_volume, ') / ', p_msrp_margin, '),
                2
            ) as total_msrp
        FROM ', v_table_name, '
        WHERE WebOrderNo = ''', v_web_order_no, '''
        GROUP BY ItemMasterProdCat
        ORDER BY FIELD(ItemMasterProdCat, ''BOAT'', ''ENG'', ''ACC'', ''FRT'', ''PREP'')
    ');
    
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
    
    -- Result Set 4: Dealer Margins Applied
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
            ROUND(
                SUM(
                    (ExtSalesAmount * 1.00) / (1 - (CASE ItemMasterProdCat
                        WHEN ''BOAT'' THEN ', v_base_margin, '
                        WHEN ''ENG'' THEN ', v_engine_margin, '
                        WHEN ''ACC'' THEN ', v_options_margin, '
                        WHEN ''FRT'' THEN ', v_freight_margin, '
                        WHEN ''PREP'' THEN ', v_prep_margin, '
                        ELSE 27.0
                    END / 100))
                ),
                2
            ) as grand_total_sale_price,
            ROUND(
                SUM((ExtSalesAmount * ', p_msrp_volume, ') / ', p_msrp_margin, '),
                2
            ) as grand_total_msrp,
            ROUND(
                SUM(
                    ((ExtSalesAmount * 1.00) / (1 - (CASE ItemMasterProdCat
                        WHEN ''BOAT'' THEN ', v_base_margin, '
                        WHEN ''ENG'' THEN ', v_engine_margin, '
                        WHEN ''ACC'' THEN ', v_options_margin, '
                        WHEN ''FRT'' THEN ', v_freight_margin, '
                        WHEN ''PREP'' THEN ', v_prep_margin, '
                        ELSE 27.0
                    END / 100))
                ) - SUM(ExtSalesAmount),
                2
            ) as total_margin_dollars
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
    print("=" * 80)
    
    try:
        cursor.callproc('GetCompleteBoatInformation', [hull_no, 0.75, 1.00])
        
        # Fetch all result sets
        result_sets = []
        for result in cursor.stored_results():
            result_sets.append(result.fetchall())
        
        # Display results
        print("\n--- Result Set 1: Boat Header ---")
        if result_sets and result_sets[0]:
            headers = ['hull_no', 'model_no', 'web_order_no', 'dealer_id', 'dealer_name', 'series_raw', 
                      'series_id', 'model_year', 'options_table', 'generated_at']
            for row in result_sets[0]:
                for header, value in zip(headers, row):
                    print(f"{header}: {value}")
        
        print("\n--- Result Set 2: Line Items (First 5) ---")
        if len(result_sets) > 1 and result_sets[1]:
            headers = ['item_no', 'item_description', 'product_category', 'quantity',
                      'dealer_cost', 'margin_pct', 'sale_price', 'msrp']
            print(f"{'Item':<15} {'Description':<40} {'Cat':<6} {'Qty':<5} {'Dealer Cost':<12} {'Margin%':<8} {'Sale Price':<12} {'MSRP':<12}")
            print("-" * 120)
            for row in result_sets[1][:5]:
                print(f"{str(row[0]):<15} {str(row[1])[:40]:<40} {str(row[2]):<6} {row[3]:<5} ${row[4]:>10,.2f} {row[5]:>6.1f}% ${row[6]:>10,.2f} ${row[7]:>10,.2f}")
            if len(result_sets[1]) > 5:
                print(f"... and {len(result_sets[1]) - 5} more items")
        else:
            print("No line items found")
        
        print("\n--- Result Set 3: Pricing Summary by Category ---")
        if len(result_sets) > 2 and result_sets[2]:
            print(f"{'Category':<10} {'Items':<8} {'Qty':<6} {'Dealer Cost':<15} {'Margin%':<8} {'Sale Price':<15} {'MSRP':<15}")
            print("-" * 90)
            for row in result_sets[2]:
                print(f"{row[0]:<10} {row[1]:<8} {row[2]:<6} ${row[3]:>12,.2f} {row[4]:>6.1f}% ${row[5]:>12,.2f} ${row[6]:>12,.2f}")
        else:
            print("No summary data found")
        
        print("\n--- Result Set 4: Dealer Margins Applied ---")
        if len(result_sets) > 3 and result_sets[3]:
            row = result_sets[3][0]
            print(f"Dealer ID: {row[0]}")
            print(f"Series: {row[1]}")
            print(f"Base Boat Margin: {row[2]}%")
            print(f"Engine Margin: {row[3]}%")
            print(f"Options Margin: {row[4]}%")
            print(f"Freight Margin: {row[5]}%")
            print(f"Prep Margin: {row[6]}%")
            print(f"MSRP Margin: {row[7]} (multiplier: {1/row[7]:.2f}x)")
            print(f"MSRP Volume: {row[8]} (multiplier: {row[8]}x)")
        
        print("\n--- Result Set 5: Grand Totals ---")
        if len(result_sets) > 4 and result_sets[4]:
            row = result_sets[4][0]
            if row[0] is not None:
                print(f"Total Line Items: {row[0]}")
                print(f"Total Quantity: {row[1]}")
                print(f"Grand Total Dealer Cost: ${row[2]:,.2f}")
                print(f"Grand Total Sale Price: ${row[3]:,.2f}")
                print(f"Grand Total MSRP: ${row[4]:,.2f}")
                print(f"Total Margin Dollars: ${row[5]:,.2f}")
                if row[2] > 0:
                    margin_pct = (row[5] / row[2]) * 100
                    print(f"Effective Margin %: {margin_pct:.2f}%")
            else:
                print("No totals data found")
        
        print("\n" + "=" * 80)
        print("Test completed successfully!")
        
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
        
        # Install procedure
        install_procedure(cursor)
        connection.commit()
        
        # Find or use provided hull
        if len(sys.argv) > 1:
            hull_no = sys.argv[1]
        else:
            hull_no = find_test_hull(cursor)
            if not hull_no:
                print("No valid test hulls found!")
                sys.exit(1)
        
        # Test procedure
        test_procedure(cursor, hull_no)
        
        cursor.close()
        print("\nAll operations completed successfully!")
        
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

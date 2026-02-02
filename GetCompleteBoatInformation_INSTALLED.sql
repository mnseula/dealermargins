-- GetCompleteBoatInformation Stored Procedure
-- Successfully installed on 2026-02-02
-- 
-- Purpose: Calculate 3 price points (dealer cost, sale price, MSRP) for window stickers
--
-- Parameters:
--   p_hull_no      - Hull serial number (e.g., 'ETW47042G607')
--   p_msrp_margin  - MSRP margin multiplier (default 0.75 = 75%)
--   p_msrp_volume  - MSRP volume multiplier (default 1.00 = 100%)
--
-- Returns 5 result sets:
--   1. Boat Header - Hull, model, dealer, series, year info
--   2. Line Items - Individual items with pricing calculations
--   3. Category Summary - Totals by product category (BOAT, ENG, ACC, FRT, PREP)
--   4. Dealer Margins - Margin percentages applied
--   5. Grand Totals - Overall pricing summary
--
-- Usage:
--   CALL GetCompleteBoatInformation('ETW47042G607', 0.75, 1.00);
--
-- NOTE: Current implementation uses WebOrderNo to link SerialNumberMaster to BoatOptions tables.
--       If no line items appear, the linking logic may need adjustment (try ERP_OrderNo or InvoiceNo).
--

DROP PROCEDURE IF EXISTS GetCompleteBoatInformation;

DELIMITER $$

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
    
END$$

DELIMITER ;

-- ============================================================================
-- GetBoatPricingWithPackage - Calculate boat pricing with package logic
-- ============================================================================
-- Replicates JavaScript Calculate2021.js with boat package pricing
-- Usage: CALL GetBoatPricingWithPackage('ETWP7154K324');
-- ============================================================================

DROP PROCEDURE IF EXISTS GetBoatPricingWithPackage;

DELIMITER $$

CREATE PROCEDURE GetBoatPricingWithPackage(
    IN p_serial_number VARCHAR(50)
)
BEGIN
    DECLARE v_dealer_id VARCHAR(20);
    DECLARE v_series VARCHAR(10);
    DECLARE v_model_year INT;
    DECLARE v_invoice_no VARCHAR(50);
    DECLARE v_boat_model VARCHAR(50);
    DECLARE v_real_model VARCHAR(50);

    -- Dealer margins
    DECLARE v_baseboatmargin DECIMAL(10,4);
    DECLARE v_enginemargin DECIMAL(10,4);
    DECLARE v_optionmargin DECIMAL(10,4);
    DECLARE v_vol_disc DECIMAL(10,4);
    DECLARE v_freight DECIMAL(10,2);
    DECLARE v_prep DECIMAL(10,2);

    -- MSRP margins
    DECLARE v_msrp_margin DECIMAL(10,4) DEFAULT 0.79;
    DECLARE v_msrp_volume DECIMAL(10,4) DEFAULT 1.0;
    DECLARE v_msrp_loyalty DECIMAL(10,4) DEFAULT 1.0;

    -- Package pricing variables
    DECLARE v_boat_cost DECIMAL(10,2) DEFAULT 0;
    DECLARE v_engine_cost DECIMAL(10,2) DEFAULT 0;
    DECLARE v_prerig_cost DECIMAL(10,2) DEFAULT 0;
    DECLARE v_default_engine_cost DECIMAL(10,2) DEFAULT 0;
    DECLARE v_default_prerig_cost DECIMAL(10,2) DEFAULT 0;

    DECLARE v_series_prefix VARCHAR(10);
    DECLARE v_has_engine INT DEFAULT 0;
    DECLARE v_has_prerig INT DEFAULT 0;

    -- Get boat information
    SELECT
        DealerNumber,
        Series,
        CAST(SUBSTRING(Boat_SerialNo, -2) AS UNSIGNED),
        InvoiceNo,
        BoatItemNo
    INTO
        v_dealer_id,
        v_series,
        v_model_year,
        v_invoice_no,
        v_boat_model
    FROM warrantyparts.SerialNumberMaster
    WHERE Boat_SerialNo = p_serial_number;

    -- Get the real model from BoatOptions
    SET @get_model_sql = CONCAT(
        'SELECT BoatModelNo INTO @real_model ',
        'FROM warrantyparts.BoatOptions', v_model_year, ' ',
        'WHERE BoatSerialNo = ''', p_serial_number, ''' ',
        'AND MCTDesc = ''PONTOONS'' LIMIT 1'
    );
    PREPARE stmt FROM @get_model_sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;

    SET v_real_model = @real_model;

    -- Determine series prefix
    SET v_series_prefix = CASE
        WHEN v_series = 'SV' THEN 'SV_23'
        WHEN v_series = 'S' THEN 'S_23'
        ELSE v_series
    END;

    -- Get dealer margins
    SET @margin_sql = CONCAT(
        'SELECT ',
        '(100 - ', v_series_prefix, '_BASE_BOAT) / 100, ',
        '(100 - ', v_series_prefix, '_ENGINE) / 100, ',
        '(100 - ', v_series_prefix, '_OPTIONS) / 100, ',
        '(100 - ', v_series_prefix, '_VOL_DISC) * 0.01, ',
        v_series_prefix, '_FREIGHT, ',
        v_series_prefix, '_PREP ',
        'INTO @baseboatmargin, @enginemargin, @optionmargin, @vol_disc, @freight, @prep ',
        'FROM warrantyparts.DealerMargins ',
        'WHERE DealerID = ''', v_dealer_id, ''''
    );

    PREPARE stmt FROM @margin_sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;

    SET v_baseboatmargin = @baseboatmargin;
    SET v_enginemargin = @enginemargin;
    SET v_optionmargin = @optionmargin;
    SET v_vol_disc = @vol_disc;
    SET v_freight = @freight;
    SET v_prep = @prep;

    -- Create temporary table for raw line items
    DROP TEMPORARY TABLE IF EXISTS temp_line_items;
    CREATE TEMPORARY TABLE temp_line_items (
        line_order INT AUTO_INCREMENT PRIMARY KEY,
        description VARCHAR(255),
        item_no VARCHAR(50),
        category VARCHAR(50),
        dealer_cost DECIMAL(10,2),
        sale_price DECIMAL(10,2),
        msrp DECIMAL(10,2),
        is_package_component TINYINT DEFAULT 0,
        is_discount TINYINT DEFAULT 0
    );

    -- Get boat cost and apply series discount
    SET @boat_sql = CONCAT(
        'SELECT COALESCE(ExtSalesAmount, 0) ',
        '- CASE ',
        '    WHEN ''', v_series, ''' = ''SV'' THEN ',
        '        CASE ',
        '            WHEN BoatModelNo LIKE ''%188%'' THEN 1650 ',
        '            WHEN BoatModelNo LIKE ''20%'' THEN 1700 ',
        '            WHEN BoatModelNo LIKE ''22%'' THEN 750 ',
        '            ELSE 0 ',
        '        END ',
        '    WHEN ''', v_series, ''' = ''S'' THEN ',
        '        CASE ',
        '            WHEN BoatModelNo LIKE ''%188%'' THEN 1650 ',
        '            WHEN BoatModelNo LIKE ''20%'' THEN 1700 ',
        '            WHEN BoatModelNo LIKE ''22%'' THEN 750 ',
        '            ELSE 0 ',
        '        END ',
        '    ELSE 0 ',
        'END INTO @boat_cost ',
        'FROM warrantyparts.BoatOptions', v_model_year, ' ',
        'WHERE BoatSerialNo = ''', p_serial_number, ''' ',
        'AND MCTDesc = ''PONTOONS'''
    );

    PREPARE stmt FROM @boat_sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;

    SET v_boat_cost = COALESCE(@boat_cost, 0);

    -- Get engine cost
    SET @engine_sql = CONCAT(
        'SELECT COALESCE(ExtSalesAmount, 0), 1 INTO @engine_cost, @has_engine ',
        'FROM warrantyparts.BoatOptions', v_model_year, ' ',
        'WHERE BoatSerialNo = ''', p_serial_number, ''' ',
        'AND MCTDesc IN (''ENGINES'', ''ENGINES I/O'') LIMIT 1'
    );

    PREPARE stmt FROM @engine_sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;

    SET v_engine_cost = COALESCE(@engine_cost, 0);
    SET v_has_engine = COALESCE(@has_engine, 0);

    -- Get prerig cost
    SET @prerig_sql = CONCAT(
        'SELECT COALESCE(ExtSalesAmount, 0), 1 INTO @prerig_cost, @has_prerig ',
        'FROM warrantyparts.BoatOptions', v_model_year, ' ',
        'WHERE BoatSerialNo = ''', p_serial_number, ''' ',
        'AND MCTDesc = ''PRE-RIG'' LIMIT 1'
    );

    PREPARE stmt FROM @prerig_sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;

    SET v_prerig_cost = COALESCE(@prerig_cost, 0);
    SET v_has_prerig = COALESCE(@has_prerig, 0);

    -- Estimate default engine and prerig costs
    -- This is a simplified approach - in production, this would need proper lookup tables
    -- For SV series with Mercury 115HP, typical defaults might be:
    -- Default engine: ~90HP = ~$8,000-9,000 dealer cost
    -- Default prerig: ~$1,200-1,300

    -- Try to get default costs from similar boats
    SET @default_engine_sql = CONCAT(
        'SELECT AVG(COALESCE(ExtSalesAmount, 0)) INTO @avg_engine_cost ',
        'FROM warrantyparts.BoatOptions', v_model_year, ' bo ',
        'WHERE bo.MCTDesc IN (''ENGINES'', ''ENGINES I/O'') ',
        'AND bo.BoatModelNo = ''', v_real_model, ''' ',
        'AND bo.ExtSalesAmount < ', v_engine_cost, ' ',
        'ORDER BY bo.ExtSalesAmount LIMIT 5'
    );

    PREPARE stmt FROM @default_engine_sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;

    -- Use the smaller engine as default, or 85% of actual as fallback
    SET v_default_engine_cost = COALESCE(@avg_engine_cost, v_engine_cost * 0.85);

    -- For prerig, use 95% as default (usually prerig variations are smaller)
    SET v_default_prerig_cost = v_prerig_cost * 0.95;

    -- Calculate boat package price (boat + default engine + default prerig)
    SET @package_dealer_cost = v_boat_cost + v_default_engine_cost + v_default_prerig_cost;

    -- Calculate package sale price and MSRP
    IF v_series = 'SV' THEN
        -- For SV: sale = msrp
        SET @package_sale = ROUND((@package_dealer_cost * v_msrp_volume * v_msrp_loyalty) / v_baseboatmargin + v_freight + v_prep, 2);
        SET @package_msrp = @package_sale;
    ELSE
        SET @package_sale = ROUND(((@package_dealer_cost * v_vol_disc) / v_baseboatmargin) + v_freight + v_prep, 2);
        SET @package_msrp = ROUND((@package_dealer_cost * v_vol_disc) / v_msrp_margin, 2);
    END IF;

    -- Insert BOAT PACKAGE line
    IF v_has_engine = 1 AND v_has_prerig = 1 THEN
        INSERT INTO temp_line_items (description, item_no, category, dealer_cost, sale_price, msrp, is_package_component)
        VALUES ('BOAT PACKAGE', 'BOAT, ENGINE, PRE-RIG', 'PACKAGE', @package_dealer_cost, @package_sale, @package_msrp, 1);
    END IF;

    -- Calculate engine increment (actual - default)
    IF v_has_engine = 1 THEN
        SET @engine_increment = v_engine_cost - v_default_engine_cost;

        IF v_series = 'SV' THEN
            SET @engine_inc_sale = ROUND((@engine_increment * v_msrp_volume * v_msrp_loyalty) / v_msrp_margin, 2);
            SET @engine_inc_msrp = @engine_inc_sale;
        ELSE
            SET @engine_inc_sale = ROUND((@engine_increment * v_vol_disc) / v_enginemargin, 2);
            SET @engine_inc_msrp = ROUND((@engine_increment * v_msrp_volume) / v_msrp_margin, 2);
        END IF;

        -- Get engine description
        SET @engine_desc_sql = CONCAT(
            'SELECT ItemDesc1, ItemNo INTO @engine_desc, @engine_itemno ',
            'FROM warrantyparts.BoatOptions', v_model_year, ' ',
            'WHERE BoatSerialNo = ''', p_serial_number, ''' ',
            'AND MCTDesc IN (''ENGINES'', ''ENGINES I/O'') LIMIT 1'
        );

        PREPARE stmt FROM @engine_desc_sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;

        -- Only show engine line if there's an increment
        IF ABS(@engine_increment) > 0.01 THEN
            INSERT INTO temp_line_items (description, item_no, category, dealer_cost, sale_price, msrp, is_package_component)
            VALUES (@engine_desc, @engine_itemno, 'ENGINE INCREMENT', @engine_increment, @engine_inc_sale, @engine_inc_msrp, 1);
        END IF;
    END IF;

    -- Calculate prerig increment (actual - default)
    IF v_has_prerig = 1 THEN
        SET @prerig_increment = v_prerig_cost - v_default_prerig_cost;

        IF v_series = 'SV' THEN
            SET @prerig_inc_sale = ROUND((@prerig_increment * v_msrp_volume * v_msrp_loyalty) / v_msrp_margin, 2);
            SET @prerig_inc_msrp = @prerig_inc_sale;
        ELSE
            SET @prerig_inc_sale = ROUND((@prerig_increment * v_vol_disc) / v_optionmargin, 2);
            SET @prerig_inc_msrp = ROUND((@prerig_increment * v_msrp_volume) / v_msrp_margin, 2);
        END IF;

        -- Get prerig description
        SET @prerig_desc_sql = CONCAT(
            'SELECT ItemDesc1, ItemNo INTO @prerig_desc, @prerig_itemno ',
            'FROM warrantyparts.BoatOptions', v_model_year, ' ',
            'WHERE BoatSerialNo = ''', p_serial_number, ''' ',
            'AND MCTDesc = ''PRE-RIG'' LIMIT 1'
        );

        PREPARE stmt FROM @prerig_desc_sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;

        -- Only show prerig line if there's an increment
        IF ABS(@prerig_increment) > 0.01 THEN
            INSERT INTO temp_line_items (description, item_no, category, dealer_cost, sale_price, msrp, is_package_component)
            VALUES (@prerig_desc, @prerig_itemno, 'PRERIG INCREMENT', @prerig_increment, @prerig_inc_sale, @prerig_inc_msrp, 1);
        END IF;
    END IF;

    -- Add all other options (not boat, engine, prerig, or discounts)
    SET @options_sql = CONCAT(
        'INSERT INTO temp_line_items (description, item_no, category, dealer_cost, sale_price, msrp, is_discount) ',
        'SELECT ',
        '    ItemDesc1, ',
        '    ItemNo, ',
        '    MCTDesc, ',
        '    COALESCE(ExtSalesAmount, 0), ',
        '    CASE ',
        '        WHEN ''', v_series, ''' = ''SV'' THEN ',
        '            ROUND(((COALESCE(ExtSalesAmount, 0) * ', v_msrp_volume, ') / ', v_msrp_margin, ') * ', v_msrp_loyalty, ', 2) ',
        '        ELSE ',
        '            ROUND((COALESCE(ExtSalesAmount, 0) * ', v_vol_disc, ') / ', v_optionmargin, ', 2) ',
        '    END, ',
        '    CASE ',
        '        WHEN ''', v_series, ''' = ''SV'' THEN ',
        '            ROUND(((COALESCE(ExtSalesAmount, 0) * ', v_msrp_volume, ') / ', v_msrp_margin, ') * ', v_msrp_loyalty, ', 2) ',
        '        ELSE ',
        '            ROUND((COALESCE(ExtSalesAmount, 0) * ', v_msrp_volume, ') / ', v_msrp_margin, ', 2) ',
        '    END, ',
        '    CASE ',
        '        WHEN MCTDesc LIKE ''Disc%'' OR MCTDesc LIKE ''%DISCOUNT%'' THEN 1 ',
        '        ELSE 0 ',
        '    END ',
        'FROM warrantyparts.BoatOptions', v_model_year, ' ',
        'WHERE BoatSerialNo = ''', p_serial_number, ''' ',
        'AND MCTDesc NOT IN (''PONTOONS'', ''Pontoon Boats OB'', ''ENGINES'', ''ENGINES I/O'', ''PRE-RIG'', ''Lower Unit Eng'', ''GROW BOATING'') ',
        'AND ItemMasterMCT NOT IN (''DIC'',''DIF'',''DIP'',''DIR'',''DIA'',''DIW'',''LOY'',''PRD'',''VOD'',''DIV'',''CAS'',''SHO'',''GRO'',''ZZZ'',''FRE'',''WAR'',''DLR'',''FRT'') ',
        'AND ItemMasterProdCat != ''111'' ',
        'ORDER BY ',
        '    CASE MCTDesc ',
        '        WHEN ''PERFORMANCE PKG'' THEN 1 ',
        '        WHEN ''Disc - Selling'' THEN 999 ',
        '        WHEN ''Disc - Volume'' THEN 999 ',
        '        ELSE 2 ',
        '    END, ',
        '    LineNo'
    );

    PREPARE stmt FROM @options_sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;

    -- Return the formatted results (excluding discounts from display)
    SELECT
        description AS 'Item Description',
        item_no AS 'Item #',
        category AS 'Category',
        dealer_cost AS 'Dealer Cost',
        sale_price AS 'Sale Price',
        msrp AS 'MSRP'
    FROM temp_line_items
    WHERE is_discount = 0  -- Exclude discount lines from display
    ORDER BY line_order;

    -- Clean up
    DROP TEMPORARY TABLE IF EXISTS temp_line_items;

END$$

DELIMITER ;

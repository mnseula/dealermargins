-- ============================================================================
-- GetBoatPricing - Calculate boat pricing following Calculate2021.js logic
-- ============================================================================
-- This procedure replicates the JavaScript pricing calculation in SQL
-- Usage: CALL GetBoatPricing('ETWP5175I324');
-- ============================================================================

DROP PROCEDURE IF EXISTS GetBoatPricing;

DELIMITER $$

CREATE PROCEDURE GetBoatPricing(
    IN p_serial_number VARCHAR(50)
)
BEGIN
    DECLARE v_dealer_id VARCHAR(20);
    DECLARE v_series VARCHAR(10);
    DECLARE v_model_year INT;
    DECLARE v_invoice_no VARCHAR(50);
    DECLARE v_erp_order VARCHAR(50);
    DECLARE v_boat_model VARCHAR(50);

    -- Dealer margins
    DECLARE v_baseboatmargin DECIMAL(10,4);
    DECLARE v_enginemargin DECIMAL(10,4);
    DECLARE v_optionmargin DECIMAL(10,4);
    DECLARE v_vol_disc DECIMAL(10,4);
    DECLARE v_freight DECIMAL(10,2);
    DECLARE v_prep DECIMAL(10,2);

    -- MSRP margins (company-wide)
    DECLARE v_msrp_margin DECIMAL(10,4) DEFAULT 0.79;
    DECLARE v_msrp_volume DECIMAL(10,4) DEFAULT 1.0;
    DECLARE v_msrp_loyalty DECIMAL(10,4) DEFAULT 1.0;

    DECLARE v_series_prefix VARCHAR(10);

    -- Get boat information
    SELECT
        DealerNumber,
        Series,
        CAST(SUBSTRING(Boat_SerialNo, -2) AS UNSIGNED) AS model_year,
        InvoiceNo,
        ERP_OrderNo,
        BoatItemNo
    INTO
        v_dealer_id,
        v_series,
        v_model_year,
        v_invoice_no,
        v_erp_order,
        v_boat_model
    FROM warrantyparts.SerialNumberMaster
    WHERE Boat_SerialNo = p_serial_number;

    -- Determine series prefix for margin lookup
    SET v_series_prefix = CASE
        WHEN v_series = 'SV' THEN 'SV_23'
        WHEN v_series = 'S' THEN 'S_23'
        ELSE v_series
    END;

    -- Get dealer margins using dynamic SQL
    SET @sql = CONCAT(
        'SELECT ',
        '(100 - ', v_series_prefix, '_BASE_BOAT) / 100, ',
        '(100 - ', v_series_prefix, '_ENGINE) / 100, ',
        '(100 - ', v_series_prefix, '_OPTIONS) / 100, ',
        '(100 - ', v_series_prefix, '_VOL_DISC) * 0.01, ',
        v_series_prefix, '_FREIGHT, ',
        v_series_prefix, '_PREP ',
        'FROM warrantyparts.DealerMargins ',
        'WHERE DealerID = ''', v_dealer_id, ''''
    );

    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;

    -- Store results in variables
    SET @sql = CONCAT(
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

    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;

    SET v_baseboatmargin = @baseboatmargin;
    SET v_enginemargin = @enginemargin;
    SET v_optionmargin = @optionmargin;
    SET v_vol_disc = @vol_disc;
    SET v_freight = @freight;
    SET v_prep = @prep;

    -- Build the dynamic table name for BoatOptions
    SET @table_name = CONCAT('warrantyparts.BoatOptions', v_model_year);

    -- Calculate pricing for each line item
    SET @sql = CONCAT(
        'SELECT ',
        '    ItemDesc1 AS Description, ',
        '    MCTDesc AS Category, ',
        '    CAST(COALESCE(ExtSalesAmount, 0) AS DECIMAL(10,2)) AS DealerCost, ',
        '    CASE ',
        -- PONTOONS
        '        WHEN MCTDesc = ''PONTOONS'' THEN ',
        '            ROUND(',
        '                CASE ',
        '                    WHEN ''', v_series, ''' = ''SV'' THEN ',
        '                        ((CAST(COALESCE(ExtSalesAmount, 0) AS DECIMAL(10,2)) ',
        -- Apply SV series discount
        '                        - CASE ',
        '                            WHEN BoatModelNo LIKE ''%188%'' THEN 1650 ',
        '                            WHEN BoatModelNo LIKE ''20%'' THEN 1700 ',
        '                            WHEN BoatModelNo LIKE ''22%'' THEN 750 ',
        '                            ELSE 0 ',
        '                        END) * ', v_msrp_volume, ' * ', v_msrp_loyalty, ') / ', v_baseboatmargin,
        '                        + ', v_freight, ' + ', v_prep,
        '                    ELSE ',
        '                        ((CAST(COALESCE(ExtSalesAmount, 0) AS DECIMAL(10,2)) * ', v_vol_disc, ') / ', v_baseboatmargin, ') ',
        '                        + ', v_freight, ' + ', v_prep,
        '                END, 2',
        '            ) ',
        -- ENGINES
        '        WHEN MCTDesc IN (''ENGINES'', ''ENGINES I/O'') THEN ',
        '            ROUND(',
        '                CASE ',
        '                    WHEN ''', v_series, ''' = ''SV'' THEN ',
        '                        (CAST(COALESCE(ExtSalesAmount, 0) AS DECIMAL(10,2)) * ', v_msrp_volume, ' * ', v_msrp_loyalty, ') / ', v_msrp_margin,
        '                    ELSE ',
        '                        (CAST(COALESCE(ExtSalesAmount, 0) AS DECIMAL(10,2)) * ', v_vol_disc, ') / ', v_enginemargin,
        '                END, 2',
        '            ) ',
        -- PRE-RIG
        '        WHEN MCTDesc = ''PRE-RIG'' THEN ',
        '            ROUND(',
        '                CASE ',
        '                    WHEN ''', v_series, ''' = ''SV'' THEN ',
        '                        (CAST(COALESCE(ExtSalesAmount, 0) AS DECIMAL(10,2)) * ', v_msrp_volume, ' * ', v_msrp_loyalty, ') / ', v_msrp_margin,
        '                    ELSE ',
        '                        (CAST(COALESCE(ExtSalesAmount, 0) AS DECIMAL(10,2)) * ', v_vol_disc, ') / ', v_optionmargin,
        '                END, 2',
        '            ) ',
        -- OTHER OPTIONS
        '        ELSE ',
        '            ROUND(',
        '                CASE ',
        '                    WHEN ''', v_series, ''' = ''SV'' THEN ',
        '                        ((CAST(COALESCE(ExtSalesAmount, 0) AS DECIMAL(10,2)) * ', v_msrp_volume, ') / ', v_msrp_margin, ') * ', v_msrp_loyalty,
        '                    ELSE ',
        '                        (CAST(COALESCE(ExtSalesAmount, 0) AS DECIMAL(10,2)) * ', v_vol_disc, ') / ', v_optionmargin,
        '                END, 2',
        '            ) ',
        '    END AS SalePrice, ',
        '    CASE ',
        -- For SV series, MSRP = Sale Price
        '        WHEN ''', v_series, ''' = ''SV'' THEN ',
        '            CASE ',
        '                WHEN MCTDesc = ''PONTOONS'' THEN ',
        '                    ROUND(',
        '                        ((CAST(COALESCE(ExtSalesAmount, 0) AS DECIMAL(10,2)) ',
        '                        - CASE ',
        '                            WHEN BoatModelNo LIKE ''%188%'' THEN 1650 ',
        '                            WHEN BoatModelNo LIKE ''20%'' THEN 1700 ',
        '                            WHEN BoatModelNo LIKE ''22%'' THEN 750 ',
        '                            ELSE 0 ',
        '                        END) * ', v_msrp_volume, ' * ', v_msrp_loyalty, ') / ', v_baseboatmargin,
        '                        + ', v_freight, ' + ', v_prep, ', 2',
        '                    ) ',
        '                ELSE ',
        '                    ROUND(',
        '                        (CAST(COALESCE(ExtSalesAmount, 0) AS DECIMAL(10,2)) * ', v_msrp_volume, ' * ', v_msrp_loyalty, ') / ', v_msrp_margin, ', 2',
        '                    ) ',
        '            END ',
        -- For other series, calculate MSRP separately
        '        ELSE ',
        '            CASE ',
        '                WHEN MCTDesc = ''PONTOONS'' THEN ',
        '                    ROUND(',
        '                        ((CAST(COALESCE(ExtSalesAmount, 0) AS DECIMAL(10,2)) * ', v_vol_disc, ') / ', v_msrp_margin, '), 2',
        '                    ) ',
        '                ELSE ',
        '                    ROUND(',
        '                        (CAST(COALESCE(ExtSalesAmount, 0) AS DECIMAL(10,2)) * ', v_msrp_volume, ') / ', v_msrp_margin, ', 2',
        '                    ) ',
        '            END ',
        '    END AS MSRP ',
        'FROM ', @table_name, ' ',
        'WHERE BoatSerialNo = ''', p_serial_number, ''' ',
        'AND ItemMasterMCT NOT IN (''DIC'',''DIF'',''DIP'',''DIR'',''DIA'',''DIW'',''LOY'',''PRD'',''VOD'',''DIV'',''CAS'',''SHO'',''GRO'',''ZZZ'',''FRE'',''WAR'',''DLR'',''FRT'') ',
        'AND ItemMasterProdCat != ''111'' ',
        'AND MCTDesc NOT IN (''Lower Unit Eng'') ',
        'ORDER BY CASE MCTDesc ',
        '    WHEN ''PONTOONS'' THEN 1 ',
        '    WHEN ''Pontoon Boats OB'' THEN 1 ',
        '    WHEN ''ENGINES'' THEN 2 ',
        '    WHEN ''PRE-RIG'' THEN 3 ',
        '    ELSE 4 ',
        'END, LineNo'
    );

    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;

END$$

DELIMITER ;

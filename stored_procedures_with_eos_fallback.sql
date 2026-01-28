-- ============================================================================
-- Bennington CPQ - Stored Procedures with EOS Fallback
-- ============================================================================
-- Purpose: SQL-driven window sticker generation with backward compatibility
-- All procedures try CPQ first, then fall back to EOS database if not found
-- ============================================================================

USE warrantyparts_test;

-- Drop existing procedures
DROP PROCEDURE IF EXISTS GetIncludedOptions;
DROP PROCEDURE IF EXISTS GetWindowStickerData;
DROP PROCEDURE IF EXISTS CalculateDealerQuote;
DROP PROCEDURE IF EXISTS GetModelFullDetails;

DELIMITER //

-- ============================================================================
-- Procedure: GetIncludedOptions
-- ============================================================================
-- Gets included options/accessories for a specific model
-- Reads from BoatOptions based on year

CREATE PROCEDURE GetIncludedOptions(
    IN p_model_id VARCHAR(20),
    IN p_year INT
)
BEGIN
    SET @year_suffix = RIGHT(CAST(p_year AS CHAR), 2);
    SET @table_name = CONCAT('warrantyparts.BoatOptions', @year_suffix);

    SET @query = CONCAT('
        SELECT DISTINCT
            ItemNo,
            ItemDesc1 AS ItemDescription,
            QuantitySold AS Quantity,
            ExtSalesAmount AS SalePrice,
            ExtSalesAmount AS MSRP
        FROM ', @table_name, '
        WHERE BoatModelNo = ?
          AND ItemMasterProdCat = ''ACC''
          AND ItemNo IS NOT NULL
          AND ItemNo != ''''
        ORDER BY ItemDesc1
    ');

    PREPARE stmt FROM @query;
    SET @model_param = p_model_id;
    EXECUTE stmt USING @model_param;
    DEALLOCATE PREPARE stmt;
END //

-- ============================================================================
-- Procedure: GetWindowStickerData
-- ============================================================================
-- Gets complete window sticker data for a model
-- WITH EOS FALLBACK for backward compatibility
--
-- Logic:
-- 1. Try CPQ first (warrantyparts_test)
-- 2. If model not found, fall back to EOS database
-- 3. If specific identifier provided (HIN/Order), filter to that boat
--
-- Parameters:
--   p_model_id: Model ID (e.g., '25QXFBWA' or '168SFSR')
--   p_dealer_id: Dealer ID (e.g., '333836')
--   p_year: Model year (e.g., 2025)
--   p_identifier: Optional HIN or Order Number to filter specific boat
--
-- Returns 4 result sets:
--   1. Model basic info with pricing
--   2. Performance specifications (filtered by identifier if provided)
--   3. Standard features by area
--   4. Included options from sales database

CREATE PROCEDURE GetWindowStickerData(
    IN p_model_id VARCHAR(20),
    IN p_dealer_id VARCHAR(20),
    IN p_year INT,
    IN p_identifier VARCHAR(30)
)
BEGIN
    DECLARE v_cpq_exists INT DEFAULT 0;
    DECLARE v_base_model VARCHAR(20);

    -- Check if model exists in CPQ
    SELECT COUNT(*) INTO v_cpq_exists
    FROM Models
    WHERE model_id = p_model_id;

    IF v_cpq_exists > 0 THEN
        -- ===== CPQ PATH =====

        -- Result Set 1: Model Information with Pricing from CPQ
        SELECT
            m.model_id,
            m.model_name,
            m.series_id,
            s.series_name,
            s.parent_series,
            m.floorplan_code,
            m.floorplan_desc,
            m.length_feet,
            m.length_str,
            m.beam_length,
            m.beam_str,
            m.loa,
            m.loa_str,
            m.seats,
            p.msrp,
            p.year,
            p.effective_date,
            d.dealerno AS dealer_id,
            d.dealer AS dealer_name,
            d.city,
            d.state,
            NOW() AS generated_date,
            'CPQ' AS data_source
        FROM Models m
        JOIN Series s ON m.series_id = s.series_id
        LEFT JOIN ModelPricing p ON m.model_id = p.model_id
            AND p.year = p_year
            AND p.end_date IS NULL
        LEFT JOIN warrantyparts.`dealermaster - use the one in eos` d
            ON d.dealerno = p_dealer_id
            AND d.productline = 'BEN'
        WHERE m.model_id = p_model_id;

        -- Result Set 2: Performance Specifications from CPQ
        SELECT
            mp.perf_package_id,
            pp.package_name,
            mp.max_hp,
            mp.no_of_tubes,
            mp.person_capacity,
            mp.hull_weight,
            mp.pontoon_gauge,
            mp.transom,
            mp.tube_height,
            mp.tube_center_to_center,
            mp.max_width,
            mp.fuel_capacity,
            mp.tube_length_str,
            mp.deck_length_str
        FROM ModelPerformance mp
        JOIN PerformancePackages pp ON mp.perf_package_id = pp.perf_package_id
        WHERE mp.model_id = p_model_id
          AND mp.year = p_year
          AND (
              p_identifier IS NULL
              OR mp.perf_package_id = (
                  SELECT attr_value
                  FROM BoatConfigurationAttributes
                  WHERE (boat_serial_no = p_identifier OR erp_order_no = p_identifier)
                    AND attr_name = 'PerformancePackage'
                  LIMIT 1
              )
          )
        ORDER BY mp.perf_package_id;

        -- Result Set 3: Standard Features from CPQ
        SELECT
            sf.area,
            sf.description,
            sf.sort_order
        FROM ModelStandardFeatures msf
        JOIN StandardFeatures sf ON msf.feature_id = sf.feature_id
        WHERE msf.model_id = p_model_id
          AND msf.year = p_year
          AND sf.active = TRUE
        ORDER BY sf.area, sf.sort_order;

    ELSE
        -- ===== EOS FALLBACK PATH =====

        -- Extract base model (remove suffixes like SR, SE, etc.)
        -- Examples: 168SFSR -> 168SF, 25QFBWASR -> 25QFBWA
        SET v_base_model = p_model_id;
        IF v_base_model REGEXP '(SR|SE|SA|SB|ST|SP|SG|SD|SN|DI|DL|DN|DE|DF)$' THEN
            SET v_base_model = SUBSTRING(v_base_model, 1, LENGTH(v_base_model) - 2);
        END IF;

        -- Result Set 1: Model Information from EOS/SerialNumberMaster
        SELECT
            p_model_id AS model_id,
            NULL AS model_name,
            snm.Series AS series_id,
            snm.Series AS series_name,
            snm.Series AS parent_series,
            NULL AS floorplan_code,
            snm.BoatDesc1 AS floorplan_desc,
            NULL AS length_feet,
            NULL AS length_str,
            NULL AS beam_length,
            NULL AS beam_str,
            NULL AS loa,
            NULL AS loa_str,
            NULL AS seats,
            NULL AS msrp,
            p_year AS year,
            NULL AS effective_date,
            d.dealerno AS dealer_id,
            d.dealer AS dealer_name,
            d.city,
            d.state,
            NOW() AS generated_date,
            'EOS' AS data_source
        FROM (SELECT 1) dummy
        LEFT JOIN warrantyparts.SerialNumberMaster snm
            ON snm.BoatItemNo = p_model_id
            AND snm.SerialModelYear = p_year
        LEFT JOIN warrantyparts.`dealermaster - use the one in eos` d
            ON d.dealerno = p_dealer_id
            AND d.productline = 'BEN'
        LIMIT 1;

        -- Result Set 2: Performance Specifications from EOS
        SELECT DISTINCT
            pps.PKG_NAME AS perf_package_id,
            pps.PKG_NAME AS package_name,
            CAST(REPLACE(pps.MAX_HP, ' HP', '') AS DECIMAL(10,2)) AS max_hp,
            NULL AS no_of_tubes,
            pps.CAP AS person_capacity,
            CAST(REPLACE(REPLACE(pps.WEIGHT, ' lbs', ''), ',', '') AS DECIMAL(10,2)) AS hull_weight,
            pps.PONT_GAUGE AS pontoon_gauge,
            pps.TRANSOM AS transom,
            NULL AS tube_height,
            NULL AS tube_center_to_center,
            NULL AS max_width,
            NULL AS fuel_capacity,
            NULL AS tube_length_str,
            NULL AS deck_length_str
        FROM Eos.perf_pkg_spec pps
        WHERE pps.MODEL LIKE CONCAT(v_base_model, '%')
          AND pps.STATUS = 'Active'
        ORDER BY pps.PKG_NAME;

        -- Result Set 3: Standard Features from EOS
        SET @year_suffix = p_year;
        SET @eos_standards_query = CONCAT('
            SELECT DISTINCT
                sm.CATEGORY AS area,
                sm.OPT_NAME AS description,
                0 AS sort_order
            FROM Eos.standards_matrix_', @year_suffix, ' sm
            WHERE sm.MODEL LIKE CONCAT(?, ''%'')
            ORDER BY sm.CATEGORY, sm.OPT_NAME
        ');

        PREPARE stmt FROM @eos_standards_query;
        SET @base_model_param = v_base_model;
        EXECUTE stmt USING @base_model_param;
        DEALLOCATE PREPARE stmt;

    END IF;

    -- Result Set 4: Included Options from Sales Database (same for both CPQ and EOS)
    SET @year_suffix = RIGHT(CAST(p_year AS CHAR), 2);
    SET @table_name = CONCAT('warrantyparts.BoatOptions', @year_suffix);

    SET @query = CONCAT('
        SELECT DISTINCT
            ItemNo,
            ItemDesc1 AS ItemDescription,
            QuantitySold AS Quantity,
            ExtSalesAmount AS SalePrice,
            ExtSalesAmount AS MSRP
        FROM ', @table_name, '
        WHERE BoatModelNo = ?
          AND ItemMasterProdCat = ''ACC''
          AND ItemNo IS NOT NULL
          AND ItemNo != ''''
          AND (
              ? IS NULL
              OR BoatSerialNo = ?
              OR ERP_OrderNo = ?
          )
        ORDER BY ItemDesc1
    ');

    PREPARE stmt FROM @query;
    SET @model_param = p_model_id;
    SET @identifier_param1 = p_identifier;
    SET @identifier_param2 = p_identifier;
    SET @identifier_param3 = p_identifier;
    EXECUTE stmt USING @model_param, @identifier_param1, @identifier_param2, @identifier_param3;
    DEALLOCATE PREPARE stmt;
END //

DELIMITER ;

-- ============================================================================
-- USAGE EXAMPLES
-- ============================================================================

/*

-- 1. CPQ Model (2025 data)
CALL GetWindowStickerData('25QXFBWA', '333836', 2025, NULL);

-- 2. EOS Model (backward compatibility for 2024)
CALL GetWindowStickerData('168SFSR', '166000', 2024, NULL);

-- 3. Specific boat by HIN
CALL GetWindowStickerData('168SFSR', '166000', 2024, 'ETWR6364F425');

-- 4. Specific boat by order number
CALL GetWindowStickerData('25QXFBWA', '333836', 2025, 'SO00920503');

*/

-- ============================================================================
-- END OF STORED PROCEDURES
-- ============================================================================

-- ============================================================================
-- Bennington CPQ - Stored Procedures with Unified Dealer Margin Lookup
-- ============================================================================
-- Purpose: SQL-driven window sticker and quote generation
-- Features:
--   - Unified dealer margin lookup (DealerQuotes + DealerMargins)
--   - CPQ/EOS backward compatibility
--   - Complete MSRP calculation with dealer costs
-- ============================================================================

USE warrantyparts_test;

-- Drop existing procedures
DROP PROCEDURE IF EXISTS GetDealerMargins;
DROP PROCEDURE IF EXISTS CalculateMSRP;
DROP PROCEDURE IF EXISTS GetWindowStickerWithPricing;
DROP PROCEDURE IF EXISTS GetIncludedOptions;
DROP PROCEDURE IF EXISTS GetWindowStickerData;

DELIMITER //

-- ============================================================================
-- Procedure: GetDealerMargins
-- ============================================================================
-- Unified dealer margin lookup - checks both DealerQuotes and DealerMargins
--
-- Parameters:
--   p_dealer_id: Dealer ID (handles both int 333836 and varchar '00333836')
--   p_series_id: Series ID (e.g., 'Q', 'QX', 'SV_23', 'SV 23')
--
-- Returns:
--   base_boat_margin_pct    - Base boat margin percentage
--   engine_margin_pct       - Engine margin percentage
--   options_margin_pct      - Options margin percentage
--   freight_type           - 'FIXED' or 'PERCENTAGE'
--   freight_value          - Dollar amount or percentage
--   prep_type              - 'FIXED' or 'PERCENTAGE'
--   prep_value             - Dollar amount or percentage
--   volume_discount_pct    - Volume discount percentage
--   data_source            - 'DealerQuotes' or 'DealerMargins'

CREATE PROCEDURE GetDealerMargins(
    IN p_dealer_id VARCHAR(20),
    IN p_series_id VARCHAR(10)
)
BEGIN
    DECLARE v_dealer_int INT;
    DECLARE v_dealer_varchar VARCHAR(20);
    DECLARE v_series_normalized VARCHAR(20);
    DECLARE v_found INT DEFAULT 0;

    -- Normalize dealer ID - handle both formats
    SET v_dealer_int = CAST(p_dealer_id AS UNSIGNED);
    SET v_dealer_varchar = LPAD(CAST(v_dealer_int AS CHAR), 8, '0');

    -- Normalize series ID - handle 'SV 23' vs 'SV_23'
    SET v_series_normalized = REPLACE(p_series_id, ' ', '_');

    -- Try DealerQuotes first (PRODUCTION TABLE)
    SET @base_margin = NULL;
    SET @series_col_prefix = CONCAT(v_series_normalized, '_');

    -- Build dynamic query to get margins from DealerQuotes wide table
    SET @query = CONCAT('
        SELECT
            ', @series_col_prefix, 'BASE_BOAT,
            ', @series_col_prefix, 'ENGINE,
            ', @series_col_prefix, 'OPTIONS,
            ', @series_col_prefix, 'FREIGHT,
            ', @series_col_prefix, 'PREP,
            ', @series_col_prefix, 'VOL_DISC,
            ''FIXED'' as freight_type,
            ''FIXED'' as prep_type,
            ''DealerQuotes'' as data_source
        FROM DealerQuotes
        WHERE DealerID = ', v_dealer_int, '
        LIMIT 1
    ');

    -- Try to execute DealerQuotes query
    SET @result_found = 0;

    -- Create temp table for results
    DROP TEMPORARY TABLE IF EXISTS temp_margins;
    CREATE TEMPORARY TABLE temp_margins (
        base_boat_margin_pct DECIMAL(10,2),
        engine_margin_pct DECIMAL(10,2),
        options_margin_pct DECIMAL(10,2),
        freight_value DECIMAL(10,2),
        prep_value DECIMAL(10,2),
        volume_discount_pct DECIMAL(10,2),
        freight_type VARCHAR(20),
        prep_type VARCHAR(20),
        data_source VARCHAR(50)
    );

    -- Try DealerQuotes
    BEGIN
        DECLARE CONTINUE HANDLER FOR SQLEXCEPTION SET @result_found = 0;

        SET @insert_query = CONCAT('INSERT INTO temp_margins ', @query);
        PREPARE stmt FROM @insert_query;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;

        SELECT COUNT(*) INTO @result_found FROM temp_margins;
    END;

    -- If not found in DealerQuotes, try DealerMargins (CPQ)
    IF @result_found = 0 THEN
        INSERT INTO temp_margins
        SELECT
            base_boat_margin,
            engine_margin,
            options_margin,
            freight_margin,
            prep_margin,
            volume_discount,
            'PERCENTAGE' as freight_type,
            'PERCENTAGE' as prep_type,
            'DealerMargins' as data_source
        FROM DealerMargins
        WHERE (dealer_id = v_dealer_varchar OR dealer_id = CAST(v_dealer_int AS CHAR))
          AND (series_id = p_series_id OR series_id = v_series_normalized)
          AND end_date IS NULL
        LIMIT 1;
    END IF;

    -- Return results
    SELECT * FROM temp_margins;

    -- Cleanup
    DROP TEMPORARY TABLE IF EXISTS temp_margins;
END //

-- ============================================================================
-- Procedure: CalculateMSRP
-- ============================================================================
-- Calculates MSRP and dealer cost from BoatOptions data
--
-- Parameters:
--   p_identifier: HIN, Model, or Serial Number
--   p_year: Year to lookup BoatOptions table
--   p_dealer_id: Dealer ID for margin lookup
--   p_series_id: Series ID for margin lookup
--
-- Returns:
--   Component-level breakdown with dealer costs

CREATE PROCEDURE CalculateMSRP(
    IN p_identifier VARCHAR(30),
    IN p_year INT,
    IN p_dealer_id VARCHAR(20),
    IN p_series_id VARCHAR(10)
)
BEGIN
    DECLARE v_base_msrp DECIMAL(10,2) DEFAULT 0;
    DECLARE v_engine_msrp DECIMAL(10,2) DEFAULT 0;
    DECLARE v_options_msrp DECIMAL(10,2) DEFAULT 0;
    DECLARE v_freight_msrp DECIMAL(10,2) DEFAULT 0;
    DECLARE v_prep_msrp DECIMAL(10,2) DEFAULT 0;

    -- Determine BoatOptions table
    SET @year_suffix = RIGHT(CAST(p_year AS CHAR), 2);
    SET @table_name = CONCAT('warrantyparts.BoatOptions', @year_suffix);

    -- Calculate component MSRPs
    SET @calc_query = CONCAT('
        SELECT
            COALESCE(SUM(CASE WHEN ItemMasterProdCat = ''BS1'' THEN ExtSalesAmount END), 0),
            COALESCE(SUM(CASE WHEN ItemMasterProdCat = ''EN7'' THEN ExtSalesAmount END), 0),
            COALESCE(SUM(CASE WHEN ItemMasterProdCat = ''ACC'' THEN ExtSalesAmount END), 0),
            0,  -- freight placeholder
            0   -- prep placeholder
        FROM ', @table_name, '
        WHERE (BoatSerialNo = ? OR BoatModelNo = ?)
    ');

    PREPARE stmt FROM @calc_query;
    EXECUTE stmt USING p_identifier, p_identifier;
    DEALLOCATE PREPARE stmt;

    -- Store results in temp table
    DROP TEMPORARY TABLE IF EXISTS temp_msrp;
    CREATE TEMPORARY TABLE temp_msrp (
        base_msrp DECIMAL(10,2),
        engine_msrp DECIMAL(10,2),
        options_msrp DECIMAL(10,2),
        freight_msrp DECIMAL(10,2),
        prep_msrp DECIMAL(10,2)
    );

    SET @insert_calc = CONCAT('INSERT INTO temp_msrp ', @calc_query);
    PREPARE stmt FROM @insert_calc;
    EXECUTE stmt USING p_identifier, p_identifier;
    DEALLOCATE PREPARE stmt;

    -- Get dealer margins
    DROP TEMPORARY TABLE IF EXISTS temp_dealer_margins;
    CREATE TEMPORARY TABLE temp_dealer_margins AS
    SELECT * FROM (
        SELECT 1 as dummy
    ) x LIMIT 0;

    -- Call GetDealerMargins to get margin info
    CALL GetDealerMargins(p_dealer_id, p_series_id);

    -- Calculate dealer costs and return combined results
    SELECT
        m.base_msrp,
        m.engine_msrp,
        m.options_msrp,
        m.freight_msrp,
        m.prep_msrp,
        (m.base_msrp + m.engine_msrp + m.options_msrp + m.freight_msrp + m.prep_msrp) as total_msrp,

        -- Note: Dealer margins will be in a separate result set from GetDealerMargins
        -- This procedure focuses on MSRP calculation

        'MSRP Breakdown' as note
    FROM temp_msrp m;

    -- Cleanup
    DROP TEMPORARY TABLE IF EXISTS temp_msrp;
END //

-- ============================================================================
-- Procedure: GetIncludedOptions
-- ============================================================================
-- Gets included options/accessories for a specific model or boat
--
-- Parameters:
--   p_identifier: Model ID, HIN, or Serial Number
--   p_year: Year to determine BoatOptions table

CREATE PROCEDURE GetIncludedOptions(
    IN p_identifier VARCHAR(30),
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
        WHERE (BoatModelNo = ? OR BoatSerialNo = ?)
          AND ItemMasterProdCat = ''ACC''
          AND ItemNo IS NOT NULL
          AND ItemNo != ''''
        ORDER BY ItemDesc1
    ');

    PREPARE stmt FROM @query;
    EXECUTE stmt USING p_identifier, p_identifier;
    DEALLOCATE PREPARE stmt;
END //

-- ============================================================================
-- Procedure: GetWindowStickerData
-- ============================================================================
-- Gets complete window sticker data with MSRP and dealer costs
-- WITH EOS FALLBACK for backward compatibility
--
-- Parameters:
--   p_model_id: Model ID (e.g., '25QXFBWA' or '168SFSR')
--   p_dealer_id: Dealer ID (e.g., '333836')
--   p_year: Model year (e.g., 2025)
--   p_identifier: Optional HIN or Order Number to filter specific boat
--
-- Returns 5 result sets:
--   1. Model basic info with pricing
--   2. Performance specifications
--   3. Standard features by area
--   4. Included options from sales database
--   5. Dealer margins and cost breakdown

CREATE PROCEDURE GetWindowStickerData(
    IN p_model_id VARCHAR(20),
    IN p_dealer_id VARCHAR(20),
    IN p_year INT,
    IN p_identifier VARCHAR(30)
)
BEGIN
    DECLARE v_cpq_exists INT DEFAULT 0;
    DECLARE v_base_model VARCHAR(20);
    DECLARE v_series_id VARCHAR(10);

    -- Check if model exists in CPQ
    SELECT COUNT(*) INTO v_cpq_exists
    FROM Models
    WHERE model_id = p_model_id;

    IF v_cpq_exists > 0 THEN
        -- ===== CPQ PATH =====

        -- Get series_id for margin lookup
        SELECT series_id INTO v_series_id FROM Models WHERE model_id = p_model_id LIMIT 1;

        -- Result Set 1: Model Information with Pricing from CPQ
        SELECT
            m.model_id,
            m.model_name,
            m.series_id,
            s.series_name,
            s.parent_series,
            m.floorplan_desc,
            m.length_feet,
            m.length_str,
            m.beam_str,
            m.loa_str,
            m.seats,
            p.msrp,
            p.year AS price_year,
            d.dealer AS dealer_name,
            d.city AS dealer_city,
            d.state AS dealer_state,
            'CPQ' AS data_source
        FROM Models m
        JOIN Series s ON m.series_id = s.series_id
        LEFT JOIN ModelPricing p ON m.model_id = p.model_id AND p.end_date IS NULL AND p.year = p_year
        LEFT JOIN warrantyparts.`dealermaster - use the one in eos` d
            ON d.dealerno = CAST(p_dealer_id AS UNSIGNED)
            AND d.productline = 'BEN'
        WHERE m.model_id = p_model_id;

        -- Result Set 2: Performance Specifications
        SELECT DISTINCT
            mp.perf_package_id,
            pp.package_name,
            mp.max_hp,
            mp.no_of_tubes,
            mp.person_capacity,
            mp.hull_weight,
            mp.pontoon_gauge,
            mp.transom,
            mp.fuel_capacity
        FROM ModelPerformance mp
        JOIN PerformancePackages pp ON mp.perf_package_id = pp.perf_package_id
        WHERE mp.model_id = p_model_id
          AND mp.year = p_year
        ORDER BY mp.perf_package_id;

        -- Result Set 3: Standard Features
        SELECT DISTINCT
            sf.area,
            sf.description
        FROM ModelStandardFeatures msf
        JOIN StandardFeatures sf ON msf.feature_id = sf.feature_id
        WHERE msf.model_id = p_model_id
          AND msf.year = p_year
        ORDER BY sf.area, sf.sort_order;

        -- Result Set 4: Included Options
        CALL GetIncludedOptions(COALESCE(p_identifier, p_model_id), p_year);

        -- Result Set 5: Dealer Margins and Pricing
        CALL GetDealerMargins(p_dealer_id, v_series_id);

    ELSE
        -- ===== EOS FALLBACK PATH =====

        -- Extract base model (remove SR, SE, SA suffixes)
        SET v_base_model = REGEXP_REPLACE(p_model_id, '(SR|SE|SA|23SR|23SE)$', '');

        -- Try to get series from SerialNumberMaster or model pattern
        SELECT DISTINCT Series INTO v_series_id
        FROM warrantyparts.SerialNumberMaster
        WHERE BoatItemNo LIKE CONCAT(v_base_model, '%')
        LIMIT 1;

        -- If not found, try to extract from model name
        IF v_series_id IS NULL THEN
            -- Extract series from model pattern (e.g., 168SF -> S, 20SV -> SV)
            SET v_series_id = REGEXP_REPLACE(p_model_id, '^[0-9]+([A-Z]+).*$', '$1');
        END IF;

        -- Result Set 1: Model Information from EOS
        SELECT DISTINCT
            p_model_id AS model_id,
            NULL AS model_name,
            v_series_id AS series_id,
            NULL AS series_name,
            NULL AS parent_series,
            BoatDesc1 AS floorplan_desc,
            NULL AS length_feet,
            NULL AS length_str,
            NULL AS beam_str,
            NULL AS loa_str,
            NULL AS seats,
            NULL AS msrp,
            p_year AS price_year,
            d.dealer AS dealer_name,
            d.city AS dealer_city,
            d.state AS dealer_state,
            'EOS' AS data_source
        FROM warrantyparts.SerialNumberMaster sm
        LEFT JOIN warrantyparts.`dealermaster - use the one in eos` d
            ON d.dealerno = CAST(p_dealer_id AS UNSIGNED)
            AND d.productline = 'BEN'
        WHERE sm.BoatItemNo LIKE CONCAT(v_base_model, '%')
        LIMIT 1;

        -- Result Set 2: Performance from EOS
        SELECT DISTINCT
            perf_pack AS perf_package_id,
            perf_pack AS package_name,
            max_hp,
            no_of_tubes,
            person_capacity,
            hull_weight,
            pontoon_gauge,
            transom,
            fuel_capacity
        FROM Eos.perf_pkg_spec
        WHERE model LIKE CONCAT(v_base_model, '%')
        ORDER BY perf_pack;

        -- Result Set 3: Standard Features from EOS
        SET @standards_table = CONCAT('Eos.standards_matrix_', p_year);
        SET @standards_query = CONCAT('
            SELECT DISTINCT
                Area AS area,
                Description AS description
            FROM ', @standards_table, '
            WHERE Model LIKE CONCAT(?, ''%'')
              AND Value = ''S''
            ORDER BY Area, Description
        ');

        PREPARE stmt FROM @standards_query;
        EXECUTE stmt USING v_base_model;
        DEALLOCATE PREPARE stmt;

        -- Result Set 4: Included Options
        CALL GetIncludedOptions(COALESCE(p_identifier, p_model_id), p_year);

        -- Result Set 5: Dealer Margins
        CALL GetDealerMargins(p_dealer_id, v_series_id);

    END IF;
END //

DELIMITER ;

-- ============================================================================
-- Test Queries
-- ============================================================================

/*

-- Test 1: Get dealer margins for NICHOLS MARINE - NORMAN (SV_23 series)
CALL GetDealerMargins('333836', 'SV_23');
CALL GetDealerMargins('333836', 'SV 23');  -- Should work with space too

-- Test 2: Get dealer margins with leading zeros
CALL GetDealerMargins('00333836', 'Q');

-- Test 3: Get window sticker for CPQ model
CALL GetWindowStickerData('25QXFBWA', '333836', 2025, NULL);

-- Test 4: Get window sticker for EOS model with specific boat
CALL GetWindowStickerData('20SVFSR', '333836', 2024, 'ETWP6278J324');

-- Test 5: Calculate MSRP for specific boat
CALL CalculateMSRP('ETWP6278J324', 2024, '333836', 'SV_23');

-- Test 6: Get included options
CALL GetIncludedOptions('ETWP6278J324', 2024);

*/

-- ============================================================================
-- END OF STORED PROCEDURES
-- ============================================================================

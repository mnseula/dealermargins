-- ============================================================================
-- Bennington CPQ - Stored Procedures
-- ============================================================================
-- Purpose: SQL-driven window sticker generation and dealer pricing
-- All procedures READ from BoatOptions25_test (no modifications)
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
-- Reads from BoatOptions25_test where ItemMasterProdCat = 'ACC'

CREATE PROCEDURE GetIncludedOptions(
    IN p_model_id VARCHAR(20)
)
BEGIN
    SELECT DISTINCT
        ItemNo,
        ItemDesc1 AS ItemDescription,
        QuantitySold AS Quantity,
        ExtSalesAmount AS SalePrice,
        ExtSalesAmount AS MSRP  -- For now, assuming MSRP = SalePrice
    FROM BoatOptions25_test
    WHERE BoatModelNo = p_model_id
      AND ItemMasterProdCat = 'ACC'
      AND ItemNo IS NOT NULL
      AND ItemNo != ''
    ORDER BY ItemDesc1;
END //

-- ============================================================================
-- Procedure: GetWindowStickerData
-- ============================================================================
-- Gets complete window sticker data for a model
-- Parameters:
--   p_model_id: Model ID (e.g., '25QXFBWA' or '22SVSR')
--   p_dealer_id: Dealer ID (e.g., '00333836')
--   p_year: Model year (e.g., 2024, 2025, 2026)
--   p_identifier: HIN (Hull ID) or Order Number to filter specific boat (e.g., 'ETWP1438F324')
-- Returns multiple result sets:
--   1. Model basic info with pricing (from CPQ Models/ModelPricing)
--   2. Performance specifications (from CPQ ModelPerformance/PerformancePackages)
--   3. Standard features by area (from CPQ StandardFeatures/ModelStandardFeatures)
--   4. ALL boat items with pricing (from BoatOptions{year} - boats, engines, options, everything)

CREATE PROCEDURE GetWindowStickerData(
    IN p_model_id VARCHAR(20),
    IN p_dealer_id VARCHAR(20),
    IN p_year INT,
    IN p_identifier VARCHAR(30)
)
BEGIN
    -- Result Set 1: Model Information with Pricing for Specified Year
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
        m.image_link,
        m.tube_length_str,
        m.deck_length_str,
        m.engine_configuration,
        p.msrp,
        p.year,
        p.effective_date,
        d.dealerno AS dealer_id,
        d.dealer AS dealer_name,
        d.city,
        d.state,
        NOW() AS generated_date
    FROM Models m
    JOIN Series s ON m.series_id = s.series_id
    LEFT JOIN ModelPricing p ON m.model_id = p.model_id
        AND p.year = p_year
        AND p.end_date IS NULL
    LEFT JOIN warrantyparts.`dealermaster - use the one in eos` d
        ON d.dealerno = p_dealer_id
        AND d.productline = 'BEN'
    WHERE m.model_id = p_model_id;

    -- Result Set 2: Performance Specifications for Specified Year
    -- If identifier provided, filter to configured package for that boat
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

    -- Result Set 3: Standard Features for Specified Year (organized by area)
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

    -- Result Set 4: Included Options from Sales Database (read-only)
    -- EXCLUDES boat items (BS1/BOA) to prevent double-counting - base boat MSRP comes from Models table
    -- If identifier provided, filter to that specific boat
    -- Query production database - dynamically select BoatOptions table based on year
    -- Year 2024 → BoatOptions24, Year 2025 → BoatOptions25, Year 2026 → BoatOptions26

    SET @year_suffix = RIGHT(CAST(p_year AS CHAR), 2);
    SET @table_name = CONCAT('warrantyparts.BoatOptions', @year_suffix);

    SET @query = CONCAT('
        SELECT
            ItemNo,
            ItemDesc1 AS ItemDescription,
            QuantitySold AS Quantity,
            ExtSalesAmount AS SalePrice,
            ExtSalesAmount AS MSRP,
            MCTDesc,
            ItemMasterMCT
        FROM ', @table_name, '
        WHERE ItemNo IS NOT NULL
          AND ItemNo != ''''
          AND ItemMasterProdCat NOT IN (''BS1'', ''BOA'')
          AND (
              (? IS NULL AND BoatModelNo = ?)
              OR BoatSerialNo = ?
              OR ERP_OrderNo = ?
          )
        ORDER BY
            CASE MCTDesc
                WHEN ''PONTOONS'' THEN 1
                WHEN ''Pontoon Boats OB'' THEN 1
                WHEN ''ENGINES'' THEN 2
                WHEN ''Engine'' THEN 2
                WHEN ''PRE-RIG'' THEN 3
                WHEN ''Prerig'' THEN 3
                ELSE 4
            END,
            ExtSalesAmount DESC,
            ItemDesc1
    ');

    PREPARE stmt FROM @query;
    SET @identifier_param1 = p_identifier;
    SET @model_param = p_model_id;
    SET @identifier_param2 = p_identifier;
    SET @identifier_param3 = p_identifier;
    EXECUTE stmt USING @identifier_param1, @model_param, @identifier_param2, @identifier_param3;
    DEALLOCATE PREPARE stmt;
END //

-- ============================================================================
-- Procedure: CalculateDealerQuote
-- ============================================================================
-- Calculates complete dealer quote with margins applied
-- Returns: Base price, options, dealer costs, margins, final totals

CREATE PROCEDURE CalculateDealerQuote(
    IN p_model_id VARCHAR(20),
    IN p_dealer_id VARCHAR(20),
    IN p_engine_msrp DECIMAL(10,2),
    IN p_freight DECIMAL(10,2),
    IN p_prep DECIMAL(10,2)
)
BEGIN
    DECLARE v_base_msrp DECIMAL(10,2);
    DECLARE v_series_id VARCHAR(10);
    DECLARE v_base_margin DECIMAL(5,2);
    DECLARE v_engine_margin DECIMAL(5,2);
    DECLARE v_options_margin DECIMAL(5,2);
    DECLARE v_freight_margin DECIMAL(5,2);
    DECLARE v_prep_margin DECIMAL(5,2);
    DECLARE v_options_total DECIMAL(10,2) DEFAULT 0.00;

    -- Get model MSRP and series
    SELECT p.msrp, m.series_id
    INTO v_base_msrp, v_series_id
    FROM Models m
    JOIN ModelPricing p ON m.model_id = p.model_id AND p.end_date IS NULL
    WHERE m.model_id = p_model_id;

    -- Get dealer margins
    SELECT
        base_boat_margin,
        engine_margin,
        options_margin,
        freight_margin,
        prep_margin
    INTO
        v_base_margin,
        v_engine_margin,
        v_options_margin,
        v_freight_margin,
        v_prep_margin
    FROM DealerMargins
    WHERE dealer_id = p_dealer_id
      AND series_id = v_series_id
      AND end_date IS NULL
    LIMIT 1;

    -- Calculate options total from sales database (read-only)
    SELECT COALESCE(SUM(ExtSalesAmount), 0)
    INTO v_options_total
    FROM BoatOptions25_test
    WHERE BoatModelNo = p_model_id
      AND ItemMasterProdCat = 'ACC'
      AND ExtSalesAmount IS NOT NULL;

    -- Return complete quote breakdown
    SELECT
        p_model_id AS model_id,
        p_dealer_id AS dealer_id,

        -- Base Boat
        v_base_msrp AS base_msrp,
        v_base_margin AS base_margin_pct,
        ROUND(v_base_msrp * (1 - v_base_margin / 100), 2) AS base_dealer_cost,
        ROUND(v_base_msrp * (v_base_margin / 100), 2) AS base_savings,

        -- Engine
        p_engine_msrp AS engine_msrp,
        v_engine_margin AS engine_margin_pct,
        ROUND(p_engine_msrp * (1 - v_engine_margin / 100), 2) AS engine_dealer_cost,
        ROUND(p_engine_msrp * (v_engine_margin / 100), 2) AS engine_savings,

        -- Options
        v_options_total AS options_msrp,
        v_options_margin AS options_margin_pct,
        ROUND(v_options_total * (1 - v_options_margin / 100), 2) AS options_dealer_cost,
        ROUND(v_options_total * (v_options_margin / 100), 2) AS options_savings,

        -- Freight
        p_freight AS freight_msrp,
        v_freight_margin AS freight_margin_pct,
        ROUND(p_freight * (1 - v_freight_margin / 100), 2) AS freight_dealer_cost,
        ROUND(p_freight * (v_freight_margin / 100), 2) AS freight_savings,

        -- Prep
        p_prep AS prep_msrp,
        v_prep_margin AS prep_margin_pct,
        ROUND(p_prep * (1 - v_prep_margin / 100), 2) AS prep_dealer_cost,
        ROUND(p_prep * (v_prep_margin / 100), 2) AS prep_savings,

        -- Totals
        ROUND(v_base_msrp + p_engine_msrp + v_options_total + p_freight + p_prep, 2) AS total_msrp,
        ROUND(
            (v_base_msrp * (1 - v_base_margin / 100)) +
            (p_engine_msrp * (1 - v_engine_margin / 100)) +
            (v_options_total * (1 - v_options_margin / 100)) +
            (p_freight * (1 - v_freight_margin / 100)) +
            (p_prep * (1 - v_prep_margin / 100)),
            2
        ) AS total_dealer_cost,
        ROUND(
            (v_base_msrp * (v_base_margin / 100)) +
            (p_engine_msrp * (v_engine_margin / 100)) +
            (v_options_total * (v_options_margin / 100)) +
            (p_freight * (v_freight_margin / 100)) +
            (p_prep * (v_prep_margin / 100)),
            2
        ) AS total_savings;
END //

-- ============================================================================
-- Procedure: GetModelFullDetails
-- ============================================================================
-- Gets comprehensive model information for quote/window sticker
-- Includes: Model info, current price, performance specs, features, dealer margins

CREATE PROCEDURE GetModelFullDetails(
    IN p_model_id VARCHAR(20),
    IN p_dealer_id VARCHAR(20)
)
BEGIN
    -- Model info with pricing
    SELECT
        m.*,
        s.series_name,
        s.parent_series,
        p.msrp,
        p.effective_date,
        p.year
    FROM Models m
    JOIN Series s ON m.series_id = s.series_id
    LEFT JOIN ModelPricing p ON m.model_id = p.model_id AND p.end_date IS NULL
    WHERE m.model_id = p_model_id;

    -- Performance data
    SELECT
        mp.*,
        pp.package_name
    FROM ModelPerformance mp
    JOIN PerformancePackages pp ON mp.perf_package_id = pp.perf_package_id
    WHERE mp.model_id = p_model_id;

    -- Standard features
    SELECT
        sf.area,
        sf.description,
        sf.sort_order
    FROM ModelStandardFeatures msf
    JOIN StandardFeatures sf ON msf.feature_id = sf.feature_id
    WHERE msf.model_id = p_model_id
      AND sf.active = TRUE
    ORDER BY sf.area, sf.sort_order;

    -- Dealer margins (if dealer specified)
    IF p_dealer_id IS NOT NULL THEN
        SELECT
            dm.*,
            d.dealer_name
        FROM DealerMargins dm
        JOIN Dealers d ON dm.dealer_id = d.dealer_id
        WHERE dm.dealer_id = p_dealer_id
          AND dm.series_id = (SELECT series_id FROM Models WHERE model_id = p_model_id)
          AND dm.end_date IS NULL;
    END IF;

    -- Included options from sales database (read-only)
    SELECT DISTINCT
        ItemNo,
        ItemDesc1 AS ItemDescription,
        QuantitySold AS Quantity,
        ExtSalesAmount AS Amount
    FROM BoatOptions25_test
    WHERE BoatModelNo = p_model_id
      AND ItemMasterProdCat = 'ACC'
      AND ItemNo IS NOT NULL
      AND ItemNo != ''
    ORDER BY ItemDesc1;
END //

DELIMITER ;

-- ============================================================================
-- USAGE EXAMPLES
-- ============================================================================

/*

-- 1. Get included options for a model
CALL GetIncludedOptions('25QXFBWA');

-- 2. Get complete window sticker data (all performance packages)
CALL GetWindowStickerData('25QXFBWA', '00333836', 2025, NULL);

-- 2b. Get window sticker for specific boat by order number
CALL GetWindowStickerData('25QXFBWA', '00333836', 2025, 'SO00935977');

-- 3. Calculate dealer quote with margins
CALL CalculateDealerQuote(
    '25QXFBWA',     -- model_id
    '00333836',     -- dealer_id
    15000.00,       -- engine_msrp
    2000.00,        -- freight
    1500.00         -- prep
);

-- 4. Get all model details including dealer margins
CALL GetModelFullDetails('25QXFBWA', '00333836');

-- 5. Get model details without dealer info
CALL GetModelFullDetails('25QXFBWA', NULL);

*/

-- ============================================================================
-- END OF STORED PROCEDURES
-- ============================================================================

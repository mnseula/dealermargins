-- Quick reload script for GetWindowStickerData procedure
-- Run this after updating the stored procedure definition

USE warrantyparts_test;

-- Drop the existing procedure
DROP PROCEDURE IF EXISTS GetWindowStickerData;

DELIMITER //

-- ============================================================================
-- Procedure: GetWindowStickerData
-- ============================================================================
-- Gets complete window sticker data for a model
-- Parameters:
--   p_model_id: Model ID (e.g., '25QXFBWA')
--   p_dealer_id: Dealer ID (e.g., '00333836')
--   p_year: Model year (e.g., 2025)
--   p_identifier: Optional HIN or Order Number to filter specific boat (NULL for all)
-- Returns multiple result sets:
--   1. Model basic info with pricing
--   2. Performance specifications (filtered by identifier if provided)
--   3. Standard features by area
--   4. Included options from sales database (filtered by identifier if provided)

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
        p.msrp,
        p.year,
        p.effective_date,
        d.dealer_id,
        d.dealer_name,
        d.city,
        d.state,
        NOW() AS generated_date
    FROM Models m
    JOIN Series s ON m.series_id = s.series_id
    LEFT JOIN ModelPricing p ON m.model_id = p.model_id
        AND p.year = p_year
        AND p.end_date IS NULL
    LEFT JOIN Dealers d ON d.dealer_id = p_dealer_id
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
    -- If identifier provided, filter to that specific boat
    -- Query production database - dynamically select BoatOptions table based on year
    -- Year 2024 → BoatOptions24, Year 2025 → BoatOptions25, Year 2026 → BoatOptions26

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

-- Test the procedure
SELECT 'GetWindowStickerData procedure reloaded successfully!' AS Status;

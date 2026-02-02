-- ============================================================================
-- Unified Dealer Margin Lookup - Handles DealerQuotes AND DealerMargins
-- ============================================================================
-- Purpose: Single function to get dealer margins from either table
-- Handles:
--   - DealerQuotes (wide table, int DealerID, fixed $ freight/prep)
--   - DealerMargins (normalized, VARCHAR DealerID, % freight/prep)
--   - Series name variations (SV_23 vs SV 23)
-- ============================================================================

USE warrantyparts_test;

DROP FUNCTION IF EXISTS GetSeriesColumnPrefix;
DROP PROCEDURE IF EXISTS GetDealerMargins;

DELIMITER //

-- ============================================================================
-- Function: GetSeriesColumnPrefix
-- ============================================================================
-- Maps series ID to DealerQuotes column prefix
-- Handles variations: 'SV 23' -> 'SV_23_', 'Q' -> 'Q_', etc.

CREATE FUNCTION GetSeriesColumnPrefix(p_series VARCHAR(20))
RETURNS VARCHAR(30)
DETERMINISTIC
BEGIN
    DECLARE v_prefix VARCHAR(30);

    -- Normalize series (replace spaces with underscores)
    SET v_prefix = REPLACE(TRIM(p_series), ' ', '_');

    -- Add trailing underscore
    SET v_prefix = CONCAT(v_prefix, '_');

    RETURN v_prefix;
END //

-- ============================================================================
-- Procedure: GetDealerMargins
-- ============================================================================
-- Unified dealer margin lookup with fallback logic
--
-- Parameters:
--   p_dealer_id VARCHAR(20) - Dealer ID (handles '333836' or '00333836')
--   p_series_id VARCHAR(20) - Series ID ('Q', 'SV_23', 'SV 23', etc.)
--
-- Returns single result set:
--   dealer_id              - Normalized dealer ID
--   dealer_name            - Dealer name
--   series_id              - Series ID
--   base_boat_margin_pct   - Base boat margin %
--   engine_margin_pct      - Engine margin %
--   options_margin_pct     - Options margin %
--   freight_type           - 'FIXED_AMOUNT' or 'PERCENTAGE'
--   freight_value          - Dollar amount or percentage
--   prep_type              - 'FIXED_AMOUNT' or 'PERCENTAGE'
--   prep_value             - Dollar amount or percentage
--   volume_discount_pct    - Volume discount %
--   data_source            - 'DealerQuotes' or 'DealerMargins'

CREATE PROCEDURE GetDealerMargins(
    IN p_dealer_id VARCHAR(20),
    IN p_series_id VARCHAR(20)
)
BEGIN
    DECLARE v_dealer_int INT;
    DECLARE v_series_normalized VARCHAR(20);
    DECLARE v_col_prefix VARCHAR(30);

    -- Normalize inputs
    SET v_dealer_int = CAST(TRIM(p_dealer_id) AS UNSIGNED);
    SET v_series_normalized = REPLACE(TRIM(p_series_id), ' ', '_');
    SET v_col_prefix = GetSeriesColumnPrefix(p_series_id);

    -- Try DealerQuotes first (PRODUCTION)
    -- Use CASE to safely extract columns even if some are NULL
    SET @sql = CONCAT('
        SELECT
            CAST(DealerID AS CHAR) as dealer_id,
            Dealership as dealer_name,
            ''', v_series_normalized, ''' as series_id,
            COALESCE(', v_col_prefix, 'BASE_BOAT, 0) as base_boat_margin_pct,
            COALESCE(', v_col_prefix, 'ENGINE, 0) as engine_margin_pct,
            COALESCE(', v_col_prefix, 'OPTIONS, 0) as options_margin_pct,
            ''FIXED_AMOUNT'' as freight_type,
            COALESCE(', v_col_prefix, 'FREIGHT, 0) as freight_value,
            ''FIXED_AMOUNT'' as prep_type,
            COALESCE(', v_col_prefix, 'PREP, 0) as prep_value,
            COALESCE(', v_col_prefix, 'VOL_DISC, 0) as volume_discount_pct,
            ''DealerQuotes'' as data_source
        FROM DealerQuotes
        WHERE DealerID = ', v_dealer_int
    );

    -- Execute query
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;

    -- If DealerQuotes returns no rows, fallback to DealerMargins
    -- (This will be handled by checking ROW_COUNT in calling code)

END //

-- ============================================================================
-- Alternative: GetDealerMarginsWithFallback
-- ============================================================================
-- Version that checks both tables and returns whichever has data

CREATE PROCEDURE GetDealerMarginsWithFallback(
    IN p_dealer_id VARCHAR(20),
    IN p_series_id VARCHAR(20)
)
BEGIN
    DECLARE v_dealer_int INT;
    DECLARE v_dealer_varchar VARCHAR(20);
    DECLARE v_series_normalized VARCHAR(20);
    DECLARE v_col_prefix VARCHAR(30);
    DECLARE v_found INT DEFAULT 0;

    -- Normalize inputs
    SET v_dealer_int = CAST(TRIM(p_dealer_id) AS UNSIGNED);
    SET v_dealer_varchar = LPAD(CAST(v_dealer_int AS CHAR), 8, '0');
    SET v_series_normalized = REPLACE(TRIM(p_series_id), ' ', '_');
    SET v_col_prefix = GetSeriesColumnPrefix(p_series_id);

    -- Create temp table for results
    DROP TEMPORARY TABLE IF EXISTS temp_dealer_margins;
    CREATE TEMPORARY TABLE temp_dealer_margins (
        dealer_id VARCHAR(20),
        dealer_name VARCHAR(200),
        series_id VARCHAR(20),
        base_boat_margin_pct DECIMAL(10,2),
        engine_margin_pct DECIMAL(10,2),
        options_margin_pct DECIMAL(10,2),
        freight_type VARCHAR(20),
        freight_value DECIMAL(10,2),
        prep_type VARCHAR(20),
        prep_value DECIMAL(10,2),
        volume_discount_pct DECIMAL(10,2),
        data_source VARCHAR(50)
    );

    -- Try DealerQuotes first
    SET @sql = CONCAT('
        INSERT INTO temp_dealer_margins
        SELECT
            CAST(DealerID AS CHAR),
            Dealership,
            ''', v_series_normalized, ''',
            COALESCE(', v_col_prefix, 'BASE_BOAT, 0),
            COALESCE(', v_col_prefix, 'ENGINE, 0),
            COALESCE(', v_col_prefix, 'OPTIONS, 0),
            ''FIXED_AMOUNT'',
            COALESCE(', v_col_prefix, 'FREIGHT, 0),
            ''FIXED_AMOUNT'',
            COALESCE(', v_col_prefix, 'PREP, 0),
            COALESCE(', v_col_prefix, 'VOL_DISC, 0),
            ''DealerQuotes''
        FROM DealerQuotes
        WHERE DealerID = ', v_dealer_int, '
        LIMIT 1
    ');

    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;

    -- Check if we found data
    SELECT COUNT(*) INTO v_found FROM temp_dealer_margins;

    -- If not found in DealerQuotes, try DealerMargins
    IF v_found = 0 THEN
        INSERT INTO temp_dealer_margins
        SELECT
            dm.dealer_id,
            d.dealer_name,
            dm.series_id,
            dm.base_boat_margin,
            dm.engine_margin,
            dm.options_margin,
            'PERCENTAGE',
            dm.freight_margin,
            'PERCENTAGE',
            dm.prep_margin,
            dm.volume_discount,
            'DealerMargins'
        FROM DealerMargins dm
        LEFT JOIN Dealers d ON dm.dealer_id = d.dealer_id
        WHERE (dm.dealer_id = v_dealer_varchar OR dm.dealer_id = CAST(v_dealer_int AS CHAR))
          AND (dm.series_id = p_series_id OR dm.series_id = v_series_normalized)
          AND dm.end_date IS NULL
        LIMIT 1;
    END IF;

    -- Return results
    SELECT * FROM temp_dealer_margins;

    -- Cleanup
    DROP TEMPORARY TABLE IF EXISTS temp_dealer_margins;
END //

DELIMITER ;

-- ============================================================================
-- Test Queries
-- ============================================================================

/*

-- Test 1: NICHOLS MARINE - NORMAN, SV_23 series (should find in DealerQuotes)
CALL GetDealerMargins('333836', 'SV_23');
CALL GetDealerMargins('333836', 'SV 23');  -- With space
CALL GetDealerMargins('00333836', 'SV_23'); -- With leading zeros

-- Test 2: Q series
CALL GetDealerMargins('333836', 'Q');

-- Test 3: With fallback version
CALL GetDealerMarginsWithFallback('333836', 'SV_23');
CALL GetDealerMarginsWithFallback('00333836', 'Q');

-- Test 4: CPQ-only dealer (should fallback to DealerMargins)
CALL GetDealerMarginsWithFallback('00322200', 'SV 23');

-- Verify function
SELECT GetSeriesColumnPrefix('SV 23');  -- Should return 'SV_23_'
SELECT GetSeriesColumnPrefix('Q');       -- Should return 'Q_'
SELECT GetSeriesColumnPrefix('QX');      -- Should return 'QX_'

*/

-- ============================================================================
-- END
-- ============================================================================

-- ============================================================================
-- Unified Dealer Margin Lookup - PRODUCTION VERSION
-- ============================================================================
-- SOURCE OF TRUTH: warrantyparts.DealerMargins (2,334 rows)
-- This is the production table with all dealer margin data
-- ============================================================================

USE warrantyparts_test;

DROP FUNCTION IF EXISTS GetSeriesColumnPrefix;
DROP PROCEDURE IF EXISTS GetDealerMarginsProduction;

DELIMITER //

-- ============================================================================
-- Function: GetSeriesColumnPrefix
-- ============================================================================
-- Maps series ID to DealerMargins column prefix
-- Handles variations: 'SV' -> 'SV_23', 'S' -> 'S_23', etc.

CREATE FUNCTION GetSeriesColumnPrefix(p_series VARCHAR(20))
RETURNS VARCHAR(30)
DETERMINISTIC
BEGIN
    DECLARE v_prefix VARCHAR(30);

    -- Normalize series (replace spaces with underscores)
    SET v_prefix = REPLACE(TRIM(p_series), ' ', '_');

    -- Special cases for column naming in DealerMargins
    IF v_prefix = 'SV' THEN
        SET v_prefix = 'SV_23';
    ELSEIF v_prefix = 'S' THEN
        SET v_prefix = 'S_23';
    END IF;

    -- Add trailing underscore
    SET v_prefix = CONCAT(v_prefix, '_');

    RETURN v_prefix;
END //

-- ============================================================================
-- Procedure: GetDealerMarginsProduction
-- ============================================================================
-- Gets dealer margins from PRODUCTION table: warrantyparts.DealerMargins
--
-- Parameters:
--   p_dealer_id VARCHAR(20) - Dealer ID (handles '333836' or '00333836')
--   p_series_id VARCHAR(20) - Series ID ('Q', 'SV', 'SV_23', etc.)
--
-- Returns:
--   dealer_id              VARCHAR(20)
--   dealer_name            VARCHAR(200)
--   series_id              VARCHAR(20)
--   base_boat_margin_pct   DECIMAL(10,2)
--   engine_margin_pct      DECIMAL(10,2)
--   options_margin_pct     DECIMAL(10,2)
--   freight_type           VARCHAR(20)    - Always 'FIXED_AMOUNT'
--   freight_value          DECIMAL(10,2)  - Dollar amount
--   prep_type              VARCHAR(20)    - Always 'FIXED_AMOUNT'
--   prep_value             DECIMAL(10,2)  - Dollar amount
--   volume_discount_pct    DECIMAL(10,2)
--   data_source            VARCHAR(50)    - Always 'warrantyparts.DealerMargins'

CREATE PROCEDURE GetDealerMarginsProduction(
    IN p_dealer_id VARCHAR(20),
    IN p_series_id VARCHAR(20)
)
BEGIN
    DECLARE v_dealer_normalized VARCHAR(20);
    DECLARE v_series_normalized VARCHAR(20);
    DECLARE v_col_prefix VARCHAR(30);

    -- Normalize dealer ID - remove leading zeros or add them as needed
    SET v_dealer_normalized = TRIM(LEADING '0' FROM TRIM(p_dealer_id));

    -- Normalize series
    SET v_series_normalized = REPLACE(TRIM(p_series_id), ' ', '_');
    SET v_col_prefix = GetSeriesColumnPrefix(p_series_id);

    -- Query warrantyparts.DealerMargins using dynamic SQL
    SET @sql = CONCAT('
        SELECT
            DealerID as dealer_id,
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
            ''warrantyparts.DealerMargins'' as data_source
        FROM warrantyparts.DealerMargins
        WHERE TRIM(LEADING ''0'' FROM DealerID) = ''', v_dealer_normalized, '''
        LIMIT 1
    ');

    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
END //

DELIMITER ;

-- ============================================================================
-- Test Queries
-- ============================================================================

/*

-- Test 1: NICHOLS MARINE - NORMAN (should get 27% from warrantyparts.DealerMargins)
CALL GetDealerMarginsProduction('333836', 'SV_23');
CALL GetDealerMarginsProduction('00333836', 'SV 23');  -- With leading zeros and space

-- Test 2: Q series
CALL GetDealerMarginsProduction('333836', 'Q');

-- Test 3: Different dealer
CALL GetDealerMarginsProduction('10050', 'SV_23');  -- BOYD'S MARINE

-- Test 4: Series column prefix function
SELECT GetSeriesColumnPrefix('SV');     -- Should return 'SV_23_'
SELECT GetSeriesColumnPrefix('SV 23');  -- Should return 'SV_23_'
SELECT GetSeriesColumnPrefix('Q');      -- Should return 'Q_'

*/

-- ============================================================================
-- END
-- ============================================================================

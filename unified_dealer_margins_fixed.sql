-- ============================================================================
-- Unified Dealer Margin Lookup - FIXED VERSION
-- ============================================================================
-- Handles special cases:
--   - SV series -> SV_23 in DealerQuotes
--   - S series -> S_23 in DealerQuotes (if exists)
-- ============================================================================

USE warrantyparts_test;

DROP FUNCTION IF EXISTS GetSeriesColumnPrefix;
DROP PROCEDURE IF EXISTS GetDealerMarginsWithFallback;

DELIMITER //

-- ============================================================================
-- Function: GetSeriesColumnPrefix
-- ============================================================================
-- Maps series ID to DealerQuotes column prefix
-- Special handling for SV -> SV_23

CREATE FUNCTION GetSeriesColumnPrefix(p_series VARCHAR(20))
RETURNS VARCHAR(30)
DETERMINISTIC
BEGIN
    DECLARE v_prefix VARCHAR(30);

    -- Normalize series (replace spaces with underscores)
    SET v_prefix = REPLACE(TRIM(p_series), ' ', '_');

    -- Special cases for DealerQuotes column names
    IF v_prefix = 'SV' THEN
        SET v_prefix = 'SV_23';
    ELSEIF v_prefix = 'S' THEN
        -- Try S_23 first, fallback to S if needed
        SET v_prefix = 'S_23';
    END IF;

    -- Add trailing underscore
    SET v_prefix = CONCAT(v_prefix, '_');

    RETURN v_prefix;
END //

-- ============================================================================
-- Procedure: GetDealerMarginsWithFallback
-- ============================================================================
-- Unified dealer margin lookup with fallback logic
-- Handles DealerQuotes wide table and DealerMargins normalized table

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

    -- Try DealerQuotes first with proper error handling
    BEGIN
        DECLARE CONTINUE HANDLER FOR SQLEXCEPTION SET v_found = 0;

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

        SELECT COUNT(*) INTO v_found FROM temp_dealer_margins;
    END;

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

        SELECT COUNT(*) INTO v_found FROM temp_dealer_margins;
    END IF;

    -- If still not found and series is 'S' (without _23), try S_23
    IF v_found = 0 AND v_series_normalized = 'S' THEN
        -- Already tried S_23, now try just S
        SET v_col_prefix = 'S_';

        BEGIN
            DECLARE CONTINUE HANDLER FOR SQLEXCEPTION SET v_found = 0;

            SET @sql = CONCAT('
                INSERT INTO temp_dealer_margins
                SELECT
                    CAST(DealerID AS CHAR),
                    Dealership,
                    ''S'',
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

            SELECT COUNT(*) INTO v_found FROM temp_dealer_margins;
        END;
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

-- Test 1: SV series (should map to SV_23)
CALL GetDealerMarginsWithFallback('333836', 'SV');
CALL GetDealerMarginsWithFallback('333836', 'SV_23');

-- Test 2: Q series
CALL GetDealerMarginsWithFallback('333836', 'Q');

-- Test 3: Verify function
SELECT GetSeriesColumnPrefix('SV');   -- Should return 'SV_23_'
SELECT GetSeriesColumnPrefix('S');    -- Should return 'S_23_'
SELECT GetSeriesColumnPrefix('Q');    -- Should return 'Q_'

*/

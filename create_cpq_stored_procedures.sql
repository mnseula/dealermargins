-- =====================================================================
-- Create CPQ Stored Procedures
-- =====================================================================
-- Creates the stored procedures needed for CPQ window stickers:
--   1. GET_CPQ_LHS_DATA - Get boat specifications (LHS section)
--   2. GET_CPQ_STANDARD_FEATURES - Get standard features by area
--
-- These procedures are called by getunregisteredboats.js via sStatement()
--
-- Author: Claude Code
-- Date: 2026-02-09
-- =====================================================================

USE warrantyparts;

DROP PROCEDURE IF EXISTS GET_CPQ_LHS_DATA;
DROP PROCEDURE IF EXISTS GET_CPQ_STANDARD_FEATURES;

-- =====================================================================
-- GET_CPQ_LHS_DATA
-- =====================================================================
-- Gets LHS (Left Hand Side) data with engine configuration
-- Parameters:
--   @PARAM1 = model_id (e.g., '23ML')
--   @PARAM2 = year (e.g., 2025)
--   @PARAM3 = hull_no (e.g., 'ETWTEST26')
-- =====================================================================

DELIMITER $$

CREATE PROCEDURE GET_CPQ_LHS_DATA(
    IN model_id_param VARCHAR(20),
    IN year_param INT,
    IN hull_no_param VARCHAR(20)
)
BEGIN
    SELECT
        m.model_id,
        m.model_name,
        m.series_id,
        m.floorplan_desc,
        m.loa_str AS loa,
        m.beam_str AS beam,
        m.length_feet,
        m.seats,
        mp.perf_package_id,
        pp.package_name,
        mp.person_capacity,
        mp.hull_weight,
        mp.max_hp,
        mp.no_of_tubes,
        mp.pontoon_gauge,
        mp.fuel_capacity,
        mp.tube_length_str AS pontoon_length,
        mp.deck_length_str AS deck_length,
        mp.tube_height,
        mp.pontoon_gauge AS pontoon_diameter,
        -- Engine configuration: use field if available, otherwise derive from twin_engine flag
        COALESCE(
            m.engine_configuration,
            CASE
                WHEN m.twin_engine = 1 THEN 'Twin Outboard'
                ELSE 'Single Outboard'
            END
        ) AS engine_configuration
    FROM warrantyparts_test.Models m
    LEFT JOIN (
        -- Get the performance package ID from the boat's configuration
        SELECT CfgValue AS perf_package_id
        FROM warrantyparts.BoatOptions26
        WHERE BoatSerialNo = hull_no_param
          AND CfgName = 'perfPack'
        LIMIT 1
    ) boat_perf ON 1=1
    LEFT JOIN warrantyparts_test.ModelPerformance mp
        ON m.model_id = mp.model_id
        AND mp.year = year_param
        AND mp.perf_package_id = boat_perf.perf_package_id
    LEFT JOIN warrantyparts_test.PerformancePackages pp
        ON mp.perf_package_id = pp.perf_package_id
    WHERE m.model_id = model_id_param
    LIMIT 1;
END$$

DELIMITER ;

-- =====================================================================
-- GET_CPQ_STANDARD_FEATURES
-- =====================================================================
-- Gets standard features for a model organized by area
-- Parameters:
--   @PARAM1 = model_id (e.g., '23ML')
--   @PARAM2 = year (e.g., 2025)
-- =====================================================================

DELIMITER $$

CREATE PROCEDURE GET_CPQ_STANDARD_FEATURES(
    IN model_id_param VARCHAR(20),
    IN year_param INT
)
BEGIN
    SELECT
        sf.feature_id,
        sf.feature_code,
        sf.area,
        sf.description,
        sf.sort_order
    FROM warrantyparts_test.StandardFeatures sf
    JOIN warrantyparts_test.ModelStandardFeatures msf
        ON sf.feature_id = msf.feature_id
    WHERE msf.model_id = model_id_param
      AND msf.year = year_param
      AND sf.active = 1
    ORDER BY
        CASE sf.area
            WHEN 'Interior Features' THEN 1
            WHEN 'Exterior Features' THEN 2
            WHEN 'Console Features' THEN 3
            WHEN 'Warranty' THEN 4
            ELSE 5
        END,
        sf.sort_order;
END$$

DELIMITER ;

-- =====================================================================
-- Verification
-- =====================================================================

SELECT
    ROUTINE_NAME,
    ROUTINE_TYPE,
    DTD_IDENTIFIER AS RETURNS,
    CREATED
FROM INFORMATION_SCHEMA.ROUTINES
WHERE ROUTINE_SCHEMA = 'warrantyparts'
  AND ROUTINE_NAME LIKE 'GET_CPQ%'
ORDER BY ROUTINE_NAME;

-- Updated sStatement: GET_CPQ_LHS_DATA_v3
-- Gets LHS data with engine configuration and proper formatting
-- Parameters:
--   @PARAM1 = model_id (e.g., '23ML')
--   @PARAM2 = year (e.g., 2025)
--   @PARAM3 = hull_no (e.g., 'ETWTEST26')

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
    WHERE BoatSerialNo = @PARAM3
      AND CfgName = 'perfPack'
    LIMIT 1
) boat_perf ON 1=1
LEFT JOIN warrantyparts_test.ModelPerformance mp
    ON m.model_id = mp.model_id
    AND mp.year = @PARAM2
    AND mp.perf_package_id = boat_perf.perf_package_id
LEFT JOIN warrantyparts_test.PerformancePackages pp
    ON mp.perf_package_id = pp.perf_package_id
WHERE m.model_id = @PARAM1
LIMIT 1;

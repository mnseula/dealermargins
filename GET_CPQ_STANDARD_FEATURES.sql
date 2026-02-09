-- sStatement: GET_CPQ_STANDARD_FEATURES
-- Gets standard features for a model organized by area
-- Parameters:
--   @PARAM1 = model_id (e.g., '23ML')
--   @PARAM2 = year (e.g., 2025)

SELECT
    sf.feature_id,
    sf.feature_code,
    sf.area,
    sf.description,
    sf.sort_order
FROM warrantyparts_test.StandardFeatures sf
JOIN warrantyparts_test.ModelStandardFeatures msf
    ON sf.feature_id = msf.feature_id
WHERE msf.model_id = @PARAM1
  AND msf.year = @PARAM2
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

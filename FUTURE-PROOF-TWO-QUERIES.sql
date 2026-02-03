-- ============================================================================
-- FUTURE-PROOF QUERIES FOR JAVASCRIPT
-- ============================================================================
-- Simple modifications to handle CPQ boats without item numbers
-- ============================================================================

-- ============================================================================
-- 1. SEL_ONE_SER_NO_MST - Boat Query (Future-Proof Version)
-- ============================================================================
-- ORIGINAL:
-- SELECT * FROM warrantyparts.SerialNumberMaster WHERE Boat_SerialNo = @PARAM1

-- MODIFIED (adds computed column for when BoatItemNo is NULL):
SELECT
    *,
    COALESCE(NULLIF(BoatItemNo, ''), CONCAT(Series, ' - ', BoatDesc1)) as BoatIdentifier
FROM warrantyparts.SerialNumberMaster
WHERE Boat_SerialNo = @PARAM1;

-- What changed:
-- - Added BoatIdentifier column
-- - Returns BoatItemNo if it exists (e.g., "20SVSRSR")
-- - Returns Series + Description if BoatItemNo is NULL (e.g., "SV - 20 S VALUE STERN RADIUS")
-- - All original columns still returned via *


-- ============================================================================
-- 2. SEL_ONE_ENG_SER_NO_MST - Engine Query (Future-Proof Version)
-- ============================================================================
-- ORIGINAL:
-- SELECT * FROM warrantyparts.EngineSerialNoMaster
-- WHERE Boat_SerialNo = @PARAM1
--   AND (OrigOrderType = 'C' OR OrigOrderType = 'I' OR OrigOrderType = 'O')
--   AND Active > 0

-- MODIFIED (adds computed column for when EngineItemNo is NULL):
SELECT
    *,
    COALESCE(NULLIF(EngineItemNo, ''), CONCAT(EngineBrand, ' - ', EngineDesc1)) as EngineIdentifier
FROM warrantyparts.EngineSerialNoMaster
WHERE Boat_SerialNo = @PARAM1
  AND (OrigOrderType = 'C' OR OrigOrderType = 'I' OR OrigOrderType = 'O')
  AND Active > 0;

-- What changed:
-- - Added EngineIdentifier column
-- - Returns EngineItemNo if it exists (e.g., "115ELPT4EFCT")
-- - Returns Brand + Description if EngineItemNo is NULL (e.g., "MERCURY ENGINES - MERC 115 HP 4S CT EFI 20 IN")
-- - All original columns still returned via *


-- ============================================================================
-- USAGE NOTES
-- ============================================================================
-- JavaScript code should check for the new identifier columns:
--
-- OLD JavaScript:
--   var boatItemNo = result[0].BoatItemNo;
--   var engineItemNo = result[0].EngineItemNo;
--
-- NEW JavaScript (works with or without item numbers):
--   var boatItemNo = result[0].BoatIdentifier || result[0].BoatItemNo;
--   var engineItemNo = result[0].EngineIdentifier || result[0].EngineItemNo;
--
-- Or simpler:
--   var boatItemNo = result[0].BoatIdentifier;  // Always populated
--   var engineItemNo = result[0].EngineIdentifier;  // Always populated


-- ============================================================================
-- TEST QUERIES
-- ============================================================================

-- Test Boat Query (current boat with ItemNo):
SELECT
    Boat_SerialNo,
    BoatItemNo,
    Series,
    BoatDesc1,
    COALESCE(NULLIF(BoatItemNo, ''), CONCAT(Series, ' - ', BoatDesc1)) as BoatIdentifier
FROM warrantyparts.SerialNumberMaster
WHERE Boat_SerialNo = 'ETWP7154K324';

-- Expected result:
-- BoatItemNo = "20SVSRSR"
-- BoatIdentifier = "20SVSRSR" (uses ItemNo since it exists)


-- Test Engine Query (current boat with ItemNo):
SELECT
    Boat_SerialNo,
    EngineItemNo,
    EngineBrand,
    EngineDesc1,
    COALESCE(NULLIF(EngineItemNo, ''), CONCAT(EngineBrand, ' - ', EngineDesc1)) as EngineIdentifier
FROM warrantyparts.EngineSerialNoMaster
WHERE Boat_SerialNo = 'ETWP7154K324'
  AND Active > 0;

-- Expected result:
-- EngineItemNo = "115ELPT4EFCT"
-- EngineIdentifier = "115ELPT4EFCT" (uses ItemNo since it exists)


-- Test with simulated NULL ItemNo (to show future behavior):
SELECT
    Boat_SerialNo,
    NULL as BoatItemNo,  -- Simulating CPQ boat
    Series,
    BoatDesc1,
    COALESCE(NULLIF(NULL, ''), CONCAT(Series, ' - ', BoatDesc1)) as BoatIdentifier
FROM warrantyparts.SerialNumberMaster
WHERE Boat_SerialNo = 'ETWP7154K324';

-- Expected result:
-- BoatItemNo = NULL
-- BoatIdentifier = "SV - 20 S VALUE STERN RADIUS" (uses description since ItemNo is NULL)


-- ============================================================================
-- SUMMARY OF CHANGES
-- ============================================================================
-- Query 1 (Boat):   Added BoatIdentifier column
-- Query 2 (Engine): Added EngineIdentifier column
--
-- Both queries:
--   - Still return all original columns (SELECT *)
--   - Add one new computed column
--   - Work with current boats (have ItemNo)
--   - Work with future CPQ boats (no ItemNo)
--   - No changes to WHERE clauses
--   - Minimal JavaScript changes needed
-- ============================================================================

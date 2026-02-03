-- ============================================================================
-- INCLUDED OPTIONS - Display Logic for Missing Item Numbers
-- ============================================================================
-- For CPQ boats where ItemNo might be NULL/empty
-- ============================================================================

-- ============================================================================
-- Pattern for Displaying Items (JavaScript logic)
-- ============================================================================
-- Current boats (have ItemNo):
--   Display: "905654 - Pro Angler Fish Station"
--
-- CPQ boats (ItemNo is NULL):
--   Display: "Pro Angler Fish Station" (no item number shown)
--
-- Logic:
--   IF ItemNo IS NOT NULL AND ItemNo != '' THEN
--     CONCAT(ItemNo, ' - ', ItemDesc1)
--   ELSE
--     ItemDesc1
--   END
-- ============================================================================


-- ============================================================================
-- SQL Query: Add ItemIdentifier column to line items
-- ============================================================================
-- This applies to queries that fetch line items from BoatOptions tables

SELECT
    ItemNo,
    ItemDesc1,
    QuantitySold,
    ExtSalesAmount,
    -- NEW: Display column that handles missing ItemNo
    CASE
        WHEN COALESCE(ItemNo, '') != '' THEN CONCAT(ItemNo, ' - ', ItemDesc1)
        ELSE ItemDesc1
    END as ItemIdentifier
FROM warrantyparts.BoatOptions24
WHERE BoatSerialNo = @PARAM1
  -- Your existing filters here
ORDER BY LineNo;


-- ============================================================================
-- JavaScript Usage
-- ============================================================================
/*
OLD JavaScript (breaks if ItemNo is NULL):
  var displayText = result[0].ItemNo + ' - ' + result[0].ItemDesc1;

NEW JavaScript (works with or without ItemNo):
  var displayText = result[0].ItemIdentifier;  // Always formatted correctly
*/


-- ============================================================================
-- Example Results
-- ============================================================================

-- Current boat (has ItemNo):
-- ItemNo    | ItemDesc1                        | ItemIdentifier
-- ----------|----------------------------------|----------------------------------------
-- 905654    | PRO ANGLER FISH STATION          | 905654 - PRO ANGLER FISH STATION
-- 900232    | 4 POLE ROD HOLDER                | 900232 - 4 POLE ROD HOLDER
-- 902607    | PANEL COLOR METALLIC WHITE       | 902607 - PANEL COLOR METALLIC WHITE

-- CPQ boat (ItemNo is NULL):
-- ItemNo    | ItemDesc1                        | ItemIdentifier
-- ----------|----------------------------------|----------------------------------------
-- NULL      | PRO ANGLER FISH STATION          | PRO ANGLER FISH STATION
-- NULL      | 4 POLE ROD HOLDER                | 4 POLE ROD HOLDER
-- NULL      | PANEL COLOR METALLIC WHITE       | PANEL COLOR METALLIC WHITE


-- ============================================================================
-- Summary of All Three Display Logic Patterns
-- ============================================================================

-- 1. BOAT (from SerialNumberMaster):
COALESCE(NULLIF(BoatItemNo, ''), CONCAT(Series, ' - ', BoatDesc1)) as BoatIdentifier

-- 2. ENGINE (from EngineSerialNoMaster):
COALESCE(NULLIF(EngineItemNo, ''), CONCAT(EngineBrand, ' - ', EngineDesc1)) as EngineIdentifier

-- 3. LINE ITEMS (from BoatOptions):
CASE
    WHEN COALESCE(ItemNo, '') != '' THEN CONCAT(ItemNo, ' - ', ItemDesc1)
    ELSE ItemDesc1
END as ItemIdentifier


-- ============================================================================
-- IMPORTANT: This is DISPLAY LOGIC ONLY
-- ============================================================================
-- This does NOT change filtering (what items are included/excluded)
-- Configuration items (colors, vinyl, furniture) still excluded via MCT codes
-- This only changes HOW items are displayed when ItemNo is missing
-- ============================================================================

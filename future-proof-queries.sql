-- ============================================================================
-- FUTURE-PROOF QUERIES FOR CPQ BOATS (WITHOUT ITEM NUMBERS)
-- ============================================================================
-- These queries use descriptions and other fields instead of relying on
-- item numbers, which won't exist for new CPQ boats.
-- ============================================================================

-- ============================================================================
-- 1. BOAT MASTER QUERY (replaces SEL_ONE_SER_NO_MST)
-- ============================================================================
-- Instead of relying on BoatItemNo, use Series + BoatDesc1 + BoatDesc2
-- to identify the boat model
-- ============================================================================

SELECT
    Boat_SerialNo,
    COALESCE(NULLIF(BoatItemNo, ''), CONCAT(Series, ' - ', BoatDesc1)) as BoatIdentifier,
    Series,
    BoatDesc1,
    BoatDesc2,
    SerialModelYear,
    DealerNumber,
    DealerName,
    DealerCity,
    DealerState,
    PanelColor,
    AccentPanel,
    TrimAccent,
    BaseVinyl,
    ColorPackage,
    ERP_OrderNo,
    InvoiceNo,
    InvoiceDateYYYYMMDD,
    OrigOrderType,
    Active
FROM warrantyparts.SerialNumberMaster
WHERE Boat_SerialNo = @PARAM1;

-- ============================================================================
-- 2. ENGINE QUERY (replaces SEL_ONE_ENG_SER_NO_MST)
-- ============================================================================
-- Instead of relying on EngineItemNo, use EngineBrand + EngineDesc1
-- to identify the engine
-- ============================================================================

SELECT
    Boat_SerialNo,
    COALESCE(NULLIF(EngineItemNo, ''), CONCAT(EngineBrand, ' - ', EngineDesc1)) as EngineIdentifier,
    EngineItemNo,
    EngineSerialNo,
    EngineBrand,
    EngineDesc1,
    OrigOrderType,
    Active,
    ERP_OrderNo
FROM warrantyparts.EngineSerialNoMaster
WHERE Boat_SerialNo = @PARAM1
  AND (OrigOrderType = 'C' OR OrigOrderType = 'I' OR OrigOrderType = 'O')
  AND Active > 0;

-- ============================================================================
-- 3. LOOKUP ENGINE COST BY DESCRIPTION (NEW APPROACH)
-- ============================================================================
-- Query BoatOptions to find engine cost using description matching
-- instead of item number matching
-- ============================================================================

-- Example: Find engine cost for ETWP7154K324's Mercury 115HP engine
SELECT
    ItemNo,
    ItemDesc1,
    ExtSalesAmount as EngineCost,
    BoatSerialNo
FROM warrantyparts.BoatOptions24
WHERE BoatSerialNo = 'ETWP7154K324'
  AND MCTDesc IN ('ENGINES', 'ENGINES I/O')
  AND ItemDesc1 LIKE '%115%HP%'  -- Match by description, not item number
LIMIT 1;

-- ============================================================================
-- 4. GENERIC ENGINE COST LOOKUP FUNCTION (DESCRIPTION-BASED)
-- ============================================================================
-- Instead of looking up by EngineItemNo, look up by:
--   - EngineBrand (MERCURY, YAMAHA, etc.)
--   - Horsepower (extracted from description)
--   - Stroke type (2S, 4S, CT, EFI, etc.)
-- ============================================================================

-- Example: Find all 115HP Mercury engines and their costs
SELECT
    ItemNo,
    ItemDesc1,
    AVG(ExtSalesAmount) as AvgCost,
    MIN(ExtSalesAmount) as MinCost,
    MAX(ExtSalesAmount) as MaxCost,
    COUNT(*) as Occurrences
FROM warrantyparts.BoatOptions24
WHERE MCTDesc IN ('ENGINES', 'ENGINES I/O')
  AND ItemDesc1 LIKE '%MERC%115%HP%'
GROUP BY ItemNo, ItemDesc1
ORDER BY Occurrences DESC;

-- ============================================================================
-- 5. PRERIG COST LOOKUP BY DESCRIPTION
-- ============================================================================
-- Find prerig costs using description patterns instead of item numbers
-- ============================================================================

SELECT
    ItemNo,
    ItemDesc1,
    ExtSalesAmount as PrerigCost,
    BoatSerialNo
FROM warrantyparts.BoatOptions24
WHERE BoatSerialNo = 'ETWP7154K324'
  AND MCTDesc = 'PRE-RIG'
  AND ItemDesc1 LIKE '%PRERIG%'
LIMIT 1;

-- ============================================================================
-- 6. OPTIONS/ACCESSORIES LOOKUP (ALREADY USING CATEGORY, NOT ITEM NUMBER!)
-- ============================================================================
-- This is CORRECT and future-proof - uses ItemMasterProdCat = 'ACC'
-- instead of ItemNo LIKE '90%'
-- ============================================================================

SELECT
    ItemNo,
    ItemDesc1,
    MCTDesc,
    ExtSalesAmount,
    ItemMasterProdCat
FROM warrantyparts.BoatOptions24
WHERE BoatSerialNo = 'ETWP7154K324'
  AND ItemMasterProdCat = 'ACC'  -- ✓ Future-proof!
ORDER BY LineNo;

-- ============================================================================
-- 7. COMPLETE BOAT PRICING (DESCRIPTION-BASED APPROACH)
-- ============================================================================
-- Get all line items without relying on item number prefixes
-- ============================================================================

SELECT
    LineNo,
    COALESCE(NULLIF(ItemNo, ''), ItemDesc1) as ItemIdentifier,
    ItemDesc1 as Description,
    MCTDesc as Category,
    ItemMasterProdCat as ProductCategory,
    ExtSalesAmount as DealerCost,
    QuantitySold,
    BoatModelNo
FROM warrantyparts.BoatOptions24
WHERE BoatSerialNo = 'ETWP7154K324'
  AND MCTDesc NOT IN ('Lower Unit Eng', 'GROW BOATING', 'ZZZ', 'WAR', 'DLR', 'FRT')
  AND ItemMasterMCT NOT IN ('DIC','DIF','DIP','DIR','DIA','DIW','LOY','PRD','VOD','DIV','CAS','SHO','GRO','ZZZ','FRE','WAR','DLR','FRT')
  AND (ItemMasterProdCat != '111' OR ItemMasterProdCat IS NULL)
ORDER BY
    CASE MCTDesc
        WHEN 'PONTOONS' THEN 1
        WHEN 'ENGINES' THEN 2
        WHEN 'ENGINES I/O' THEN 2
        WHEN 'PRE-RIG' THEN 3
        WHEN 'PERFORMANCE PKG' THEN 4
        ELSE 5
    END,
    LineNo;

-- ============================================================================
-- NOTES FOR FUTURE CPQ INTEGRATION
-- ============================================================================
-- When CPQ boats arrive without item numbers:
--
-- 1. BOAT IDENTIFICATION:
--    - Use: Series + BoatDesc1 + BoatDesc2
--    - Example: "SV - 20 S VALUE STERN RADIUS - 2024"
--
-- 2. ENGINE IDENTIFICATION:
--    - Use: EngineBrand + EngineDesc1
--    - Example: "MERCURY ENGINES - MERC 115 HP 4S CT EFI 20 IN"
--    - Parse horsepower: Extract "115" from description
--    - Parse type: Extract "4S CT EFI" from description
--
-- 3. COST LOOKUPS:
--    - Query BoatOptions by description matching
--    - Use pattern matching: LIKE '%115%HP%MERC%'
--    - Average costs across similar descriptions if needed
--
-- 4. DEFAULT CONFIGURATION:
--    - Create lookup table mapping:
--      * Series + Length → Default Engine Description
--      * Series + Length → Default Prerig Description
--    - Example: "SV 20ft" → "MERC 90HP 4S" (default)
--
-- ============================================================================

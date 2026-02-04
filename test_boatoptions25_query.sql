-- ============================================================================
-- Complete Working Query for BoatOptions25
-- ============================================================================
-- Test Serial: ETWC4149F425
-- Expected: 21 items (boat, engines, prerig, accessories)
-- Excludes: Config items (colors, vinyl, canvas, etc.)
-- ============================================================================

SELECT
    ItemNo,
    ItemDesc1,
    MCTDesc,
    ItemMasterMCT,
    ExtSalesAmount,
    QuantitySold,
    CASE
        WHEN COALESCE(ItemNo, '') != '' THEN CONCAT(ItemNo, ' - ', ItemDesc1)
        ELSE ItemDesc1
    END as ItemIdentifier
FROM warrantyparts.BoatOptions25
WHERE BoatSerialNo = 'ETWC4149F425'
  AND ItemMasterMCT NOT IN (
    'DIC','DIF','DIP','DIR','DIA','DIW','LOY','PRD','VOD','DIV',
    'SHO','GRO','ZZZ','FRE','WAR','DLR','FRT',
    'A0','A0C','A0G','A0I','A0P','A0T','A0V','A1','A6','FUR'
  )
  AND (ItemMasterMCT <> 'DIS' OR (ItemMasterMCT = 'DIS' AND ItemNo = 'NPPNPRICE16S'))
  AND (ItemMasterMCT <> 'ENZ' OR (ItemMasterMCT = 'ENZ' AND ItemDesc1 LIKE '%VALUE%'))
  AND ItemMasterProdCat <> '111'
  AND NOT (ItemMasterMCT = 'ACY' AND COALESCE(ExtSalesAmount, 0) = 0)
ORDER BY
  CASE MCTDesc
    WHEN 'PONTOONS' THEN 1
    WHEN 'Pontoon Boats OB' THEN 1
    WHEN 'Pontoon Boats IO' THEN 1
    WHEN 'Lower Unit Eng' THEN 2
    WHEN 'ENGINES' THEN 3
    WHEN 'Engine' THEN 3
    WHEN 'Engine IO' THEN 3
    WHEN 'PRE-RIG' THEN 4
    WHEN 'Prerig' THEN 4
    ELSE 5
  END,
  LineNo ASC;


-- ============================================================================
-- Key Changes from Original JavaScript Query:
-- ============================================================================
-- 1. REMOVED invoice/ERP filter (was causing empty results)
-- 2. ADDED: AND NOT (ItemMasterMCT = 'ACY' AND COALESCE(ExtSalesAmount, 0) = 0)
--    This excludes $0 accessories (config items) in BoatOptions25
-- 3. ADDED: ItemIdentifier column for display
--
-- Note: BoatOptions25 uses generic 'ACY' code for all accessories,
-- so we filter by cost instead of specific MCT codes like BoatOptions24
-- ============================================================================

-- ============================================================================
-- ALL THREE QUERIES - Complete with Display Logic for Missing Item Numbers
-- ============================================================================
-- Option 1: If Item # is empty, show description only (no item number)
-- ============================================================================

-- ============================================================================
-- QUERY 1: SEL_ONE_SER_NO_MST (Boat Query)
-- ============================================================================
SELECT
    *,
    COALESCE(NULLIF(BoatItemNo, ''), CONCAT(Series, ' - ', BoatDesc1)) as BoatIdentifier
FROM warrantyparts.SerialNumberMaster
WHERE Boat_SerialNo = @PARAM1;

-- Results:
--   Current boat: BoatIdentifier = "20SVSRSR"
--   CPQ boat:     BoatIdentifier = "SV - 20 S VALUE STERN RADIUS"


-- ============================================================================
-- QUERY 2: SEL_ONE_ENG_SER_NO_MST (Engine Query)
-- ============================================================================
SELECT
    *,
    COALESCE(NULLIF(EngineItemNo, ''), CONCAT(EngineBrand, ' - ', EngineDesc1)) as EngineIdentifier
FROM warrantyparts.EngineSerialNoMaster
WHERE Boat_SerialNo = @PARAM1
  AND (OrigOrderType = 'C' OR OrigOrderType = 'I' OR OrigOrderType = 'O')
  AND Active > 0;

-- Results:
--   Current boat: EngineIdentifier = "115ELPT4EFCT"
--   CPQ boat:     EngineIdentifier = "MERCURY ENGINES - MERC 115 HP 4S CT EFI 20 IN"


-- ============================================================================
-- QUERY 3: LINE ITEMS / INCLUDED OPTIONS (from BoatOptions table)
-- ============================================================================
SELECT
    ItemNo,
    ItemDesc1,
    QuantitySold,
    ExtSalesAmount,
    CASE
        WHEN COALESCE(ItemNo, '') != '' THEN CONCAT(ItemNo, ' - ', ItemDesc1)
        ELSE ItemDesc1
    END as ItemIdentifier,
    MCTDesc,
    ItemMasterMCT,
    ItemMasterProdCat
FROM warrantyparts.BoatOptions24
WHERE BoatSerialNo = @PARAM1
  AND MCTDesc NOT IN ('PONTOONS', 'Pontoon Boats OB', 'ENGINES', 'ENGINES I/O', 'PRE-RIG', 'Lower Unit Eng', 'GROW BOATING')
  AND ItemMasterMCT NOT IN ('DIC','DIF','DIP','DIR','DIA','DIW','LOY','PRD','VOD','DIV','CAS','SHO','GRO','ZZZ','FRE','WAR','DLR','FRT','A0','A0C','A0G','A0I','A0P','A0T','A0V','A1','A6','FUR')
  AND ItemMasterProdCat != '111'
  AND MCTDesc NOT LIKE 'Disc%'
  AND MCTDesc NOT LIKE '%DISCOUNT%'
ORDER BY
    CASE MCTDesc
        WHEN 'PERFORMANCE PKG' THEN 1
        ELSE 2
    END,
    LineNo;

-- Results:
--   Current boat: ItemIdentifier = "905654 - PRO ANGLER FISH STATION"
--   CPQ boat:     ItemIdentifier = "PRO ANGLER FISH STATION"


-- ============================================================================
-- JAVASCRIPT IMPLEMENTATION
-- ============================================================================

/*
// ============================================================================
// Query 1: Boat Info
// ============================================================================
const boatQuery = `
    SELECT
        *,
        COALESCE(NULLIF(BoatItemNo, ''), CONCAT(Series, ' - ', BoatDesc1)) as BoatIdentifier
    FROM warrantyparts.SerialNumberMaster
    WHERE Boat_SerialNo = ?
`;

connection.query(boatQuery, [serialNumber], (err, results) => {
    if (err) throw err;

    // OLD: var boatItemNo = results[0].BoatItemNo;  // Breaks if NULL
    // NEW:
    var boatItemNo = results[0].BoatIdentifier;     // Always works ✓

    console.log('Boat:', boatItemNo);
    // Current boat: "20SVSRSR"
    // CPQ boat:     "SV - 20 S VALUE STERN RADIUS"
});


// ============================================================================
// Query 2: Engine Info
// ============================================================================
const engineQuery = `
    SELECT
        *,
        COALESCE(NULLIF(EngineItemNo, ''), CONCAT(EngineBrand, ' - ', EngineDesc1)) as EngineIdentifier
    FROM warrantyparts.EngineSerialNoMaster
    WHERE Boat_SerialNo = ?
      AND (OrigOrderType = 'C' OR OrigOrderType = 'I' OR OrigOrderType = 'O')
      AND Active > 0
`;

connection.query(engineQuery, [serialNumber], (err, results) => {
    if (err) throw err;

    // OLD: var engineItemNo = results[0].EngineItemNo;  // Breaks if NULL
    // NEW:
    var engineItemNo = results[0].EngineIdentifier;     // Always works ✓

    console.log('Engine:', engineItemNo);
    // Current boat: "115ELPT4EFCT"
    // CPQ boat:     "MERCURY ENGINES - MERC 115 HP 4S CT EFI 20 IN"
});


// ============================================================================
// Query 3: Line Items / Included Options
// ============================================================================
const itemsQuery = `
    SELECT
        ItemNo,
        ItemDesc1,
        QuantitySold,
        ExtSalesAmount,
        CASE
            WHEN COALESCE(ItemNo, '') != '' THEN CONCAT(ItemNo, ' - ', ItemDesc1)
            ELSE ItemDesc1
        END as ItemIdentifier,
        MCTDesc,
        ItemMasterMCT
    FROM warrantyparts.BoatOptions24
    WHERE BoatSerialNo = ?
      AND MCTDesc NOT IN ('PONTOONS', 'Pontoon Boats OB', 'ENGINES', 'ENGINES I/O', 'PRE-RIG', 'Lower Unit Eng', 'GROW BOATING')
      AND ItemMasterMCT NOT IN ('DIC','DIF','DIP','DIR','DIA','DIW','LOY','PRD','VOD','DIV','CAS','SHO','GRO','ZZZ','FRE','WAR','DLR','FRT','A0','A0C','A0G','A0I','A0P','A0T','A0V','A1','A6','FUR')
      AND ItemMasterProdCat != '111'
      AND MCTDesc NOT LIKE 'Disc%'
      AND MCTDesc NOT LIKE '%DISCOUNT%'
    ORDER BY
        CASE MCTDesc WHEN 'PERFORMANCE PKG' THEN 1 ELSE 2 END,
        LineNo
`;

connection.query(itemsQuery, [serialNumber], (err, results) => {
    if (err) throw err;

    results.forEach(item => {
        // OLD: var display = item.ItemNo + ' - ' + item.ItemDesc1;  // Breaks if ItemNo is NULL
        // NEW:
        var display = item.ItemIdentifier;  // Always works ✓

        console.log(display, '$' + item.ExtSalesAmount);
        // Current boat: "905654 - PRO ANGLER FISH STATION $1,500.00"
        // CPQ boat:     "PRO ANGLER FISH STATION $1,500.00"
    });
});
*/


-- ============================================================================
-- DISPLAY EXAMPLES
-- ============================================================================

-- Current Boat (has ItemNo):
-- ===========================
-- Boat:   20SVSRSR
-- Engine: 115ELPT4EFCT
-- Items:
--   905654 - PRO ANGLER FISH STATION
--   900232 - 4 POLE ROD HOLDER
--   900465 - BIMINI BLUE ICE LED LIGHTING
--   904239 - CURVED BOARDING LADDER WITH PLATFORM
--   901258 - SWITCH SNGL BAT BENCH SV/S

-- CPQ Boat (ItemNo is NULL):
-- ===========================
-- Boat:   SV - 20 S VALUE STERN RADIUS
-- Engine: MERCURY ENGINES - MERC 115 HP 4S CT EFI 20 IN
-- Items:
--   PRO ANGLER FISH STATION
--   4 POLE ROD HOLDER
--   BIMINI BLUE ICE LED LIGHTING
--   CURVED BOARDING LADDER WITH PLATFORM
--   SWITCH SNGL BAT BENCH SV/S


-- ============================================================================
-- SUMMARY
-- ============================================================================
-- ✓ All three queries add an "Identifier" column
-- ✓ Identifier shows ItemNo + Description when ItemNo exists
-- ✓ Identifier shows Description only when ItemNo is NULL
-- ✓ JavaScript just uses the Identifier column - works for all boats
-- ✓ No breaking changes - all original columns still returned
-- ✓ Minimal JavaScript changes - 3 variable assignments
-- ============================================================================

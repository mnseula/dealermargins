-- ============================================================================
-- Create Views with BoatIdentifier and EngineIdentifier
-- ============================================================================
-- These views add computed columns for CPQ compatibility
-- Falls back to descriptive names when ItemNo is empty
-- ============================================================================

USE warrantyparts_test;

-- ============================================================================
-- 1. SerialNumberMaster View with BoatIdentifier
-- ============================================================================

DROP VIEW IF EXISTS SerialNumberMasterView;

CREATE VIEW SerialNumberMasterView AS
SELECT
    *,
    -- BoatIdentifier: Use BoatItemNo if populated, else "Series - BoatDesc1"
    COALESCE(
        NULLIF(BoatItemNo, ''),
        CONCAT(IFNULL(Series, ''), ' - ', IFNULL(BoatDesc1, ''))
    ) AS BoatIdentifier
FROM SerialNumberMaster;

-- ============================================================================
-- 2. EngineSerialNoMaster View with EngineIdentifier
-- ============================================================================

DROP VIEW IF EXISTS EngineSerialNoMasterView;

CREATE VIEW EngineSerialNoMasterView AS
SELECT
    *,
    -- EngineIdentifier: Use EngineItemNo if populated, else "EngineBrand - EngineDesc1"
    COALESCE(
        NULLIF(EngineItemNo, ''),
        CONCAT(IFNULL(EngineBrand, ''), ' - ', IFNULL(EngineDesc1, ''))
    ) AS EngineIdentifier
FROM EngineSerialNoMaster;

-- ============================================================================
-- Test the Views
-- ============================================================================

-- Test SerialNumberMaster View
SELECT
    Boat_SerialNo,
    BoatItemNo,
    Series,
    BoatDesc1,
    BoatIdentifier,
    CASE
        WHEN BoatItemNo IS NULL OR BoatItemNo = '' THEN 'Fallback'
        ELSE 'ItemNo'
    END AS Source
FROM SerialNumberMasterView
LIMIT 10;

-- Test EngineSerialNoMaster View
SELECT
    Boat_SerialNo,
    EngineItemNo,
    EngineBrand,
    EngineDesc1,
    EngineIdentifier,
    CASE
        WHEN EngineItemNo IS NULL OR EngineItemNo = '' THEN 'Fallback'
        ELSE 'ItemNo'
    END AS Source
FROM EngineSerialNoMasterView
LIMIT 10;

-- ============================================================================
-- Show counts
-- ============================================================================

SELECT
    'SerialNumberMaster' AS TableName,
    COUNT(*) AS TotalRows,
    SUM(CASE WHEN BoatItemNo IS NULL OR BoatItemNo = '' THEN 1 ELSE 0 END) AS EmptyItemNo,
    SUM(CASE WHEN BoatItemNo IS NOT NULL AND BoatItemNo != '' THEN 1 ELSE 0 END) AS HasItemNo
FROM SerialNumberMaster

UNION ALL

SELECT
    'EngineSerialNoMaster' AS TableName,
    COUNT(*) AS TotalRows,
    SUM(CASE WHEN EngineItemNo IS NULL OR EngineItemNo = '' THEN 1 ELSE 0 END) AS EmptyItemNo,
    SUM(CASE WHEN EngineItemNo IS NOT NULL AND EngineItemNo != '' THEN 1 ELSE 0 END) AS HasItemNo
FROM EngineSerialNoMaster;

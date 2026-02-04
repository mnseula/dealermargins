-- ============================================================================
-- Verify Imported BoatOptions Data
-- ============================================================================
-- Run this after import to verify data quality
-- Database: warrantyparts_boatoptions_test
-- ============================================================================

USE warrantyparts_boatoptions_test;

-- ============================================================================
-- 1. ROW COUNT SUMMARY
-- ============================================================================
SELECT 'Row Count Summary' as Check_Type;

SELECT
    TABLE_NAME,
    TABLE_ROWS
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'warrantyparts_boatoptions_test'
    AND TABLE_NAME LIKE 'BoatOptions%'
    AND TABLE_NAME NOT LIKE '%_test'
ORDER BY TABLE_NAME;

-- ============================================================================
-- 2. CPQ ORDERS - Check ConfigID and ValueText
-- ============================================================================
SELECT '\n\nCPQ Orders with Configured Items' as Check_Type;

SELECT
    ERP_OrderNo,
    BoatSerialNo,
    BoatModelNo,
    ItemNo,
    ItemDesc1,
    ConfigID,
    ValueText,
    ExtSalesAmount,
    MCTDesc
FROM BoatOptions26
WHERE ConfigID IS NOT NULL
    AND ConfigID != ''
ORDER BY ERP_OrderNo, LineNo
LIMIT 20;

-- ============================================================================
-- 3. CONFIGURED ITEMS - Colors, Vinyl, Canvas (should have ValueText)
-- ============================================================================
SELECT '\n\nConfigured Items (Colors, Vinyl, Canvas)' as Check_Type;

SELECT
    BoatSerialNo,
    ItemNo,
    ItemDesc1,
    ValueText,
    ItemMasterMCT,
    MCTDesc,
    ExtSalesAmount
FROM BoatOptions25
WHERE (
    ItemDesc1 LIKE '%COLOR%'
    OR ItemDesc1 LIKE '%VINYL%'
    OR ItemDesc1 LIKE '%CANVAS%'
    OR ValueText IS NOT NULL
)
ORDER BY BoatSerialNo, ItemNo
LIMIT 20;

-- ============================================================================
-- 4. RECENT INVOICES - Check InvoiceDate
-- ============================================================================
SELECT '\n\nRecent Invoices (December 2024 onwards)' as Check_Type;

SELECT
    InvoiceDate,
    InvoiceNo,
    COUNT(*) as LineItems,
    COUNT(DISTINCT BoatSerialNo) as BoatCount,
    SUM(ExtSalesAmount) as TotalAmount
FROM BoatOptions25
WHERE InvoiceDate >= 20241214
GROUP BY InvoiceDate, InvoiceNo
ORDER BY InvoiceDate DESC
LIMIT 10;

-- ============================================================================
-- 5. SAMPLE BOATS - Complete Order Details
-- ============================================================================
SELECT '\n\nSample Complete Boat Orders' as Check_Type;

-- Get one recent boat
SELECT
    bo.BoatSerialNo,
    bo.BoatModelNo,
    bo.ERP_OrderNo,
    bo.InvoiceNo,
    bo.InvoiceDate,
    COUNT(*) as LineItems,
    SUM(bo.ExtSalesAmount) as TotalAmount,
    GROUP_CONCAT(DISTINCT bo.MCTDesc SEPARATOR ', ') as ItemTypes
FROM BoatOptions25 bo
WHERE bo.InvoiceDate >= 20241214
GROUP BY bo.BoatSerialNo, bo.BoatModelNo, bo.ERP_OrderNo, bo.InvoiceNo, bo.InvoiceDate
ORDER BY bo.InvoiceDate DESC
LIMIT 5;

-- ============================================================================
-- 6. ITEM BREAKDOWN - By MCT Type
-- ============================================================================
SELECT '\n\nItem Breakdown by MCT Type (2025 models)' as Check_Type;

SELECT
    MCTDesc,
    ItemMasterMCT,
    COUNT(*) as ItemCount,
    COUNT(DISTINCT BoatSerialNo) as BoatCount,
    SUM(ExtSalesAmount) as TotalAmount,
    AVG(ExtSalesAmount) as AvgAmount
FROM BoatOptions25
GROUP BY MCTDesc, ItemMasterMCT
ORDER BY ItemCount DESC
LIMIT 20;

-- ============================================================================
-- 7. DETAILED VIEW - One Complete Boat with All Items
-- ============================================================================
SELECT '\n\nDetailed View - One Complete Boat' as Check_Type;

-- Pick a recent boat and show all its items
SELECT
    LineNo,
    ItemNo,
    ItemDesc1,
    MCTDesc,
    ItemMasterMCT,
    ItemMasterProdCat,
    QuantitySold,
    ExtSalesAmount,
    ConfigID,
    ValueText
FROM BoatOptions25
WHERE BoatSerialNo = (
    SELECT BoatSerialNo
    FROM BoatOptions25
    WHERE InvoiceDate >= 20241214
    ORDER BY InvoiceDate DESC
    LIMIT 1
)
ORDER BY LineNo;

-- ============================================================================
-- 8. DATA QUALITY CHECKS
-- ============================================================================
SELECT '\n\nData Quality Checks' as Check_Type;

-- Check for missing critical fields
SELECT
    'Missing BoatSerialNo' as Issue,
    COUNT(*) as Count
FROM BoatOptions25
WHERE BoatSerialNo IS NULL OR BoatSerialNo = ''

UNION ALL

SELECT
    'Missing ItemNo' as Issue,
    COUNT(*) as Count
FROM BoatOptions25
WHERE ItemNo IS NULL OR ItemNo = ''

UNION ALL

SELECT
    'Missing MCTDesc' as Issue,
    COUNT(*) as Count
FROM BoatOptions25
WHERE MCTDesc IS NULL OR MCTDesc = ''

UNION ALL

SELECT
    'Zero Amount Items' as Issue,
    COUNT(*) as Count
FROM BoatOptions25
WHERE ExtSalesAmount = 0 OR ExtSalesAmount IS NULL

UNION ALL

SELECT
    'ConfigID populated' as Issue,
    COUNT(*) as Count
FROM BoatOptions25
WHERE ConfigID IS NOT NULL AND ConfigID != '';

-- ============================================================================
-- 9. CPQ vs NON-CPQ COMPARISON
-- ============================================================================
SELECT '\n\nCPQ vs Non-CPQ Orders' as Check_Type;

SELECT
    CASE
        WHEN ConfigID IS NOT NULL AND ConfigID != '' THEN 'CPQ Orders'
        ELSE 'Non-CPQ Orders'
    END as OrderType,
    COUNT(DISTINCT ERP_OrderNo) as OrderCount,
    COUNT(DISTINCT BoatSerialNo) as BoatCount,
    COUNT(*) as LineItems,
    SUM(ExtSalesAmount) as TotalAmount
FROM BoatOptions25
GROUP BY
    CASE
        WHEN ConfigID IS NOT NULL AND ConfigID != '' THEN 'CPQ Orders'
        ELSE 'Non-CPQ Orders'
    END;

-- ============================================================================
-- 10. INVOICE DATE RANGE
-- ============================================================================
SELECT '\n\nInvoice Date Range' as Check_Type;

SELECT
    MIN(InvoiceDate) as FirstInvoice,
    MAX(InvoiceDate) as LastInvoice,
    COUNT(DISTINCT InvoiceDate) as UniqueDates,
    COUNT(DISTINCT InvoiceNo) as TotalInvoices
FROM BoatOptions25
WHERE InvoiceDate >= 20241214;

-- ============================================================================
-- VERIFICATION COMPLETE
-- ============================================================================
SELECT '\n\n✅ Verification Complete!' as Status;

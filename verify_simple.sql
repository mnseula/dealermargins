-- Simple verification - key metrics only
USE warrantyparts_boatoptions_test;

-- 1. Total rows by table
SELECT 'TOTAL ROWS BY TABLE' as metric, '' as value
UNION ALL
SELECT TABLE_NAME, CAST(TABLE_ROWS AS CHAR)
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'warrantyparts_boatoptions_test'
    AND TABLE_NAME IN ('BoatOptions24', 'BoatOptions25', 'BoatOptions26')
ORDER BY TABLE_NAME;

-- 2. CPQ order count
SELECT '' as metric, '' as value
UNION ALL
SELECT 'CPQ ORDERS (with ConfigID)', CAST(COUNT(DISTINCT ERP_OrderNo) AS CHAR)
FROM BoatOptions25
WHERE ConfigID IS NOT NULL AND ConfigID != '';

-- 3. Invoice date range
SELECT '' as metric, '' as value
UNION ALL
SELECT 'EARLIEST INVOICE', CAST(MIN(InvoiceDate) AS CHAR)
FROM BoatOptions25
WHERE InvoiceDate >= 20241214
UNION ALL
SELECT 'LATEST INVOICE', CAST(MAX(InvoiceDate) AS CHAR)
FROM BoatOptions25
WHERE InvoiceDate >= 20241214;

-- 4. Sample boat serial numbers
SELECT '' as metric, '' as value
UNION ALL
SELECT 'SAMPLE SERIALS', BoatSerialNo
FROM BoatOptions25
WHERE InvoiceDate >= 20241214
GROUP BY BoatSerialNo
LIMIT 5;

-- 5. Configured items count
SELECT '' as metric, '' as value
UNION ALL
SELECT 'CONFIGURED ITEMS', CAST(COUNT(*) AS CHAR)
FROM BoatOptions25
WHERE ValueText IS NOT NULL AND ValueText != '';

-- 6. MCT breakdown
SELECT '' as metric, '' as value
UNION ALL
SELECT 'MCT TYPES', '' as value
UNION ALL
SELECT MCTDesc, CAST(COUNT(*) AS CHAR)
FROM BoatOptions25
GROUP BY MCTDesc
ORDER BY COUNT(*) DESC
LIMIT 10;

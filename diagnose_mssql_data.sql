-- ============================================================================
-- Diagnostic Queries for MSSQL Data Investigation
-- ============================================================================
-- Run these on MSSQL to understand why so few rows are being imported
-- ============================================================================

USE CSISTG;
GO

-- 1. Check total rows in coitem_mst for BENN site
SELECT
    'Total rows in coitem_mst for BENN' as check_name,
    COUNT(*) as row_count
FROM [CSISTG].[dbo].[coitem_mst]
WHERE site_ref = 'BENN';

-- 2. Check rows WITH serial numbers
SELECT
    'Rows with serial numbers' as check_name,
    COUNT(*) as row_count
FROM [CSISTG].[dbo].[coitem_mst]
WHERE site_ref = 'BENN'
    AND Uf_BENN_BoatSerialNumber IS NOT NULL
    AND Uf_BENN_BoatSerialNumber != '';

-- 3. Check rows WITHOUT serial numbers
SELECT
    'Rows WITHOUT serial numbers' as check_name,
    COUNT(*) as row_count
FROM [CSISTG].[dbo].[coitem_mst]
WHERE site_ref = 'BENN'
    AND (Uf_BENN_BoatSerialNumber IS NULL OR Uf_BENN_BoatSerialNumber = '');

-- 4. What product codes exist for rows WITH serial numbers?
SELECT TOP 50
    im.product_code,
    COUNT(*) as row_count,
    COUNT(DISTINCT coi.Uf_BENN_BoatSerialNumber) as boat_count
FROM [CSISTG].[dbo].[coitem_mst] coi
LEFT JOIN [CSISTG].[dbo].[item_mst] im ON coi.item = im.item AND coi.site_ref = im.site_ref
WHERE coi.site_ref = 'BENN'
    AND coi.Uf_BENN_BoatSerialNumber IS NOT NULL
    AND coi.Uf_BENN_BoatSerialNumber != ''
GROUP BY im.product_code
ORDER BY row_count DESC;

-- 5. What product codes exist for rows WITHOUT serial numbers?
SELECT TOP 50
    im.product_code,
    COUNT(*) as row_count
FROM [CSISTG].[dbo].[coitem_mst] coi
LEFT JOIN [CSISTG].[dbo].[item_mst] im ON coi.item = im.item AND coi.site_ref = im.site_ref
WHERE coi.site_ref = 'BENN'
    AND (coi.Uf_BENN_BoatSerialNumber IS NULL OR coi.Uf_BENN_BoatSerialNumber = '')
GROUP BY im.product_code
ORDER BY row_count DESC;

-- 6. Check if BS1 (base boat) exists at all
SELECT
    'Rows with BS1 product code' as check_name,
    COUNT(*) as total_bs1,
    COUNT(CASE WHEN coi.Uf_BENN_BoatSerialNumber IS NOT NULL THEN 1 END) as bs1_with_serial,
    COUNT(CASE WHEN coi.Uf_BENN_BoatSerialNumber IS NULL THEN 1 END) as bs1_without_serial
FROM [CSISTG].[dbo].[coitem_mst] coi
LEFT JOIN [CSISTG].[dbo].[item_mst] im ON coi.item = im.item AND coi.site_ref = im.site_ref
WHERE coi.site_ref = 'BENN'
    AND im.product_code = 'BS1';

-- 7. Sample of boats with serial numbers
SELECT TOP 20
    coi.Uf_BENN_BoatSerialNumber,
    coi.Uf_BENN_BoatModel,
    coi.co_num,
    COUNT(*) as line_count,
    STRING_AGG(im.product_code, ', ') as product_codes
FROM [CSISTG].[dbo].[coitem_mst] coi
LEFT JOIN [CSISTG].[dbo].[item_mst] im ON coi.item = im.item AND coi.site_ref = im.site_ref
WHERE coi.site_ref = 'BENN'
    AND coi.Uf_BENN_BoatSerialNumber IS NOT NULL
    AND coi.Uf_BENN_BoatSerialNumber != ''
GROUP BY coi.Uf_BENN_BoatSerialNumber, coi.Uf_BENN_BoatModel, coi.co_num
ORDER BY line_count DESC;

-- 8. Check date range of data
SELECT
    'Date range of orders' as check_name,
    MIN(coi.order_date) as earliest_order,
    MAX(coi.order_date) as latest_order,
    COUNT(DISTINCT coi.co_num) as unique_orders
FROM [CSISTG].[dbo].[coitem_mst] coi
WHERE coi.site_ref = 'BENN';

-- 9. Check our specific filter that's being used
SELECT
    'Rows matching our import filter' as check_name,
    COUNT(*) as row_count,
    COUNT(DISTINCT coi.Uf_BENN_BoatSerialNumber) as boat_count
FROM [CSISTG].[dbo].[coitem_mst] coi
LEFT JOIN [CSISTG].[dbo].[item_mst] im ON coi.item = im.item AND coi.site_ref = im.site_ref
WHERE coi.site_ref = 'BENN'
    AND coi.Uf_BENN_BoatSerialNumber IS NOT NULL
    AND coi.Uf_BENN_BoatSerialNumber != ''
    AND im.product_code IN (
        'BS1', 'EN7', 'ENG', 'ENI', 'EN9', 'EN4', 'ENA', 'EN2', 'EN3', 'EN8', 'ENT',
        'ACC', 'H1', 'H1P', 'H1V', 'H1I', 'H1F', 'H3A', 'H5',
        'L0', 'L2', 'L12',
        '003', '008', '024', '090', '302',
        'ASY',
        '010', '011', '005', '006', '015', '017', '023', '029', '030'
    );

-- 10. Compare BoatModelNo field vs BoatSerialNumber field
SELECT
    'Rows with BoatModelNo' as field_name,
    COUNT(*) as row_count
FROM [CSISTG].[dbo].[coitem_mst]
WHERE site_ref = 'BENN'
    AND Uf_BENN_BoatModel IS NOT NULL
    AND Uf_BENN_BoatModel != ''
UNION ALL
SELECT
    'Rows with BoatSerialNumber' as field_name,
    COUNT(*) as row_count
FROM [CSISTG].[dbo].[coitem_mst]
WHERE site_ref = 'BENN'
    AND Uf_BENN_BoatSerialNumber IS NOT NULL
    AND Uf_BENN_BoatSerialNumber != '';

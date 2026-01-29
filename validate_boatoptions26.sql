-- ============================================================================
-- BoatOptions26_test Validation Queries
-- ============================================================================
-- Run these to validate the imported data
-- ============================================================================

USE warrantyparts_test;

-- 1. Overall Statistics
SELECT
    'Overall Statistics' as check_name,
    COUNT(*) as total_rows,
    COUNT(DISTINCT ERP_OrderNo) as unique_orders,
    COUNT(DISTINCT CASE WHEN BoatSerialNo IS NOT NULL AND BoatSerialNo != ''
                        THEN BoatSerialNo END) as boats_with_serial,
    COUNT(DISTINCT CASE WHEN BoatModelNo IS NOT NULL AND BoatModelNo != ''
                        THEN BoatModelNo END) as boats_with_model,
    COUNT(DISTINCT ItemMasterProdCat) as unique_product_codes,
    MIN(InvoiceDate) as earliest_invoice,
    MAX(InvoiceDate) as latest_invoice
FROM BoatOptions26_test;

-- 2. Product Code Distribution
SELECT
    ItemMasterProdCat as product_code,
    COUNT(*) as row_count,
    COUNT(DISTINCT ERP_OrderNo) as order_count,
    COUNT(DISTINCT CASE WHEN BoatSerialNo IS NOT NULL AND BoatSerialNo != ''
                        THEN BoatSerialNo END) as boats_with_serial,
    ROUND(SUM(ExtSalesAmount), 2) as total_sales_amount
FROM BoatOptions26_test
GROUP BY ItemMasterProdCat
ORDER BY row_count DESC;

-- 3. Orders with Complete Builds (BOA + ENG)
SELECT
    'Complete Builds (BOA + ENG)' as metric,
    COUNT(DISTINCT ERP_OrderNo) as order_count
FROM (
    SELECT DISTINCT ERP_OrderNo
    FROM BoatOptions26_test
    WHERE ItemMasterProdCat = 'BOA'
    INTERSECT
    SELECT DISTINCT ERP_OrderNo
    FROM BoatOptions26_test
    WHERE ItemMasterProdCat = 'ENG'
) complete_builds;

-- 4. Sample Complete Boat Build
SELECT
    ERP_OrderNo,
    BoatSerialNo,
    BoatModelNo,
    ItemMasterProdCat,
    ItemDesc1,
    ExtSalesAmount,
    InvoiceNo
FROM BoatOptions26_test
WHERE ERP_OrderNo IN (
    SELECT ERP_OrderNo
    FROM BoatOptions26_test
    WHERE ItemMasterProdCat = 'BOA'
    LIMIT 1
)
ORDER BY
    CASE ItemMasterProdCat
        WHEN 'BOA' THEN 1
        WHEN 'ENG' THEN 2
        WHEN 'ACY' THEN 3
        ELSE 4
    END,
    LineNo;

-- 5. MSRP Calculation Example (First BOA order)
SELECT
    ERP_OrderNo,
    BoatSerialNo,
    BoatModelNo,
    SUM(CASE WHEN ItemMasterProdCat = 'BOA' THEN ExtSalesAmount ELSE 0 END) as base_boat_msrp,
    SUM(CASE WHEN ItemMasterProdCat = 'ENG' THEN ExtSalesAmount ELSE 0 END) as engine_msrp,
    SUM(CASE WHEN ItemMasterProdCat = 'ACY' THEN ExtSalesAmount ELSE 0 END) as accessories_msrp,
    SUM(CASE WHEN ItemMasterProdCat = 'PPR' THEN ExtSalesAmount ELSE 0 END) as prep_msrp,
    SUM(ExtSalesAmount) as total_msrp
FROM BoatOptions26_test
WHERE ERP_OrderNo IN (
    SELECT ERP_OrderNo
    FROM BoatOptions26_test
    WHERE ItemMasterProdCat = 'BOA'
    LIMIT 1
)
GROUP BY ERP_OrderNo, BoatSerialNo, BoatModelNo;

-- 6. Top 10 Boats by MSRP
SELECT
    ERP_OrderNo,
    BoatSerialNo,
    BoatModelNo,
    COUNT(*) as line_items,
    SUM(ExtSalesAmount) as total_msrp
FROM BoatOptions26_test
WHERE ItemMasterProdCat IN ('BOA', 'ENG', 'ACY')
GROUP BY ERP_OrderNo, BoatSerialNo, BoatModelNo
ORDER BY total_msrp DESC
LIMIT 10;

-- 7. Data Quality Checks
SELECT
    'Data Quality' as check_name,
    COUNT(CASE WHEN ERP_OrderNo IS NULL THEN 1 END) as missing_order_no,
    COUNT(CASE WHEN ItemNo IS NULL THEN 1 END) as missing_item_no,
    COUNT(CASE WHEN ExtSalesAmount IS NULL THEN 1 END) as missing_price,
    COUNT(CASE WHEN ItemMasterProdCat IS NULL THEN 1 END) as missing_prod_cat,
    COUNT(CASE WHEN ExtSalesAmount < 0 THEN 1 END) as negative_amounts
FROM BoatOptions26_test;

-- 8. Series Distribution
SELECT
    Series,
    COUNT(*) as row_count,
    COUNT(DISTINCT ERP_OrderNo) as order_count,
    COUNT(DISTINCT CASE WHEN ItemMasterProdCat = 'BOA' THEN ERP_OrderNo END) as boats
FROM BoatOptions26_test
WHERE Series IS NOT NULL AND Series != ''
GROUP BY Series
ORDER BY row_count DESC;

-- 9. Invoice Date Distribution (by year)
SELECT
    LEFT(CAST(InvoiceDate AS CHAR), 4) as year,
    COUNT(*) as row_count,
    COUNT(DISTINCT ERP_OrderNo) as order_count
FROM BoatOptions26_test
WHERE InvoiceDate IS NOT NULL
GROUP BY LEFT(CAST(InvoiceDate AS CHAR), 4)
ORDER BY year DESC;

-- 10. Comparison with BoatOptions25_test
SELECT
    '25_test' as table_name,
    COUNT(*) as rows,
    COUNT(DISTINCT BoatSerialNo) as boats_serial,
    COUNT(DISTINCT ERP_OrderNo) as orders
FROM BoatOptions25_test
UNION ALL
SELECT
    '26_test' as table_name,
    COUNT(*) as rows,
    COUNT(DISTINCT BoatSerialNo) as boats_serial,
    COUNT(DISTINCT ERP_OrderNo) as orders
FROM BoatOptions26_test;

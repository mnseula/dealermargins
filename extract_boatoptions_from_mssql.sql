-- ============================================================================
-- Extract Boat Options from MSSQL for BoatOptions25 Table
-- ============================================================================
-- This query extracts all physical items (excluding configuration items)
-- from MSSQL sales orders and formats them for the MySQL BoatOptions25 table
-- ============================================================================

SELECT
    ser.ser_num AS BoatSerialNo,
    coi.item AS ItemNo,
    itm.description AS ItemDesc1,
    pc.description AS MCTDesc,
    itm.product_code AS ItemMasterMCT,
    itm.Uf_BENN_ProductCategory AS ItemMasterProdCat,
    coi.price * coi.qty_ordered AS ExtSalesAmount,
    coi.qty_ordered AS QuantitySold,
    coi.co_line AS LineNo,
    coi.co_num AS OrderNumber,
    ser.item AS BoatModelNo
FROM CSISTG.dbo.serial_mst ser
JOIN CSISTG.dbo.coitem_mst coi
    ON ser.ref_num = coi.co_num
    AND ser.site_ref = coi.site_ref
JOIN CSISTG.dbo.item_mst itm
    ON coi.item = itm.item
    AND coi.site_ref = itm.site_ref
LEFT JOIN CSISTG.dbo.prodcode_mst pc
    ON itm.product_code = pc.product_code
    AND itm.site_ref = pc.site_ref
WHERE ser.site_ref = 'BENN'
  -- Only include sales orders (SO prefix)
  AND ser.ref_num LIKE 'SO%'

  -- EXCLUDE: BOM Placeholder items
  AND itm.Uf_BENN_ProductCategory <> '111'

  -- EXCLUDE: Financial/Discount items by product code (MCT)
  AND itm.product_code NOT IN (
    'DIC','DIF','DIP','DIR','DIA','DIW',  -- Dealer incentives/funds
    'LOY','PRD','VOD','DIS','CAS',         -- Discounts/loyalty
    'SHO','GRO','ZZZ','WAR','DLR',         -- Show/grow/warranty
    'FRE','FRP','FRT',                     -- Freight
    'A0','A0C','A0G','A0I','A0P','A0T','A0V','A1','A6','FUR',
    'TAX','INT','LAB','MKT','ADV','DLM',   -- Tax/interest/labor/marketing
    'DMG','DSP','OTD','OTI','PGA','MKA','MIG','DON','REW','SNAP'
  )

  -- EXCLUDE: Financial/Discount items by product category
  AND itm.Uf_BENN_ProductCategory NOT LIKE 'C%'   -- All discount categories
  AND itm.Uf_BENN_ProductCategory NOT LIKE 'DI%'  -- Dealer incentive categories
  AND itm.Uf_BENN_ProductCategory NOT LIKE 'W%'   -- Warranty categories
  AND itm.Uf_BENN_ProductCategory NOT LIKE 'N%'   -- Freight/handling categories
  AND itm.Uf_BENN_ProductCategory NOT LIKE 'PA%'  -- Price adjustment categories
  AND itm.Uf_BENN_ProductCategory NOT LIKE 'X%'   -- Misc categories
  AND itm.Uf_BENN_ProductCategory NOT IN ('GRO','LAB','TAX','SHO','INT','PGA','VOI','S1','S3','S4','S5')

  -- EXCLUDE: Special handling for DIS items (allow only specific ones)
  AND NOT (itm.product_code = 'DIS' AND coi.item <> 'NPPNPRICE16S')

  -- EXCLUDE: Special handling for ENZ items (allow only VALUE items)
  AND NOT (itm.product_code = 'ENZ' AND itm.description NOT LIKE '%VALUE%')

  -- EXCLUDE: $0 configuration items (colors, vinyl, canvas selections)
  AND NOT (
    itm.Uf_BENN_ProductCategory IN ('H1','H1I','H1P','H1V','H3U','H5','L0','S2','ASY')
    AND COALESCE(coi.price * coi.qty_ordered, 0) = 0
  )

  -- EXCLUDE: ACY items with $0 (configuration selections)
  AND NOT (
    itm.product_code = 'ACY'
    AND COALESCE(coi.price * coi.qty_ordered, 0) = 0
  )

ORDER BY
  ser.ser_num,
  -- Sort by item type for logical grouping
  CASE pc.description
    WHEN 'Pontoon Boats OB' THEN 1
    WHEN 'Pontoon Boats IO' THEN 1
    WHEN 'Lower Unit Eng' THEN 2
    WHEN 'ENGINES' THEN 3
    WHEN 'Engine' THEN 3
    WHEN 'Engine IO' THEN 3
    WHEN 'Engine Accessory' THEN 4
    WHEN 'PRE-RIG' THEN 5
    WHEN 'Prerig' THEN 5
    WHEN 'Accessory' THEN 6
    WHEN 'Trailer' THEN 7
    ELSE 8
  END,
  coi.co_line;

-- ============================================================================
-- Expected Output Columns for MySQL BoatOptions25 Table:
-- ============================================================================
-- BoatSerialNo         nvarchar(20)    - Boat serial number
-- ItemNo               nvarchar(30)    - Item number
-- ItemDesc1            nvarchar(40)    - Item description
-- MCTDesc              nvarchar(50)    - Product code description
-- ItemMasterMCT        nvarchar(10)    - Product code (ACY, BOA, ENG, etc.)
-- ItemMasterProdCat    nvarchar(3)     - Product category (ACC, BL7, EN3, etc.)
-- ExtSalesAmount       decimal         - Extended sales amount (price * qty)
-- QuantitySold         decimal         - Quantity sold
-- LineNo               int             - Order line number
-- OrderNumber          nvarchar(10)    - Sales order number
-- BoatModelNo          nvarchar(30)    - Boat model number
-- ============================================================================

-- ============================================================================
-- Test Query - Get sample data for one boat
-- ============================================================================
-- Uncomment to test with a specific serial:
-- WHERE ser.ser_num = 'ETWC5755C525'
--   AND ... (rest of filters)
-- ============================================================================

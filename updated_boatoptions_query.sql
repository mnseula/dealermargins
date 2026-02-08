-- Updated Part 2: CPQ Configuration Attributes
-- Add these new fields to the SELECT in Part 2 of the query

SELECT
    LEFT(coi.Uf_BENN_BoatWebOrderNumber, 30) AS [WebOrderNo],
    LEFT(im.Uf_BENN_Series, 5) AS [C_Series],
    coi.qty_invoiced AS [QuantitySold],
    LEFT(co.type, 1) AS [Orig_Ord_Type],
    LEFT(coi.Uf_BENN_BoatModel, 14) AS [OptionSerialNo],
    -- Classify MCTDesc based on configuration attribute name
    CASE
        WHEN attr_detail.attr_name = 'Base Boat' THEN 'PONTOONS'
        WHEN attr_detail.attr_name LIKE '%Pre-Rig%'
             OR attr_detail.attr_name LIKE '%Rigging%'
             OR attr_detail.attr_name LIKE '%Pre Rig%' THEN 'PRE-RIG'
        WHEN attr_detail.Uf_BENN_Cfg_Price > 0 THEN 'ACCESSORIES'
        ELSE 'STANDARD FEATURES'
    END AS [MCTDesc],
    coi.co_line AS [LineSeqNo],
    coi.co_line AS [LineNo],
    LEFT(attr_detail.attr_name, 50) AS [ItemNo],
    NULL AS [ItemMasterProdCatDesc],
    LEFT(im.Uf_BENN_ProductCategory, 3) AS [ItemMasterProdCat],
    -- Classify ItemMasterMCT based on configuration attribute name
    CASE
        WHEN attr_detail.attr_name = 'Base Boat' THEN 'BOA'
        WHEN attr_detail.attr_name LIKE '%Pre-Rig%'
             OR attr_detail.attr_name LIKE '%Rigging%'
             OR attr_detail.attr_name LIKE '%Pre Rig%' THEN 'PRE'
        WHEN attr_detail.Uf_BENN_Cfg_Price > 0 THEN 'ACC'
        ELSE 'STD'
    END AS [ItemMasterMCT],
    LEFT(attr_detail.attr_value, 30) AS [ItemDesc1],
    LEFT(iim.inv_num, 30) AS [InvoiceNo],
    CASE
        WHEN ah.inv_date IS NOT NULL
        THEN CONVERT(INT, CONVERT(VARCHAR(8), ah.inv_date, 112))
        ELSE NULL
    END AS [InvoiceDate],
    CAST(ISNULL(attr_detail.Uf_BENN_Cfg_Price, 0) AS DECIMAL(10,2)) AS [ExtSalesAmount],
    LEFT(coi.co_num, 30) AS [ERP_OrderNo],
    LEFT(ser.ser_num, 15) AS [BoatSerialNo],
    LEFT(coi.Uf_BENN_BoatModel, 14) AS [BoatModelNo],
    ah.apply_to_inv_num AS [ApplyToNo],
    LEFT(coi.config_id, 30) AS [ConfigID],
    LEFT(attr_detail.attr_value, 100) AS [ValueText],
    co.order_date AS [order_date],
    co.external_confirmation_ref AS [external_confirmation_ref],
    -- NEW FIELDS BELOW --
    CAST(ISNULL(attr_detail.Uf_BENN_Cfg_MSRP, 0) AS DECIMAL(10,2)) AS [MSRP],
    LEFT(attr_detail.Uf_BENN_Cfg_Name, 100) AS [CfgName],
    LEFT(attr_detail.Uf_BENN_Cfg_Page, 50) AS [CfgPage],
    LEFT(attr_detail.Uf_BENN_Cfg_Screen, 50) AS [CfgScreen],
    LEFT(attr_detail.Uf_BENN_Cfg_Value, 100) AS [CfgValue],
    LEFT(attr_detail.attr_type, 20) AS [CfgAttrType]
FROM [CSISTG].[dbo].[coitem_mst] coi
INNER JOIN [CSISTG].[dbo].[cfg_attr_mst] attr_detail
    ON coi.config_id = attr_detail.config_id
    AND coi.site_ref = attr_detail.site_ref
    AND attr_detail.attr_value IS NOT NULL
    AND attr_detail.print_flag = 'E'
-- ... rest of joins remain the same ...


-- IMPORTANT: Also add these columns to Part 1 (regular items) with NULL values:
-- Add after [external_confirmation_ref]:
--   NULL AS [MSRP],
--   NULL AS [CfgName],
--   NULL AS [CfgPage],
--   NULL AS [CfgScreen],
--   NULL AS [CfgValue],
--   NULL AS [CfgAttrType]

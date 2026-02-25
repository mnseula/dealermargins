-- Troubleshoot missing line item for SO00935316 / ETWS0309L526
-- 24 LXS Fastback Arch, invoiced 2026-02-24, Crowe Marine Inc
-- Suspected missing: second engine (F250XSB2)
--
-- Changes vs production import query:
--   1. Date filter in Part 1 commented out (boat invoiced yesterday, not today)
--   2. Filtered to SO00935316 only

WITH BoatOrders AS (
    SELECT
        coi.co_num,
        coi.site_ref,
        COALESCE(
            MAX(CASE
                WHEN NULLIF(coi.Uf_BENN_BoatSerialNumber, '') LIKE 'ETW%'
                    THEN NULLIF(coi.Uf_BENN_BoatSerialNumber, '')
                WHEN ser.ser_num LIKE 'ETW%'
                    THEN ser.ser_num
                ELSE NULL
            END),
            MAX(NULLIF(coi.Uf_BENN_BoatSerialNumber, '')),
            MAX(ser.ser_num)
        ) AS Uf_BENN_BoatSerialNumber,
        MAX(NULLIF(coi.Uf_BENN_BoatModel, ''))  AS Uf_BENN_BoatModel,
        MAX(NULLIF(coi.config_id, ''))           AS config_id
    FROM [CSIPRD].[dbo].[coitem_mst] coi
    LEFT JOIN [CSIPRD].[dbo].[serial_mst] ser
        ON coi.co_num = ser.ref_num
        AND coi.co_line = ser.ref_line
        AND coi.co_release = ser.ref_release
        AND coi.item = ser.item
        AND coi.site_ref = ser.site_ref
        AND ser.ref_type = 'O'
    LEFT JOIN [CSIPRD].[dbo].[co_mst] co_bo
        ON coi.co_num = co_bo.co_num
        AND coi.site_ref = co_bo.site_ref
    WHERE coi.site_ref = 'BENN'
        AND (
            co_bo.external_confirmation_ref LIKE 'SO%'
            OR TRY_CAST(co_bo.external_confirmation_ref AS BIGINT) IS NOT NULL
        )
        AND (
            (coi.Uf_BENN_BoatSerialNumber IS NOT NULL AND coi.Uf_BENN_BoatSerialNumber != '')
            OR (coi.config_id IS NOT NULL AND coi.config_id != '')
            OR (ser.ser_num IS NOT NULL AND ser.ser_num != '')
        )
    GROUP BY coi.co_num, coi.site_ref
),
OrderedRows AS (

-- Part 1: Main order lines (boat, engine, prerigs, accessories)
SELECT
    LEFT(coi.Uf_BENN_BoatWebOrderNumber, 30)            AS [WebOrderNo],
    LEFT(im.Uf_BENN_Series, 5)                          AS [C_Series],
    coi.qty_invoiced                                    AS [QuantitySold],
    LEFT(co.type, 1)                                    AS [Orig_Ord_Type],
    LEFT(ser.ser_num, 12)                               AS [OptionSerialNo],
    pcm.description                                     AS [MCTDesc],
    coi.co_line                                         AS [LineSeqNo],
    coi.co_line                                         AS [LineNo],
    LEFT(coi.item, 15)                                  AS [ItemNo],
    NULL                                                AS [ItemMasterProdCatDesc],
    LEFT(im.Uf_BENN_ProductCategory, 3)                 AS [ItemMasterProdCat],
    LEFT(im.Uf_BENN_MaterialCostType, 10)               AS [ItemMasterMCT],
    LEFT(coi.description, 100)                          AS [ItemDesc1],
    LEFT(LTRIM(RTRIM(iim.inv_num)), 30)                 AS [InvoiceNo],
    CASE WHEN iim.tax_date IS NOT NULL
         THEN CONVERT(INT, CONVERT(VARCHAR(8), iim.tax_date, 112))
         ELSE NULL
    END                                                 AS [InvoiceDate],
    CAST((coi.price * coi.qty_invoiced) AS DECIMAL(10,2)) AS [ExtSalesAmount],
    LEFT(coi.co_num, 30)                                AS [ERP_OrderNo],
    LEFT(COALESCE(coi.Uf_BENN_BoatSerialNumber, bo.Uf_BENN_BoatSerialNumber), 15) AS [BoatSerialNo],
    LEFT(COALESCE(coi.Uf_BENN_BoatModel, bo.Uf_BENN_BoatModel), 14) AS [BoatModelNo],
    NULL                                                AS [ApplyToNo],
    ''                                                  AS [ConfigID],
    ''                                                  AS [ValueText],
    co.order_date                                       AS [order_date],
    co.external_confirmation_ref                        AS [external_confirmation_ref],
    NULL                                                AS [MSRP],
    NULL                                                AS [CfgName],
    NULL                                                AS [CfgPage],
    NULL                                                AS [CfgScreen],
    NULL                                                AS [CfgValue],
    NULL                                                AS [CfgAttrType]
FROM [CSIPRD].[dbo].[coitem_mst] coi
INNER JOIN BoatOrders bo
    ON coi.co_num = bo.co_num AND coi.site_ref = bo.site_ref
LEFT JOIN [CSIPRD].[dbo].[inv_item_mst] iim
    ON coi.co_num = iim.co_num AND coi.co_line = iim.co_line
    AND coi.co_release = iim.co_release AND coi.site_ref = iim.site_ref
LEFT JOIN [CSIPRD].[dbo].[co_mst] co
    ON coi.co_num = co.co_num AND coi.site_ref = co.site_ref
LEFT JOIN [CSIPRD].[dbo].[item_mst] im
    ON coi.item = im.item AND coi.site_ref = im.site_ref
LEFT JOIN [CSIPRD].[dbo].[prodcode_mst] pcm
    ON im.Uf_BENN_MaterialCostType = pcm.product_code AND im.site_ref = pcm.site_ref
LEFT JOIN [CSIPRD].[dbo].[serial_mst] ser
    ON coi.co_num = ser.ref_num AND coi.co_line = ser.ref_line
    AND coi.co_release = ser.ref_release AND coi.item = ser.item
    AND coi.site_ref = ser.site_ref AND ser.ref_type = 'O'
WHERE coi.site_ref = 'BENN'
    AND TRY_CAST(co.external_confirmation_ref AS BIGINT) IS NOT NULL
    AND iim.inv_num IS NOT NULL
    AND coi.qty_invoiced > 0
    -- Date filter removed to see all invoiced lines regardless of date
    -- AND CAST(iim.tax_date AS DATE) = CAST(GETDATE() AS DATE)

UNION ALL

-- Part 2: Configuration attributes for CPQ invoiced items
SELECT
    LEFT(coi.Uf_BENN_BoatWebOrderNumber, 30)            AS [WebOrderNo],
    LEFT(im.Uf_BENN_Series, 5)                          AS [C_Series],
    coi.qty_invoiced                                    AS [QuantitySold],
    LEFT(co.type, 1)                                    AS [Orig_Ord_Type],
    LEFT(coi.Uf_BENN_BoatModel, 14)                     AS [OptionSerialNo],
    CASE
        WHEN attr_detail.attr_name = 'Base Boat' THEN 'PONTOONS'
        WHEN attr_detail.attr_name LIKE '%Pre-Rig%'
          OR attr_detail.attr_name LIKE '%Rigging%'
          OR attr_detail.attr_name LIKE '%Pre Rig%' THEN 'PRE-RIG'
        WHEN attr_detail.Uf_BENN_Cfg_Price > 0 THEN 'ACCESSORIES'
        ELSE 'STANDARD FEATURES'
    END                                                 AS [MCTDesc],
    coi.co_line                                         AS [LineSeqNo],
    coi.co_line                                         AS [LineNo],
    LEFT(attr_detail.attr_name, 50)                     AS [ItemNo],
    NULL                                                AS [ItemMasterProdCatDesc],
    LEFT(im.Uf_BENN_ProductCategory, 3)                 AS [ItemMasterProdCat],
    CASE
        WHEN attr_detail.attr_name = 'Base Boat' THEN 'BOA'
        WHEN attr_detail.attr_name LIKE '%Pre-Rig%'
          OR attr_detail.attr_name LIKE '%Rigging%'
          OR attr_detail.attr_name LIKE '%Pre Rig%' THEN 'PRE'
        WHEN attr_detail.Uf_BENN_Cfg_Price > 0 THEN 'ACC'
        ELSE 'STD'
    END                                                 AS [ItemMasterMCT],
    LEFT(attr_detail.attr_value, 100)                   AS [ItemDesc1],
    LEFT(LTRIM(RTRIM(iim.inv_num)), 30)                 AS [InvoiceNo],
    CASE WHEN iim.tax_date IS NOT NULL
         THEN CONVERT(INT, CONVERT(VARCHAR(8), iim.tax_date, 112))
         ELSE NULL
    END                                                 AS [InvoiceDate],
    CAST(ISNULL(attr_detail.Uf_BENN_Cfg_Price, 0) AS DECIMAL(10,2)) AS [ExtSalesAmount],
    LEFT(coi.co_num, 30)                                AS [ERP_OrderNo],
    LEFT(ser.ser_num, 15)                               AS [BoatSerialNo],
    LEFT(coi.Uf_BENN_BoatModel, 14)                     AS [BoatModelNo],
    NULL                                                AS [ApplyToNo],
    LEFT(coi.config_id, 30)                             AS [ConfigID],
    LEFT(attr_detail.attr_value, 100)                   AS [ValueText],
    co.order_date                                       AS [order_date],
    co.external_confirmation_ref                        AS [external_confirmation_ref],
    CAST(ISNULL(attr_detail.Uf_BENN_Cfg_MSRP, 0) AS DECIMAL(10,2)) AS [MSRP],
    LEFT(attr_detail.Uf_BENN_Cfg_Name, 100)             AS [CfgName],
    LEFT(attr_detail.Uf_BENN_Cfg_Page, 50)              AS [CfgPage],
    LEFT(attr_detail.Uf_BENN_Cfg_Screen, 50)            AS [CfgScreen],
    LEFT(attr_detail.Uf_BENN_Cfg_Value, 100)            AS [CfgValue],
    LEFT(attr_detail.attr_type, 20)                     AS [CfgAttrType]
FROM [CSIPRD].[dbo].[coitem_mst] coi
INNER JOIN [CSIPRD].[dbo].[cfg_attr_mst] attr_detail
    ON coi.config_id = attr_detail.config_id AND coi.site_ref = attr_detail.site_ref
    AND attr_detail.attr_value IS NOT NULL AND attr_detail.print_flag = 'E'
LEFT JOIN [CSIPRD].[dbo].[cfg_comp_mst] ccm
    ON attr_detail.config_id = ccm.config_id AND attr_detail.comp_id = ccm.comp_id
    AND attr_detail.site_ref = ccm.site_ref
LEFT JOIN [CSIPRD].[dbo].[inv_item_mst] iim
    ON coi.co_num = iim.co_num AND coi.co_line = iim.co_line
    AND coi.co_release = iim.co_release AND coi.site_ref = iim.site_ref
LEFT JOIN [CSIPRD].[dbo].[co_mst] co
    ON coi.co_num = co.co_num AND coi.site_ref = co.site_ref
LEFT JOIN [CSIPRD].[dbo].[item_mst] im
    ON coi.item = im.item AND coi.site_ref = im.site_ref
LEFT JOIN [CSIPRD].[dbo].[serial_mst] ser
    ON coi.co_num = ser.ref_num AND coi.co_line = ser.ref_line
    AND coi.co_release = ser.ref_release AND coi.item = ser.item
    AND coi.site_ref = ser.site_ref AND ser.ref_type = 'O'
WHERE coi.config_id IS NOT NULL
    AND coi.site_ref = 'BENN'
    AND co.external_confirmation_ref LIKE 'SO%'
    AND coi.qty_invoiced > 0
    -- AND CAST(iim.tax_date AS DATE) = CAST(GETDATE() AS DATE)

)
SELECT
    [WebOrderNo], [C_Series], [QuantitySold], [Orig_Ord_Type], [OptionSerialNo],
    [MCTDesc],
    ROW_NUMBER() OVER (PARTITION BY [ERP_OrderNo] ORDER BY [LineSeqNo], [ItemNo]) AS [LineSeqNo],
    [LineNo], [ItemNo], [ItemMasterProdCatDesc], [ItemMasterProdCat], [ItemMasterMCT],
    [ItemDesc1], [InvoiceNo], [InvoiceDate], [ExtSalesAmount], [ERP_OrderNo],
    [BoatSerialNo], [BoatModelNo], [ApplyToNo], [ConfigID], [ValueText],
    [order_date], [external_confirmation_ref],
    [MSRP], [CfgName], [CfgPage], [CfgScreen], [CfgValue], [CfgAttrType]
FROM OrderedRows
WHERE [ERP_OrderNo] IN (
    SELECT DISTINCT [ERP_OrderNo]
    FROM OrderedRows
    WHERE [ItemMasterMCT] IN ('BOA', 'BOI') AND [ERP_OrderNo] = 'SO00935316'
)
ORDER BY [ERP_OrderNo], [LineSeqNo]

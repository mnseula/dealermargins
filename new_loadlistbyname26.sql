-- UPDATED BoatOptions26 Query (2026-02-08)
-- Added MSRP and CPQ configuration columns for proper CPQ boat support
-- This query will return ALL columns needed for window stickers

SELECT
    BoatSerialNo,
    BoatModelNo,
    Series,
    ERP_OrderNo,
    Orig_Ord_Type,
    InvoiceNo,
    ApplyToNo,
    WebOrderNo,
    InvoiceDate,
    LineNo,
    LineSeqNo,
    MCTDesc,
    ItemNo,
    ItemDesc1,
    OptionSerialNo,
    ItemMasterMCT,
    ItemMasterProdCat,
    ItemMasterProdCatDesc,
    QuantitySold,
    ExtSalesAmount,
    -- NEW COLUMNS ADDED FOR CPQ SUPPORT --
    MSRP,              -- Retail price from CPQ (Uf_BENN_Cfg_MSRP)
    CfgName,           -- CPQ configuration name (e.g., "Model", "batterySwitching")
    CfgPage,           -- CPQ page name
    CfgScreen,         -- CPQ screen name
    CfgValue,          -- CPQ value selected
    CfgAttrType,       -- CPQ attribute type
    order_date,        -- Order date
    external_confirmation_ref,  -- External reference
    ConfigID,          -- Configuration ID
    ValueText,         -- Value text
    C_Series           -- Series code
FROM warrantyparts.BoatOptions26
{FILTER}

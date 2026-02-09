-- ORIGINAL BoatOptions26 Query (BACKUP - 2026-02-08)
-- This is the query that loadByListName('BoatOptions26') used before adding MSRP support

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
    ExtSalesAmount
FROM warrantyparts.BoatOptions26
{FILTER}

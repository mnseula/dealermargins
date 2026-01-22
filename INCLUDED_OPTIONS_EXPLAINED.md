# Included Options - Why Result Set 4 is Empty

## Current Situation

When calling `GetWindowStickerData()` for 2026 models, **Result Set 4 (Included Options) is empty**.

**This is expected and correct behavior.**

## Why Result Set 4 is Empty

### Data Sources
1. **CPQ Data (Models, Pricing, Performance, Features)**
   - Loaded from Infor CPQ APIs
   - Contains **2026 models** (model IDs: 25QXFBWA, 25SSRSE, etc.)
   - 283 models loaded
   - Pricing and specifications current for 2026

2. **Sales Data (BoatOptions25_test table)**
   - Historical sales transactions
   - Contains **2020-2024 models** (model IDs: 22SSRSE, 24MFBSE, etc.)
   - 323,272 sales records
   - Shows what options were actually included when boats were sold

### The Gap
- **No overlap**: 2026 models haven't been sold yet
- **Zero models** exist in both CPQ data AND sales data
- Result Set 4 queries `BoatOptions25_test` for included options
- Since no 2026 models have sales history, result set is empty

## Verification Results

```
✅ Table BoatOptions25_test exists: 323,272 records
✅ Stored procedure queries correctly: WHERE ItemMasterProdCat = 'ACC'
❌ Model 25QXFBWA in sales data: 0 records
❌ Any 2026 models in sales data: 0 models

Models with most ACC items in sales database:
  - 22SSRSE: 3,275 ACC items
  - 22MFBSE: 3,100 ACC items
  - 24MSBSE: 2,970 ACC items
  (All 2020-2024 models)
```

## When Will Result Set 4 Show Data?

Result Set 4 will populate automatically when:

1. **2026 boats are sold** and transactions recorded in sales system
2. **Sales data flows** into BoatOptions25_test table
3. **Options are marked** with `ItemMasterProdCat = 'ACC'`
4. **Model IDs match** between CPQ and sales (e.g., 25QXFBWA)

No code changes needed - it will work automatically.

## Testing with Historical Data

To see Result Set 4 with actual data, you would need to:

1. Query a model that exists in both datasets (currently none)
2. OR load historical CPQ data for 2020-2024 models
3. OR wait for 2026 models to start selling

Example test if model existed:
```sql
-- This would work if 22SSRSE was in CPQ data
CALL GetWindowStickerData('22SSRSE', 'NICHOLS MARINE - NORMAN');
-- Would return 3,275 ACC items in Result Set 4
```

## Stored Procedure is Working Correctly

The `GetWindowStickerData` stored procedure logic is correct:

```sql
-- Result Set 4: Included Options from Sales Database (read-only)
SELECT DISTINCT
    ItemNo,
    ItemDesc1 AS ItemDescription,
    QuantitySold AS Quantity,
    ExtSalesAmount AS SalePrice,
    ExtSalesAmount AS MSRP
FROM BoatOptions25_test
WHERE BoatModelNo = p_model_id
  AND ItemMasterProdCat = 'ACC'
  AND ItemNo IS NOT NULL
  AND ItemNo != ''
ORDER BY ItemDesc1;
```

This query:
- ✅ Correctly filters by `ItemMasterProdCat = 'ACC'` (future-proof)
- ✅ Filters out NULL/empty item numbers
- ✅ Returns proper fields (ItemNo, Description, Quantity, Price)
- ✅ Orders by description

## Summary

| Item | Status | Notes |
|------|--------|-------|
| **CPQ Data** | ✅ Loaded | 283 models, 2026 year |
| **Sales Data** | ✅ Exists | 323K records, 2020-2024 models |
| **Stored Procedure** | ✅ Working | All 4 result sets returned |
| **Result Set 1** | ✅ Data | Model info |
| **Result Set 2** | ✅ Data | Performance packages |
| **Result Set 3** | ✅ Data | Standard features |
| **Result Set 4** | ⚠️ Empty | Expected - no sales history for 2026 models yet |

## Current Window Sticker Output

```sql
CALL GetWindowStickerData('25QXFBWA', 'NICHOLS MARINE - NORMAN');
```

**Returns:**
- ✅ Model: 25QXFBWA, QX Series, 28'-3", 15 seats, $103,726
- ✅ Performance: 5 packages (25_IN_25, ESP_25, ESP+_25, SPS+_25, TWIN_ELLIPTICAL_25)
- ✅ Standard Features: Console, Exterior, Interior, Warranty (organized by area)
- ⚠️ Included Options: Empty (no sales history yet for this 2026 model)

This is **expected and correct** behavior for new model year boats.

# EOS Backward Compatibility System

## Overview

The window sticker generation system now supports **backward compatibility** by automatically falling back to EOS database when a model is not found in the CPQ system.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  GetWindowStickerData(model_id, dealer_id, year, identifier)│
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │  Model exists in CPQ?         │
         └───────┬───────────────┬───────┘
                 │               │
          ✓ YES  │               │  ✗ NO
                 │               │
         ┌───────▼───────┐   ┌───▼──────────┐
         │   CPQ PATH    │   │  EOS FALLBACK│
         │ (2025+ data)  │   │ (pre-2025)   │
         └───────────────┘   └──────────────┘
                 │               │
                 ├───────────────┤
                 │ 4 Result Sets │
                 └───────────────┘
```

## How It Works

### 1. Model Detection
- Checks if `model_id` exists in `warrantyparts_test.Models`
- If **FOUND**: Uses CPQ system (Models, ModelPricing, ModelPerformance, ModelStandardFeatures)
- If **NOT FOUND**: Falls back to EOS system (Eos database)

### 2. EOS Fallback Process

**Step 1: Extract Base Model**
```sql
168SFSR → 168SF   (removes suffix: SR, SE, SA, etc.)
25QFBWASR → 25QFBWA
```

**Step 2: Query EOS Tables**
- **Model Info**: `warrantyparts.SerialNumberMaster`
- **Performance**: `Eos.perf_pkg_spec` (with DISTINCT)
- **Standards**: `Eos.standards_matrix_YYYY` (with DISTINCT)
- **Options**: `warrantyparts.BoatOptionsYY` (same for both)

**Step 3: Return Data**
- Adds `data_source` field: `'CPQ'` or `'EOS'`
- Returns same 4 result sets for compatibility

## Database Structure

### EOS Tables (Eos database)

**options_matrix_YYYY** (e.g., options_matrix_2024, options_matrix_2025)
- Stores available options per model
- Columns: SERIES, MODEL, PART, CATEGORY, OPT_NAME, etc.

**perf_pkg_spec**
- Performance package specifications
- Columns: MODEL, PKG_NAME, MAX_HP, CAP, WEIGHT, PONT_GAUGE, TRANSOM
- **Note**: Contains many variations of same model (handles with DISTINCT)

**standards_matrix_YYYY** (e.g., standards_matrix_2024)
- Standard features per model
- Columns: SERIES, MODEL, STANDARD, CATEGORY, OPT_NAME
- **Note**: May have duplicates (handles with DISTINCT)

### Production Tables (warrantyparts database)

**SerialNumberMaster**
- Boat production records
- Contains: BoatItemNo, Series, BoatDesc1, SerialModelYear, DealerNumber

**BoatOptionsYY** (e.g., BoatOptions24, BoatOptions25)
- Boat line items and options
- Used for accessories (ItemMasterProdCat = 'ACC')

## Usage Examples

### Example 1: CPQ Model (2025)
```bash
python3 generate_window_sticker.py 25QXFBWA 333836 2025
```
**Result**: Uses CPQ system
- Data Source: CPQ
- Full pricing, performance, and features from warrantyparts_test

### Example 2: EOS Model (2024)
```bash
python3 generate_window_sticker.py 168SFSR 166000 2024
```
**Result**: Uses EOS fallback
- Data Source: EOS
- Performance packages from Eos.perf_pkg_spec
- Standard features from Eos.standards_matrix_2024

### Example 3: Specific Boat by HIN
```bash
python3 generate_window_sticker.py 168SFSR 166000 2024 ETWR6364F425
```
**Result**: EOS fallback with specific boat filtering
- Filters accessories to specific HIN

## SQL Examples

### Direct SQL Call - CPQ Model
```sql
CALL GetWindowStickerData('25QXFBWA', '333836', 2025, NULL);
-- Returns: data_source = 'CPQ'
```

### Direct SQL Call - EOS Model
```sql
CALL GetWindowStickerData('168SFSR', '166000', 2024, NULL);
-- Returns: data_source = 'EOS'
```

## Data Differences

| Field                 | CPQ                | EOS               |
|-----------------------|--------------------|-------------------|
| **model_name**        | Full name          | NULL              |
| **length_feet**       | Numeric value      | NULL              |
| **beam_length**       | Numeric value      | NULL              |
| **seats**             | Numeric value      | NULL              |
| **msrp**              | Current price      | NULL              |
| **floorplan_desc**    | Short description  | Long description  |
| **Performance**       | Clean list         | May have variants |
| **Standards**         | Organized          | May have HTML     |

## Limitations & Notes

### EOS Data Characteristics
1. **No MSRP**: EOS doesn't store pricing in these tables
2. **No Dimensions**: Length, beam, seats not available
3. **Variations**: Performance packages may have slight naming differences
4. **HTML Entities**: Standard features may contain `&quot;`, `&amp;`, etc.
5. **Duplicates**: Even with DISTINCT, some variations may appear

### Backward Compatibility Benefits
✅ **Seamless**: No code changes needed for existing calls
✅ **Automatic**: Detects and switches between CPQ/EOS automatically
✅ **Historical**: Can generate stickers for any model year
✅ **Future-Proof**: New models go to CPQ, old models use EOS

## File Structure

```
/dealermargins/
├── stored_procedures_with_eos_fallback.sql  # Main procedure
├── load_eos_procedure.py                    # Loader script
├── generate_window_sticker.py               # Python generator
├── window_sticker_168SFSR_2024_EOS.txt     # Sample EOS output
└── EOS_BACKWARD_COMPATIBILITY.md           # This document
```

## Testing

### Test CPQ Model
```bash
python3 generate_window_sticker.py 168SF 333836 2025
```
Expected: Data Source: CPQ

### Test EOS Model
```bash
python3 generate_window_sticker.py 168SFSR 166000 2024
```
Expected: Data Source: EOS (Backward Compatibility Mode)

### Test Non-Existent Model
```bash
python3 generate_window_sticker.py NOTFOUND 333836 2024
```
Expected: Error - No model found

## Migration Path

**Phase 1 (Current)**: Hybrid system
- 2025+ models → CPQ
- Pre-2025 models → EOS fallback

**Phase 2 (Future)**: Gradual migration
- Import historical models to CPQ
- EOS remains as fallback

**Phase 3 (Long-term)**: Full CPQ
- All models in CPQ system
- EOS fallback for edge cases only

## Troubleshooting

### Issue: Model not found in either system
**Solution**: Check model ID format and year

### Issue: EOS returns no performance packages
**Solution**: Verify model exists in `Eos.perf_pkg_spec` with STATUS='Active'

### Issue: EOS returns too many duplicates
**Solution**: Already handled with DISTINCT, but data may have legitimate variations

### Issue: HTML entities in standard features
**Solution**: Normal for EOS data (e.g., `&quot;` = quote, `&amp;` = ampersand)

## Key Takeaways

1. **Transparent**: System automatically chooses correct data source
2. **Backward Compatible**: Works with all historical model data
3. **Forward Compatible**: New models use improved CPQ structure
4. **Maintainable**: Single stored procedure handles both paths
5. **Reliable**: Falls back gracefully when CPQ data unavailable

---

**Last Updated**: January 28, 2026
**Version**: 1.0
**Author**: CPQ & EOS Integration Team

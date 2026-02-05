# CPQ Import Fix - Get ALL Configuration Attributes

## Problem

The import was only getting **some** of the configuration attributes (46-50 rows per order) instead of **all** attributes (56-61 rows per order).

### Root Cause

Part 2 of the import query had overly restrictive filters:

```sql
AND attr_detail.attr_name = 'Description'
AND attr_detail.sl_field = 'jobmatl.description'
AND attr_detail.attr_type = 'Schema'
```

This only imported attributes where the attribute name was literally "Description", missing all the other configuration attributes like:
- ACCENT PANEL COLOR
- ACCENT PANEL TYPE
- Additional Display
- Aft Bimini Tops
- Base Boat
- BASE VINYL
- Battery Switching
- etc.

## Solution

**Removed the restrictive filters** to import ALL configuration attributes from `cfg_attr_mst`.

### Changes Made to `import_boatoptions_test.py`:

1. **Removed three filter conditions** (lines 201-203):
   ```sql
   -- REMOVED:
   -- AND attr_detail.attr_name = 'Description'
   -- AND attr_detail.sl_field = 'jobmatl.description'
   -- AND attr_detail.attr_type = 'Schema'
   ```

2. **Updated ItemNo mapping** (line 177):
   ```sql
   -- OLD:
   LEFT(ISNULL(ccm.comp_name, attr_detail.comp_id), 15) AS [ItemNo]

   -- NEW:
   LEFT(ISNULL(ccm.comp_name, attr_detail.attr_name), 30) AS [ItemNo]
   ```

   Now uses attribute name (e.g., "ACCENT PANEL COLOR") as ItemNo when component name is not available.

3. **Updated comment** (line 167):
   ```sql
   -- OLD: Part 2: Component "Description" attributes for invoiced, configured items (CPQ boats)
   -- NEW: Part 2: ALL configuration attributes for invoiced, configured items (CPQ boats)
   ```

## Expected Results

After running the import with these changes:

| Order No | Before (Missing) | After (Expected) | Attributes |
|----------|------------------|------------------|------------|
| SO00936068 | 50 rows (missing 6) | **56 rows** ✓ | All configuration attributes |
| SO00936066 | 48 rows (missing 13) | **61 rows** ✓ | All configuration attributes |
| SO00936047 | 46 rows | TBD | Configuration attributes |
| SO00936067 | 50 rows | TBD | Configuration attributes |

## Data Mapping

Each configuration attribute now maps to BoatOptions table as:

- **ItemNo**: Attribute name (e.g., "ACCENT PANEL COLOR")
- **ItemDesc1**: Attribute value (e.g., "No Accent")
- **ValueText**: Attribute value (e.g., "No Accent")
- **ConfigID**: Configuration GID (e.g., "BENN0000000000000000000000005299")

## Testing

1. Run the import:
   ```bash
   python3 import_boatoptions_test.py
   ```

2. Verify row counts:
   ```sql
   SELECT
       ERP_OrderNo,
       COUNT(*) as ImportedRows
   FROM BoatOptions26
   WHERE ERP_OrderNo IN ('SO00936066', 'SO00936068')
   GROUP BY ERP_OrderNo;
   ```

   Expected:
   - SO00936068: 56 rows
   - SO00936066: 61 rows

3. Verify attribute types:
   ```sql
   SELECT ItemNo, ItemDesc1, ValueText
   FROM BoatOptions26
   WHERE ERP_OrderNo = 'SO00936068'
   ORDER BY LineSeqNo
   LIMIT 10;
   ```

   Should see attribute names like "ACCENT PANEL COLOR", "ACCENT PANEL TYPE", etc.

## Impact on JavaScript

**No JavaScript changes needed** from this fix. The ItemNo field will now have attribute names instead of empty/null values for CPQ configuration attributes.

However, the original JavaScript fix (packagePricing.js line 68) is still needed:
```javascript
window.model = boatmodel[0].ItemNo || boatmodel[0].ItemDesc1;
```

## Next Steps

1. ✅ Import script updated
2. ⏳ Run import to verify all attributes are captured
3. ⏳ Test JavaScript window sticker generation with CPQ boats
4. ⏳ Verify all configuration attributes display correctly

## Files Modified

- `import_boatoptions_test.py` - Import query filters updated
- `packagePricing.js` - Added ItemNo fallback (already committed)

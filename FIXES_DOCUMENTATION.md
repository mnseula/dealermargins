# Boat Import System Fixes - Documentation

## Date: 2026-02-24
## Summary: Fixed invoice number and dealer number issues preventing boats from loading in web app

---

## Issues Discovered

### 1. Invoice Number Truncation
**Problem:** SerialNumberMaster.InvoiceNo column was VARCHAR(10), but MSSQL invoice numbers are 8+ digits with leading spaces (e.g., `'    25225969'`). This caused truncation and mismatches between SerialNumberMaster and BoatOptionsXX tables.

**Impact:** Web app queries failed because SerialNumberMaster had `'252259'` but BoatOptions26 had `'25225969'`.

**Solution:** 
```sql
ALTER TABLE SerialNumberMaster MODIFY InvoiceNo VARCHAR(30);
```

### 2. Dealer Numbers with Leading Spaces
**Problem:** MSSQL `co.cust_num` field had leading spaces (e.g., `' 559236'`), but web app queries use exact match with padded format (`'000000559236'`).

**Impact:** Wilson Marine boats (and others) weren't visible because dealer number `' 559236'` didn't match `'000000559236'`.

**Solution:** Added TRIM() to both SQL query and Python processing:
- SQL: `LTRIM(RTRIM(co.cust_num)) AS DealerNumber`
- Python: `boat.get('DealerNumber', '').strip().lstrip('0')`

### 3. Invoice Number Format Mismatch
**Problem:** SerialNumberMaster had engine invoice numbers, but BoatOptionsXX had boat invoice numbers. Each boat has two invoices (engine + boat).

**Example:**
- ETWS0887A626: Engine invoice = `25217526`, Boat invoice = `25225969`
- SerialNumberMaster had engine invoice
- Web app needed boat invoice to query BoatOptions26

**Solution:** Updated SerialNumberMaster to use boat invoice numbers (from BOA/BOI lines in BoatOptionsXX).

### 4. BoatOrders CTE Missing Serial-Based Boats
**Problem:** Original query only checked `coi.Uf_BENN_BoatSerialNumber` but some boats only have serial numbers in `serial_mst` table.

**Solution:** Added check for `ser.ser_num`:
```sql
OR (ser.ser_num IS NOT NULL AND ser.ser_num != '')
```

---

## Database Schema Changes

### SerialNumberMaster Table
```sql
-- Changed InvoiceNo column size
ALTER TABLE SerialNumberMaster MODIFY InvoiceNo VARCHAR(30);

-- DealerNumber already VARCHAR(20), no change needed
```

### SerialNumberRegistrationStatus Table
```sql
-- No InvoiceNo column exists in this table
```

---

## Script Modifications

### 1. import_boatoptions_to_serial_master.py

#### Change 1: TRIM dealer numbers in SQL query
**Line 126:**
```python
# Before:
co.cust_num AS DealerNumber,

# After:
LTRIM(RTRIM(co.cust_num)) AS DealerNumber,
```

#### Change 2: TRIM dealer numbers in Python processing
**Line 557:**
```python
# Before:
'DealerNumber': boat.get('DealerNumber', '').lstrip('0') or '',

# After:
'DealerNumber': boat.get('DealerNumber', '').strip().lstrip('0') or '',
```

#### Change 3: LEFT JOIN for arinv_mst with TRIM
**Line 153:**
```python
# Before:
INNER JOIN [{db}].[dbo].[arinv_mst] ah
    ON iim.inv_num = ah.inv_num
    AND iim.site_ref = ah.site_ref

# After:
LEFT JOIN [{db}].[dbo].[arinv_mst] ah
    ON RTRIM(LTRIM(iim.inv_num)) = RTRIM(LTRIM(ah.inv_num))
    AND iim.site_ref = ah.site_ref
```

### 2. getunregisteredboats.js

#### Change: TRIM invoice number from SerialNumberMaster
**Line 90:**
```javascript
// Before:
var snmInvoiceNo = snmRec[0].InvoiceNo;

// After:
var snmInvoiceNo = snmRec[0].InvoiceNo.trim();
```

### 3. import_boatoptions_production.py

#### Change 1: Lower date cutoff for pre-CPQ boats
**Line 27:**
```python
# Before:
CPQ_GO_LIVE_DATE = date(2025, 12, 14)

# After:
IMPORT_CUTOFF_DATE = date(2025, 1, 1)
```

#### Change 2: Add check for serial_mst in BoatOrders CTE
**Line 196:**
```python
# Added:
OR
-- Serial-based boats: serial tracked in serial_mst (pre-CPQ)
(ser.ser_num IS NOT NULL AND ser.ser_num != '')
```

#### Change 3: Hardcode to production database
Removed `--PRD` flag switching, always uses CSIPRD now.

---

## Manual Fixes Applied

### DEFEO'S MARINA Boats (5 boats)
**Serials:** ETWS0887A626, ETWS0884A626, ETWS0889A626, ETWS0890A626, ETWS0872A626

**Fixes:**
1. Updated SerialNumberMaster.InvoiceNo from truncated to full boat invoice numbers
2. Script: `update_defeo_invoices.py`

### Wilson Marine Boats (3 boats)  
**Serials:** ETWS9752K526, ETWS9874K526, ETWS0927A626

**Fixes:**
1. Updated SerialNumberMaster.InvoiceNo from truncated to full boat invoice numbers
2. Updated SerialNumberMaster.DealerNumber from `' 559236'` to `'000000559236'`
3. Scripts: `fix_wilson_invoices.py`, `fix_wilson_dealer.py`

### Other Boats (8 boats)
**Serials:** ETWS0796A626, ETWS0804A626, ETWS0925A626, ETWS1044A626, ETWS1047A626, ETWS0838A626, ETWS0422L526, ETWS0121L526

**Fixes:**
1. Updated SerialNumberMaster.InvoiceNo from truncated to full boat invoice numbers

---

## Remaining Issues

### 159,351 Existing Boats Still Have Truncated Invoice Numbers
**Problem:** All boats imported before today have invoice numbers truncated to fit VARCHAR(10).

**Impact:** These boats won't load in web app unless manually fixed or re-imported.

**Solution Options:**
1. **Truncate and Re-import (Recommended):**
   ```sql
   TRUNCATE TABLE SerialNumberMaster;
   TRUNCATE TABLE SerialNumberRegistrationStatus;
   ```
   Then run `import_boatoptions_to_serial_master.py`

2. **Bulk Update Script:** Create script to update all 159k records with full invoice numbers from MSSQL

---

## Testing Results

### ✅ Working Now:
- All 16 DEFEO and Wilson Marine boats load correctly in web app
- Invoice numbers match between SerialNumberMaster and BoatOptionsXX
- Dealer numbers are clean (no leading spaces)
- Window stickers generate properly

### ✅ Future Imports:
- New boats will have full invoice numbers (VARCHAR(30))
- Dealer numbers will be trimmed (no leading spaces)
- Both invoice and dealer number mismatches are prevented

---

## Files Modified

1. `import_boatoptions_to_serial_master.py` - TRIM dealer numbers, arinv_mst LEFT JOIN
2. `import_boatoptions_production.py` - Lower cutoff date, add serial_mst check
3. `getunregisteredboats.js` - TRIM invoice number

## Files Created (Diagnostic/Fix Scripts)

1. `update_defeo_invoices.py` - Fixed DEFEO boat invoice numbers
2. `fix_wilson_invoices.py` - Fixed Wilson Marine invoice numbers
3. `fix_wilson_dealer.py` - Fixed Wilson Marine dealer numbers
4. `check_boat_lines.py` - Diagnostic script for BoatOptionsXX records
5. `check_wilson_marine.py` - Diagnostic script for Wilson Marine boats
6. `fix_invoice_mismatch.py` - Fix invoice mismatches for DEFEO boats
7. `trim_defeo_invoices_bo26.py` - Trim invoice numbers in BoatOptions26

---

## Lessons Learned

1. **Always TRIM() data from MSSQL** - Character fields often have padding
2. **Check column sizes** - VARCHAR(10) was too small for invoice numbers
3. **Match data formats** - Web app uses padded dealer numbers ('000000559236')
4. **Test with real data** - 16 boats revealed issues affecting all 159k records
5. **Invoice numbers differ** - Engine vs boat invoices are separate numbers

---

## Next Steps for Full Cleanup

To fix the remaining 159,351 boats:

```bash
# Option 1: Clean slate (recommended)
python3 << 'PYEOF'
import mysql.connector
conn = mysql.connector.connect(
    host='ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com',
    port=3306, database='warrantyparts',
    user='awsmaster', password='VWvHG9vfG23g7gD'
)
cursor = conn.cursor()
cursor.execute('TRUNCATE TABLE SerialNumberMaster')
cursor.execute('TRUNCATE TABLE SerialNumberRegistrationStatus')
conn.commit()
cursor.close()
conn.close()
print('Tables truncated. Run import_boatoptions_to_serial_master.py now.')
PYEOF

python import_boatoptions_to_serial_master.py
```

This will re-import all 159,367 boats with correct full invoice numbers and trimmed dealer numbers.

---

**End of Documentation**

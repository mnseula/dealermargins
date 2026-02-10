# Fix Test Boat ETWINVTEST01 → ETWINVTEST0122

## Problem
- Test boat ETWINVTEST01 is a 2022 model (22SFC) but serial ends in "01"
- Routes to wrong table: BoatOptions99_04 instead of BoatOptions22
- Can't update ERP (CREImport user is read-only)

## Solution: Manual Copy

### Step 1: Import from ERP
```bash
python import_boatoptions_production.py
```
This will import ETWINVTEST01 into BoatOptions99_04 (wrong table, but we'll fix it)

### Step 2: Copy to Correct Table
```bash
python manual_insert_test_boat.py
```
This will:
- Copy 57 rows from BoatOptions99_04 → BoatOptions22
- Change serial: ETWINVTEST01 → ETWINVTEST0122
- Delete old rows from BoatOptions99_04

### Step 3: Verify
```bash
python verify_etwinvtest0122.py
```

### Step 4: Test in Browser
1. Hard refresh (Ctrl+Shift+R / Cmd+Shift+R)
2. Search for **ETWINVTEST0122** (new serial)
3. Should load from BoatOptions22 ✅

## Note
Since we can't update ERP, every time you run the import it will re-import ETWINVTEST01 to the wrong table. Just run `manual_insert_test_boat.py` again to move it to the correct table.

## Better Alternative
Use a real production boat with a proper serial (ending in 22-26) instead of this test boat.

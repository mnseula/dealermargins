# CPQ Pricing Fix - Testing Plan

**Version:** 2026-02-12 (with safety checks)
**Purpose:** Verify CPQ pricing fix works correctly for both CPQ and legacy boats

---

## 🛡️ Safety Features Added

### 1. Multiple Boat Records Check
- **Code:** `if (boatmodel.length > 1)`
- **Protection:** Legacy boats with single BOA record skip CPQ extraction entirely
- **Log:** "Single boat record found - using standard pricing (legacy boat)"

### 2. "Base Boat" Validation
- **Code:** `isBaseBoot && hasValidMSRP`
- **Protection:** Only extracts if "Base Boat" exists AND has MSRP > 0
- **Log:** "No CPQ Base Boat line found - using standard pricing from boat record"

### 3. Null Safety in Calculations
- **Code:** `window.cpqBaseBoatDealerCost && Number(window.cpqBaseBoatDealerCost) > 0`
- **Protection:** Falls back to `ExtSalesAmount` if CPQ value is null/0/undefined
- **Log:** "Using CPQ dealer cost: $X" vs no log (uses standard)

### 4. MSRP Fallback
- **Code:** `window.cpqBaseBoatMSRP && Number(window.cpqBaseBoatMSRP) > 0`
- **Protection:** Falls back to `boatoptions[j].MSRP` if CPQ MSRP not available
- **Log:** "CPQ item with real MSRP from Base Boat" vs "Item with MSRP from record"

### 5. Empty Array Protection
- **Code:** `if (nonBaseBoats.length > 0)`
- **Protection:** If filtering removes all boats, keeps original array
- **Log:** "⚠️ Filtering would remove all boat records - keeping original"

---

## 📋 Test Cases

### Test Case 1: CPQ Boat with "Base Boat" Line ✅

**Example Boat:** ETWINVTEST0226 (23ML, M Series)

**Expected Database Records:**
- Line 1: "Base Boat, 23ML" → ExtSales: $41,131, MSRP: $58,171
- Line 2: "23ML, 23 M CRUISE" → ExtSales: $46,915, MSRP: $0

**Expected Console Logs:**
```
Multiple boat records found (2), checking for CPQ Base Boat line...
✅ CPQ Base Boat pricing extracted:
   MSRP: $58171
   Dealer Cost: $41131
Using CPQ dealer cost: $41131
CPQ item with real MSRP from Base Boat: 23 M CRUISE = $58171
```

**Expected Line Items Display:**
- Base Boat MSRP: **$58,171.00** (from CPQ)
- Base Boat Dealer Cost: **$41,131.00** (from CPQ)
- Options use their individual pricing

**Expected Calculations (0% margins):**
- Sale Price: **$41,131.00** (equals CPQ dealer cost)
- MSRP: **$58,171.00** (from CPQ, never changes)

**Expected Calculations (37% margins):**
- Sale Price: **$25,912.53** (= $41,131 × 0.63)
- MSRP: **$58,171.00** (from CPQ, never changes)

---

### Test Case 2: Legacy Boat (Single BOA Record) ✅

**Example:** Any 2024 or earlier boat with standard model codes (e.g., 22GBRSE, 24QFBSR)

**Expected Database Records:**
- Line 1: "22GBRSE, 22 G FASTBACK..." → ExtSales: $X, MSRP: $0

**Expected Console Logs:**
```
Single boat record found - using standard pricing (legacy boat)
```

**Expected Behavior:**
- Uses `ExtSalesAmount` from boat record (original behavior)
- MSRP is calculated from dealer cost (original behavior)
- NO CPQ extraction occurs
- `window.cpqBaseBoatMSRP = null`
- `window.cpqBaseBoatDealerCost = null`

**Verification:**
- Pricing matches historical window stickers
- No change from pre-fix behavior
- No errors in console

---

### Test Case 3: Legacy Boat with Multiple BOA Records (No "Base Boat") ✅

**Scenario:** Older boat that might have duplicate records but no "Base Boat" line

**Expected Database Records:**
- Line 1: "22GBRSE" → ExtSales: $X, MSRP: $0
- Line 2: "22GBRSE" (duplicate) → ExtSales: $Y, MSRP: $0

**Expected Console Logs:**
```
Multiple boat records found (2), checking for CPQ Base Boat line...
No CPQ Base Boat line found - using standard pricing from boat record
```

**Expected Behavior:**
- Filters out duplicates (original behavior)
- Uses first record's `ExtSalesAmount`
- MSRP calculated from dealer cost
- NO CPQ extraction (no "Base Boat" found)
- Falls back to legacy pricing logic

---

### Test Case 4: CPQ Boat Missing "Base Boat" Line ✅

**Scenario:** CPQ boat loaded incorrectly, only has configured boat line

**Expected Database Records:**
- Line 1: "23ML, 23 M CRUISE" → ExtSales: $46,915, MSRP: $0

**Expected Console Logs:**
```
Single boat record found - using standard pricing (legacy boat)
```

**Expected Behavior:**
- Treats as legacy boat (fallback)
- Uses `ExtSalesAmount = $46,915`
- Calculates MSRP from dealer cost
- NOT IDEAL but doesn't crash
- **Action:** Should investigate why "Base Boat" line is missing

---

### Test Case 5: "Base Boat" Line Has MSRP = 0 ✅

**Scenario:** CPQ data incomplete, "Base Boat" exists but no MSRP

**Expected Database Records:**
- Line 1: "Base Boat, 23ML" → ExtSales: $41,131, MSRP: $0
- Line 2: "23ML, 23 M CRUISE" → ExtSales: $46,915, MSRP: $0

**Expected Console Logs:**
```
Multiple boat records found (2), checking for CPQ Base Boat line...
No CPQ Base Boat line found - using standard pricing from boat record
```

**Expected Behavior:**
- Grep doesn't match (requires MSRP > 0)
- Falls back to using Line 2 pricing
- Uses `ExtSalesAmount = $46,915`
- **Action:** Should investigate why CPQ MSRP is missing

---

## 🧪 Testing Procedure

### Step 1: Test CPQ Boat (ETWINVTEST0226)

1. Upload updated JavaScript files to EOS
2. Open browser console (F12)
3. Load boat ETWINVTEST0226
4. **Verify Console Logs:**
   - ✅ "CPQ Base Boat pricing extracted"
   - ✅ "MSRP: $58171"
   - ✅ "Dealer Cost: $41131"
5. **Verify Line Items:**
   - Base boat MSRP = $58,171
   - Base boat dealer cost = $41,131
6. **Test 0% margins:**
   - Set all margins to 0%
   - Click Calculate
   - Sale price should = $41,131
7. **Test 37% margins:**
   - Set all margins to 37%
   - Click Calculate
   - Sale price should ≈ $25,913
   - MSRP stays $58,171

### Step 2: Test Legacy Boat (Pick any 2023-2024 boat)

1. Stay in EOS (don't refresh)
2. Select a legacy boat (e.g., 22GBRSE from 2024)
3. **Verify Console Logs:**
   - ✅ "Single boat record found - using standard pricing (legacy boat)"
   - OR "No CPQ Base Boat line found - using standard pricing"
4. **Verify Pricing:**
   - Matches historical window sticker
   - MSRP calculated (not from database)
   - No errors
5. **Test Margins:**
   - Apply dealer margins
   - Verify calculations match legacy formulas
   - Verify no console errors

### Step 3: Test Edge Cases

1. **Boat with no options** (just base boat)
2. **Boat with engine package** (verify engine pricing)
3. **IO boat** (Volvo/Mercury inboard/outboard)
4. **SV Series boat** (special pricing)

### Step 4: Regression Testing

**Pick 5 random boats from different years:**
- 1 from 2020 (legacy)
- 1 from 2021 (legacy)
- 1 from 2023 (legacy)
- 1 from 2024 (legacy)
- 1 from 2026 (CPQ)

**For each:**
1. Load boat
2. Check console for errors
3. Verify pricing looks reasonable
4. Click Calculate
5. Verify no JavaScript errors
6. Compare with old window sticker (if available)

---

## ✅ Success Criteria

### Must Have:
- ✅ CPQ boats load CPQ MSRP and dealer cost correctly
- ✅ Legacy boats continue to work without errors
- ✅ No JavaScript console errors for any boat type
- ✅ 0% margin test passes (sale = dealer cost)
- ✅ MSRP never changes for CPQ boats

### Nice to Have:
- Clear console logging showing which pricing path is used
- Helpful warnings if CPQ data is missing
- No performance degradation

---

## 🚨 Rollback Plan

If testing fails:

1. **Stop using new files immediately**
2. **Restore from backups:**
   - `old_packagePricing_before_cpq_pricing_fix.js` → `packagePricing.js`
   - `old_Calculate2021_before_cpq_pricing_fix.js` → `Calculate2021.js`
   - `old_calculate_before_cpq_pricing_fix.js` → `calculate.js`
3. **Upload restored files to EOS**
4. **Verify legacy boats work again**
5. **Report issue with details:**
   - Which boat failed
   - Console errors
   - Expected vs actual pricing

---

## 📊 Test Results Template

```
Date: _______________
Tester: _______________

CPQ Boat Test (ETWINVTEST0226):
- Console logs correct: [ ] YES [ ] NO
- MSRP = $58,171: [ ] YES [ ] NO
- Dealer cost = $41,131: [ ] YES [ ] NO
- 0% margin test: [ ] PASS [ ] FAIL
- 37% margin test: [ ] PASS [ ] FAIL
- Notes: ________________________________

Legacy Boat Test (Model: __________):
- No console errors: [ ] YES [ ] NO
- Pricing matches old sticker: [ ] YES [ ] NO [ ] N/A
- Margins calculate correctly: [ ] YES [ ] NO
- Notes: ________________________________

Edge Cases:
- Boat type: __________
- Result: [ ] PASS [ ] FAIL
- Notes: ________________________________

Overall Result: [ ] PASS [ ] FAIL
Approved for Production: [ ] YES [ ] NO

Signature: _______________
```

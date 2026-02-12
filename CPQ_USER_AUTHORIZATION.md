# CPQ User Authorization - Hide CPQ Logic from Unauthorized Users

**Date:** 2026-02-12
**Purpose:** Restrict CPQ boat functionality to authorized Bennington Marine users only

---

## Authorization Logic

Only this user can see CPQ boats:
- **web@bennington.com** (or WEB@BENNINGTON.COM)

**Authorization Check:**
```javascript
var user = getValue('EOS','USER');
var isCpqAuthorized = (user === 'WEB@BENNINGTON.COM' || user === 'web@bennington.com');
```

---

## Files Modified

### 1. **packagePricing.js**
**Lines 135-183: CPQ pricing extraction**

**Changes:**
- Added user authorization check at line 142
- CPQ pricing extraction only happens if `isCpqAuthorized === true`
- Unauthorized users see: `"⚠️ User not authorized for CPQ boats - using legacy pricing"`

**Before:**
```javascript
if (boatmodel.length > 1) {
    // Always extract CPQ pricing
    var baseBoatRec = $.grep(boatmodel, function (rec) { ... });
}
```

**After:**
```javascript
if (boatmodel.length > 1) {
    if (isCpqAuthorized) {
        // Only extract CPQ pricing if authorized
        var baseBoatRec = $.grep(boatmodel, function (rec) { ... });
    } else {
        console.log('⚠️ User not authorized for CPQ boats - using legacy pricing');
    }
}
```

---

### 2. **Calculate2021.js**
**Lines 33-72: Use CPQ pricing in calculations**

**Changes:**
- Added user authorization check at line 33
- CPQ dealer cost only used if `isCpqAuthorized === true`
- CPQ MSRP only used if `isCpqAuthorized === true`

**Before:**
```javascript
var dealercost = (mct === 'PONTOONS' && window.cpqBaseBoatDealerCost && Number(window.cpqBaseBoatDealerCost) > 0)
    ? window.cpqBaseBoatDealerCost
    : boatoptions[j].ExtSalesAmount;
```

**After:**
```javascript
var dealercost = (mct === 'PONTOONS' && isCpqAuthorized && window.cpqBaseBoatDealerCost && Number(window.cpqBaseBoatDealerCost) > 0)
    ? window.cpqBaseBoatDealerCost
    : boatoptions[j].ExtSalesAmount;
```

---

### 3. **calculate.js**
**Lines 33-72: Use CPQ pricing in calculations (pre-2021 boats)**

**Changes:**
- Identical to Calculate2021.js
- Added user authorization check
- CPQ dealer cost and MSRP only used if authorized

---

### 4. **getunregisteredboats.js**
**Lines 193-323: Apply CPQ margins and load CPQ data**

**Changes:**
- Added user authorization check at line 195
- CPQ margin logic only applies if `isCpqAuthorized === true`
- CPQ LHS data and standard features only load if authorized

**Before:**
```javascript
if (window.isCPQBoat) {
    console.log('CPQ boat detected - using CPQ margin logic');
    applyDealerMarginsCPQ();
}
```

**After:**
```javascript
if (isCpqAuthorized && window.isCPQBoat) {
    console.log('CPQ boat detected - using CPQ margin logic');
    applyDealerMarginsCPQ();
}
```

---

### 5. **print.js**
**Lines 40-660: Display CPQ data on window sticker**

**Changes:**
- Added user authorization check at line 40
- CPQ model name handling only if authorized (lines 49-60)
- CPQ LHS specs only displayed if authorized (line 442)
- CPQ performance specs only displayed if authorized (line 552)
- CPQ standard features only displayed if authorized (line 642)

**Before:**
```javascript
if (window.cpqLhsData && window.cpqLhsData.model_id) {
    console.log('Using CPQ LHS data for specs section');
}
```

**After:**
```javascript
if (isCpqAuthorized && window.cpqLhsData && window.cpqLhsData.model_id) {
    console.log('Using CPQ LHS data for specs section');
}
```

---

## Behavior Changes

### For Authorized Users (@BENNINGTONMARINE.COM + approved users):
- **No change** - CPQ boats work exactly as before
- See CPQ pricing, margins, LHS data, and standard features
- Console logs show "Using CPQ..." messages

### For Unauthorized Users (everyone else):
- **CPQ boats appear as legacy boats**
- Use ExtSalesAmount from boat record for dealer cost
- MSRP calculated from dealer cost (legacy formula)
- No CPQ LHS data displayed (fall back to legacy boat_specs if available)
- No CPQ standard features (fall back to legacy standards)
- Console shows: "⚠️ User not authorized for CPQ boats - using legacy pricing"

---

## Testing Instructions

### Test as Authorized User:
1. Login as user with @BENNINGTONMARINE.COM domain
2. Load boat ETWINVTEST0226
3. Verify console shows: "✅ CPQ Base Boat pricing extracted"
4. Verify MSRP = $58,171, Dealer Cost = $41,131
5. Verify LHS specs display correctly

### Test as Unauthorized User:
1. Login as dealer user (not @BENNINGTONMARINE.COM)
2. Load boat ETWINVTEST0226
3. Verify console shows: "⚠️ User not authorized for CPQ boats - using legacy pricing"
4. Verify boat loads but uses ExtSalesAmount (legacy pricing)
5. Verify no CPQ-specific data displays

---

## Security Notes

- Authorization is **client-side only** (JavaScript checks)
- Not a security feature - just hides UI/features from non-technical users
- Advanced users could still see CPQ data by modifying JavaScript
- Database access controls should handle true security restrictions

---

## Rollback Plan

If issues occur, restore from these backups:
- `old_packagePricing_before_cpq_pricing_fix.js` → `packagePricing.js`
- `old_Calculate2021_before_cpq_pricing_fix.js` → `Calculate2021.js`
- `old_calculate_before_cpq_pricing_fix.js` → `calculate.js`

---

## Future Improvements

When ready to enable for additional users:
1. Add more users to the authorization check
2. OR expand to include entire domains (e.g., @BENNINGTONMARINE.COM)
3. OR remove checks entirely to enable for all users

**To add additional authorized users:**
```javascript
var isCpqAuthorized = (user === 'WEB@BENNINGTON.COM' ||
                       user === 'web@bennington.com' ||
                       user === 'NEWUSER@EXAMPLE.COM');  // Add here
```

**To enable for entire domain:**
```javascript
var isCpqAuthorized = (user === 'WEB@BENNINGTON.COM' ||
                       user === 'web@bennington.com' ||
                       user.includes('@BENNINGTONMARINE.COM'));
```

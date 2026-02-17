# Fix: Quote Character Truncation in Poster Options

## Problem
Item descriptions containing quote characters (`"`) were being truncated when displayed in the poster/flyer options list. For example:
- `"12" Vivid UX Touchscreen Display` became `"12`
- `TRIPLE ESP (TRIPLE 32" TUBE PACKAGE)` became `TRIPLE ESP (TRIPLE 32`

## Root Cause
The HTML input fields used double quotes for the `value` attribute:
```html
<input type="text" value="12" Vivid UX Touchscreen Display" ...>
```

When the browser parsed this, the quote character in the description terminated the attribute early, causing truncation.

## Solution

### 1. Changed HTML Attribute Delimiters (`getposteroptions.js`)
Changed from double quotes to single quotes for all HTML attributes that contain user data:

**Before:**
```javascript
var newOptionItem1 = '<li class="ui-state-focus"><span class="ui-icon ui-icon-arrowthick-2-n-s"></span><input type="text" value="';
var newOptionItem2 = '" name = "tb';
var newOptionItem3 = '" size="75"><input onclick="xButtons()" class="opt-x" type="button" id="';
var newOptionItem4 = '" value="X"></li>';
```

**After:**
```javascript
var newOptionItem1 = '<li class="ui-state-focus" data-itemno=\'';
var newOptionItem2 = '\'><span class="ui-icon ui-icon-arrowthick-2-n-s"></span><input type="text" value=\'';
var newOptionItem3 = '\' name = \'tb';
var newOptionItem4 = '\' size="75"><input onclick="xButtons()" class="opt-x" type="button" value="X"></li>';
```

### 2. Added `data-itemno` Attribute for Reliable Storage (`getposteroptions.js`)
Instead of storing the item number in the button's `id` attribute (which gets corrupted), we now store it in a `data-itemno` attribute on the `<li>` element:

```javascript
optionsList += newOptionItem1 + escapeHtmlAttribute(itemno) + newOptionItem2 + escapeHtmlAttribute(itemdesc) + newOptionItem3 + escapeHtmlAttribute(itemno) + newOptionItem4;
```

### 3. Updated Save Function (`saveposter.js`)
Changed from reading the button's `id` to reading the `data-itemno` attribute:

**Before:**
```javascript
var part = $(this).context.lastChild.id;
var descTB = 'tb' + $(this).context.lastChild.id;
var desc = $('input:text[name="' + descTB  + '"]').val();
```

**After:**
```javascript
var part = $(this).attr('data-itemno');
var desc = $(this).find('input:text').first().val();
```

### 4. Added Corruption Recovery for Legacy Data (`getposteroptions.js`)
For previously saved boats with corrupted data, added automatic recovery:

```javascript
// Build lookup maps from original boat table
var descLookupMap = {};
var descToItemNoMap = {};
var validItemNos = {};

// Detect and fix corruption
var isItemNoInValidSet = validItemNos[itemno];
var isItemNoCorrupted = (!isItemNoInValidSet || itemno.indexOf(' ') > -1 || itemno.length > 30 || /^\d+$/.test(itemno));

if (isItemNoCorrupted) {
    // Try exact match first
    if (descToItemNoMap[upperItemDesc]) {
        itemno = descToItemNoMap[upperItemDesc];
    } else {
        // Try partial matching for CPQ boats
        for (var k = 0; k < originalBoatTableCopy.length; k++) {
            // Match logic here...
        }
    }
}
```

## Files Changed
1. `getposteroptions.js` - HTML template changes, corruption recovery
2. `saveposter.js` - Read from `data-itemno` attribute

## Testing
- New boats: Single quotes prevent quote characters from breaking HTML
- Previously saved corrupted boats: Automatic recovery restores full descriptions
- Legacy boats (90... item numbers): Protected from unintended changes

## Example Output

**Before Fix:**
```html
<input type="text" value="12" Vivid UX Touchscreen..." name="tb12" ...>
<!-- Browser sees: value="12" -->
```

**After Fix:**
```html
<input type="text" value='12" Vivid UX Touchscreen...' name='tb12" Vivid...' ...>
<!-- Browser sees entire value -->
```

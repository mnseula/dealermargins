# ESP Plus Performance Data Correction

## Issue
The ESP Plus (ESP+_25) performance data for model 25QXFBWA had incorrect specifications.

## Database Changes Made

### 1. Column Definition Update
**Changed:** `ModelPerformance.pontoon_gauge` column definition
- **From:** `DECIMAL(4,2)` - Only supported 2 decimal places (rounded 0.125 to 0.13)
- **To:** `DECIMAL(5,3)` - Supports 3 decimal places (stores 0.125 correctly)

### 2. ESP Plus Data Correction
**Model:** 25QXFBWA
**Performance Package:** ESP+_25
**Year:** 2025

#### Corrected Values:
- **Person Capacity:** 15/12/8 People
- **Hull Weight:** 4650.0 lbs
- **Max HP:** 500.0 HP
- **Pontoon Gauge:** 0.125 inches (1/8 inch)

## SQL to Reproduce

```sql
-- Update column definition
ALTER TABLE ModelPerformance
MODIFY COLUMN pontoon_gauge DECIMAL(5,3)
COMMENT 'Pontoon gauge thickness in inches (e.g., 0.125 = 1/8 inch)';

-- Update ESP Plus data
UPDATE ModelPerformance
SET
    max_hp = 500.0,
    person_capacity = '15/12/8 People',
    hull_weight = 4650.0,
    pontoon_gauge = 0.125
WHERE model_id = '25QXFBWA'
  AND perf_package_id = 'ESP+_25'
  AND year = 2025;
```

## Verification

```sql
CALL GetWindowStickerData('25QXFBWA', 'NICHOLS MARINE - NORMAN', 2025);
```

ESP Plus section should show:
- Max HP: 500.0 HP
- Person Capacity: 15/12/8 People
- Hull Weight: 4650.0 lbs
- Pontoon Gauge: 0.125

## Files Updated
- `database_schema.sql` - Updated pontoon_gauge column definition
- `ESP_PLUS_CORRECTION.md` - This documentation file

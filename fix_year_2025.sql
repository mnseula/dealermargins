-- ============================================================================
-- Fix Year: Update 2026 to 2025 in Database
-- ============================================================================
-- Run this once to correct the year in existing records
-- Future runs of load_cpq_data.py will use 2025 automatically
-- ============================================================================

USE warrantyparts_test;

-- Update ModelPricing records
UPDATE ModelPricing
SET year = 2025
WHERE year = 2026;

-- Update DealerMargins records
UPDATE DealerMargins
SET year = 2025
WHERE year = 2026;

-- Verify the changes
SELECT 'ModelPricing Records' as Table_Name,
       year,
       COUNT(*) as Record_Count
FROM ModelPricing
GROUP BY year
UNION ALL
SELECT 'DealerMargins Records' as Table_Name,
       year,
       COUNT(*) as Record_Count
FROM DealerMargins
GROUP BY year
ORDER BY Table_Name, year;

-- ============================================================================
-- Expected Results:
-- ModelPricing Records   2025   283
-- DealerMargins Records  2025   100
-- ============================================================================

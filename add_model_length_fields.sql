-- Add pontoon diameter and fuel capacity fields to Models table
-- These are populated from the base performance package

USE warrantyparts_test;

-- Add pontoon_gauge if it doesn't exist
SET @col_exists_gauge = (
    SELECT COUNT(*) 
    FROM information_schema.columns 
    WHERE table_schema = DATABASE() 
    AND table_name = 'Models' 
    AND column_name = 'pontoon_gauge'
);

SET @sql_gauge = IF(@col_exists_gauge = 0, 
    'ALTER TABLE Models ADD COLUMN pontoon_gauge DECIMAL(4,2) COMMENT "Pontoon diameter/gauge in inches" AFTER deck_length_num', 
    'SELECT "pontoon_gauge already exists" AS message'
);
PREPARE stmt FROM @sql_gauge;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Add fuel_capacity if it doesn't exist
SET @col_exists_fuel = (
    SELECT COUNT(*) 
    FROM information_schema.columns 
    WHERE table_schema = DATABASE() 
    AND table_name = 'Models' 
    AND column_name = 'fuel_capacity'
);

SET @sql_fuel = IF(@col_exists_fuel = 0, 
    'ALTER TABLE Models ADD COLUMN fuel_capacity VARCHAR(50) COMMENT "Fuel capacity range (e.g., 25 Gal. - 40 Gal.)" AFTER pontoon_gauge', 
    'SELECT "fuel_capacity already exists" AS message'
);
PREPARE stmt FROM @sql_fuel;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Verify columns were added
DESCRIBE Models;

-- Fix DealerMargins constraints for freight and prep
-- These should be dollar amounts (0-10000), not percentages (0-100)

USE warrantyparts_test;

-- Drop the incorrect constraints
ALTER TABLE DealerMargins DROP CHECK chk_freight_margin_range;
ALTER TABLE DealerMargins DROP CHECK chk_prep_margin_range;

-- Add new constraints with correct ranges (dollar amounts up to $10,000)
ALTER TABLE DealerMargins
    ADD CONSTRAINT chk_freight_margin_range CHECK (freight_margin BETWEEN 0 AND 10000);

ALTER TABLE DealerMargins
    ADD CONSTRAINT chk_prep_margin_range CHECK (prep_margin BETWEEN 0 AND 10000);

-- Verify the changes
SHOW CREATE TABLE DealerMargins;

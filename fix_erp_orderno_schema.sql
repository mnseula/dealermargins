-- =====================================================================
-- Fix ERP_OrderNo Column Type
-- =====================================================================
-- Changes ERP_OrderNo from INT to VARCHAR(30) in old BoatOptions tables
-- to support CPQ order numbers that start with "SO"
--
-- Affected tables: All tables before BoatOptions22
-- CPQ orders use format: SO00936074, SO00936067, etc.
-- INT column converts these to 0, losing the order number
--
-- Author: Claude Code
-- Date: 2026-02-10
-- =====================================================================

USE warrantyparts;

-- BoatOptionsBefore_05
ALTER TABLE BoatOptionsBefore_05 MODIFY COLUMN ERP_OrderNo VARCHAR(30);

-- BoatOptions99_04 (1999-2004)
ALTER TABLE BoatOptions99_04 MODIFY COLUMN ERP_OrderNo VARCHAR(30);

-- BoatOptions05_07 (2005-2007)
ALTER TABLE BoatOptions05_07 MODIFY COLUMN ERP_OrderNo VARCHAR(30);

-- BoatOptions08_10 (2008-2010)
ALTER TABLE BoatOptions08_10 MODIFY COLUMN ERP_OrderNo VARCHAR(30);

-- BoatOptions11_14 (2011-2014)
ALTER TABLE BoatOptions11_14 MODIFY COLUMN ERP_OrderNo VARCHAR(30);

-- BoatOptions15 (2015)
ALTER TABLE BoatOptions15 MODIFY COLUMN ERP_OrderNo VARCHAR(30);

-- BoatOptions16 (2016)
ALTER TABLE BoatOptions16 MODIFY COLUMN ERP_OrderNo VARCHAR(30);

-- BoatOptions17 (2017)
ALTER TABLE BoatOptions17 MODIFY COLUMN ERP_OrderNo VARCHAR(30);

-- BoatOptions18 (2018)
ALTER TABLE BoatOptions18 MODIFY COLUMN ERP_OrderNo VARCHAR(30);

-- BoatOptions19 (2019)
ALTER TABLE BoatOptions19 MODIFY COLUMN ERP_OrderNo VARCHAR(30);

-- BoatOptions20 (2020)
ALTER TABLE BoatOptions20 MODIFY COLUMN ERP_OrderNo VARCHAR(30);

-- BoatOptions21 (2021)
ALTER TABLE BoatOptions21 MODIFY COLUMN ERP_OrderNo VARCHAR(30);

-- Verify changes
SELECT
    TABLE_NAME,
    COLUMN_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'warrantyparts'
  AND COLUMN_NAME = 'ERP_OrderNo'
  AND TABLE_NAME LIKE 'BoatOptions%'
ORDER BY TABLE_NAME;

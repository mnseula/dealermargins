-- ============================================================================
-- Create BoatOptions26_test Table
-- ============================================================================
-- Purpose: New table for complete boat builds with proper product code filtering
-- Created: 2026-01-29
-- Database: warrantyparts_test
-- ============================================================================

USE warrantyparts_test;

-- Create the new table (same structure as BoatOptions25_test)
CREATE TABLE IF NOT EXISTS `BoatOptions26_test` (
  `id` int NOT NULL AUTO_INCREMENT,
  `BoatSerialNo` varchar(15) NOT NULL DEFAULT '',
  `BoatModelNo` varchar(14) DEFAULT NULL,
  `Series` varchar(5) DEFAULT NULL,
  `ERP_OrderNo` varchar(30) DEFAULT NULL,
  `Orig_Ord_Type` varchar(1) DEFAULT NULL,
  `InvoiceNo` varchar(30) NOT NULL DEFAULT '0',
  `ApplyToNo` int DEFAULT NULL,
  `WebOrderNo` varchar(30) DEFAULT NULL,
  `InvoiceDate` int DEFAULT NULL,
  `LineNo` int NOT NULL DEFAULT '0',
  `LineSeqNo` int NOT NULL DEFAULT '0',
  `MCTDesc` varchar(30) DEFAULT NULL,
  `ItemNo` varchar(15) DEFAULT NULL,
  `ItemDesc1` varchar(30) DEFAULT NULL,
  `OptionSerialNo` varchar(12) DEFAULT NULL,
  `ItemMasterMCT` varchar(10) DEFAULT NULL,
  `ItemMasterProdCat` varchar(3) DEFAULT NULL,
  `ItemMasterProdCatDesc` varchar(30) DEFAULT NULL,
  `QuantitySold` int DEFAULT NULL,
  `ExtSalesAmount` decimal(10,2) DEFAULT NULL,
  `created_at` timestamp DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_serial` (`BoatSerialNo`),
  KEY `idx_model` (`BoatModelNo`),
  KEY `idx_erp_order` (`ERP_OrderNo`),
  KEY `idx_invoice` (`InvoiceNo`),
  KEY `idx_prod_cat` (`ItemMasterProdCat`),
  KEY `idx_invoice_date` (`InvoiceDate`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Complete boat builds with proper product code filtering';

-- Show the table was created
SELECT 'BoatOptions26_test table created successfully' AS status;
SHOW CREATE TABLE BoatOptions26_test;

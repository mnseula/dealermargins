-- ============================================================================
-- Setup Test Database for BoatOptions Import Testing
-- ============================================================================
-- Purpose: Create staging database to test MSSQL scraping before production
-- Date: 2026-02-03
-- ============================================================================

-- Create test database
CREATE DATABASE IF NOT EXISTS warrantyparts_boatoptions_test
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE warrantyparts_boatoptions_test;

-- ============================================================================
-- BoatOptions24 Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS BoatOptions24 (
    ERP_OrderNo VARCHAR(30),
    BoatSerialNo VARCHAR(15),
    BoatModelNo VARCHAR(14),
    LineNo INT,
    ItemNo VARCHAR(30),
    ItemDesc1 VARCHAR(50),
    ExtSalesAmount DECIMAL(10,2),
    QuantitySold DECIMAL(18,8),
    Series VARCHAR(5),
    WebOrderNo VARCHAR(30),
    Orig_Ord_Type VARCHAR(1),
    ApplyToNo VARCHAR(30),
    InvoiceNo VARCHAR(30),
    InvoiceDate INT,
    ItemMasterProdCat VARCHAR(3),
    ItemMasterProdCatDesc VARCHAR(100),
    ItemMasterMCT VARCHAR(10),
    MCTDesc VARCHAR(50),
    LineSeqNo INT,
    ConfigID VARCHAR(30),
    ValueText VARCHAR(100),
    OptionSerialNo VARCHAR(12),
    C_Series VARCHAR(5),
    PRIMARY KEY (ERP_OrderNo, LineSeqNo),
    INDEX idx_serial (BoatSerialNo),
    INDEX idx_model (BoatModelNo),
    INDEX idx_invoice (InvoiceNo),
    INDEX idx_mct (ItemMasterMCT)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- BoatOptions25_test Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS BoatOptions25_test (
    ERP_OrderNo VARCHAR(30),
    BoatSerialNo VARCHAR(15),
    BoatModelNo VARCHAR(14),
    LineNo INT,
    ItemNo VARCHAR(30),
    ItemDesc1 VARCHAR(50),
    ExtSalesAmount DECIMAL(10,2),
    QuantitySold DECIMAL(18,8),
    Series VARCHAR(5),
    WebOrderNo VARCHAR(30),
    Orig_Ord_Type VARCHAR(1),
    ApplyToNo VARCHAR(30),
    InvoiceNo VARCHAR(30),
    InvoiceDate INT,
    ItemMasterProdCat VARCHAR(3),
    ItemMasterProdCatDesc VARCHAR(100),
    ItemMasterMCT VARCHAR(10),
    MCTDesc VARCHAR(50),
    LineSeqNo INT,
    ConfigID VARCHAR(30),
    ValueText VARCHAR(100),
    OptionSerialNo VARCHAR(12),
    C_Series VARCHAR(5),
    PRIMARY KEY (ERP_OrderNo, LineSeqNo),
    INDEX idx_serial (BoatSerialNo),
    INDEX idx_model (BoatModelNo),
    INDEX idx_invoice (InvoiceNo),
    INDEX idx_mct (ItemMasterMCT)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- BoatOptions26_test Table (Will receive all CPQ orders)
-- ============================================================================
CREATE TABLE IF NOT EXISTS BoatOptions26_test (
    ERP_OrderNo VARCHAR(30),
    BoatSerialNo VARCHAR(15),
    BoatModelNo VARCHAR(14),
    LineNo INT,
    ItemNo VARCHAR(30),
    ItemDesc1 VARCHAR(50),
    ExtSalesAmount DECIMAL(10,2),
    QuantitySold DECIMAL(18,8),
    Series VARCHAR(5),
    WebOrderNo VARCHAR(30),
    Orig_Ord_Type VARCHAR(1),
    ApplyToNo VARCHAR(30),
    InvoiceNo VARCHAR(30),
    InvoiceDate INT,
    ItemMasterProdCat VARCHAR(3),
    ItemMasterProdCatDesc VARCHAR(100),
    ItemMasterMCT VARCHAR(10),
    MCTDesc VARCHAR(50),
    LineSeqNo INT,
    ConfigID VARCHAR(30),
    ValueText VARCHAR(100),
    OptionSerialNo VARCHAR(12),
    C_Series VARCHAR(5),
    PRIMARY KEY (ERP_OrderNo, LineSeqNo),
    INDEX idx_serial (BoatSerialNo),
    INDEX idx_model (BoatModelNo),
    INDEX idx_invoice (InvoiceNo),
    INDEX idx_mct (ItemMasterMCT),
    INDEX idx_config (ConfigID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Check tables created
SHOW TABLES;

-- Check table structures
DESCRIBE BoatOptions24;
DESCRIBE BoatOptions25_test;
DESCRIBE BoatOptions26_test;

-- ============================================================================
-- READY FOR TESTING
-- ============================================================================
-- Next step: Run import_boatoptions_test.py to populate with data from 12/14/2025 onwards

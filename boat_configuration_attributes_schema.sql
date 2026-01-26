-- ============================================================================
-- Boat Configuration Attributes Table
-- ============================================================================
-- Purpose: Store boat configuration attributes from SQL Server cfg_attr_mst
--          Including Performance Package and other configuration options
-- Source:  SQL Server CSISTG.dbo.cfg_attr_mst table
-- ============================================================================

USE warrantyparts_test;

DROP TABLE IF EXISTS BoatConfigurationAttributes;

CREATE TABLE BoatConfigurationAttributes (
    id INT AUTO_INCREMENT PRIMARY KEY,

    -- Boat identification
    boat_serial_no VARCHAR(15) COMMENT 'HIN - Hull Identification Number',
    boat_model_no VARCHAR(14) COMMENT 'Boat model number',
    erp_order_no VARCHAR(30) COMMENT 'Sales order number',
    web_order_no VARCHAR(30) COMMENT 'Web order number',
    config_id VARCHAR(50) COMMENT 'Configuration ID from configurator',

    -- Attribute details
    attr_name VARCHAR(100) COMMENT 'Attribute name (e.g., Performance Package, Console, Fuel)',
    attr_value VARCHAR(255) COMMENT 'Attribute value (e.g., ESP+_25, SPS+)',
    cfg_value VARCHAR(255) COMMENT 'cfgaUf_BENN_Cfg_Value - Configuration value',
    comp_id VARCHAR(50) COMMENT 'Component ID',

    -- Metadata
    series VARCHAR(5) COMMENT 'Boat series',
    invoice_no VARCHAR(30) COMMENT 'Invoice number',
    invoice_date INT COMMENT 'Invoice date (YYYYMMDD format)',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Indexes for fast lookups
    INDEX idx_boat_serial (boat_serial_no),
    INDEX idx_boat_model (boat_model_no),
    INDEX idx_erp_order (erp_order_no),
    INDEX idx_config_id (config_id),
    INDEX idx_attr_name (attr_name),
    INDEX idx_attr_name_value (attr_name, attr_value),
    INDEX idx_series (series),

    -- Composite index for common query pattern
    INDEX idx_boat_attr (boat_model_no, attr_name)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Boat configuration attributes from SQL Server staging database';

-- ============================================================================
-- View: Performance Packages by Boat
-- ============================================================================

CREATE OR REPLACE VIEW BoatPerformancePackages AS
SELECT
    boat_serial_no,
    boat_model_no,
    erp_order_no,
    web_order_no,
    series,
    attr_value AS performance_package,
    cfg_value AS performance_package_cfg_value,
    invoice_no,
    invoice_date
FROM BoatConfigurationAttributes
WHERE attr_name = 'Performance Package'
  AND attr_value IS NOT NULL;

-- ============================================================================
-- View: All Configuration Options by Boat
-- ============================================================================

CREATE OR REPLACE VIEW BoatConfigurationSummary AS
SELECT
    boat_model_no,
    boat_serial_no,
    erp_order_no,
    series,
    MAX(CASE WHEN attr_name = 'Performance Package' THEN attr_value END) AS performance_package,
    MAX(CASE WHEN attr_name = 'Fuel' THEN attr_value END) AS fuel_config,
    MAX(CASE WHEN attr_name = 'Console' THEN attr_value END) AS console_type,
    MAX(CASE WHEN attr_name = 'Canvas Color' THEN attr_value END) AS canvas_color,
    MAX(CASE WHEN attr_name = 'Captain''s Chairs' THEN attr_value END) AS captains_chairs,
    MAX(CASE WHEN attr_name = 'Trim Accents' THEN attr_value END) AS trim_accents,
    MAX(CASE WHEN attr_name = 'BASE VINYL' THEN attr_value END) AS base_vinyl,
    MAX(CASE WHEN attr_name = 'FLOORING' THEN attr_value END) AS flooring
FROM BoatConfigurationAttributes
GROUP BY boat_model_no, boat_serial_no, erp_order_no, series;

-- ============================================================================
-- Sample Queries
-- ============================================================================

-- Get performance package for a specific boat model
-- SELECT * FROM BoatPerformancePackages WHERE boat_model_no = '25QXFBWA';

-- Get all configuration options for a specific sales order
-- SELECT * FROM BoatConfigurationAttributes WHERE erp_order_no = 'SO00930192' ORDER BY attr_name;

-- Get configuration summary for a boat
-- SELECT * FROM BoatConfigurationSummary WHERE boat_model_no = '25QXFBWA';

-- Count boats by performance package
-- SELECT performance_package, COUNT(*) as boat_count
-- FROM BoatPerformancePackages
-- GROUP BY performance_package
-- ORDER BY boat_count DESC;

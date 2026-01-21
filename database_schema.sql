-- ============================================================================
-- Bennington CPQ Data - MySQL Database Schema
-- ============================================================================
-- Purpose: Store model catalog, pricing, performance specs, and standard features
-- Source Data: Infor CPQ APIs (OptionList, Performance Matrix, Standards Matrix)
-- Created: 2026-01-21
-- ============================================================================

-- Drop tables in reverse order of dependencies
DROP TABLE IF EXISTS ModelStandardFeatures;
DROP TABLE IF EXISTS ModelPerformance;
DROP TABLE IF EXISTS ModelPricing;
DROP TABLE IF EXISTS StandardFeatures;
DROP TABLE IF EXISTS PerformancePackages;
DROP TABLE IF EXISTS Models;
DROP TABLE IF EXISTS Series;

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Series Table
-- ----------------------------------------------------------------------------
-- Stores boat series information (Q, QX, R, LXS, M, S, etc.)
-- Series codes can change month-to-month, so this tracks active series

CREATE TABLE Series (
    series_id VARCHAR(10) PRIMARY KEY,
    series_name VARCHAR(100),
    parent_series VARCHAR(10),
    description TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_active (active),
    INDEX idx_parent (parent_series)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- Models Table
-- ----------------------------------------------------------------------------
-- Central table for all boat models
-- One row per unique model (e.g., 24LXSFB, 26LXSSBA)

CREATE TABLE Models (
    model_id VARCHAR(20) PRIMARY KEY,
    series_id VARCHAR(10) NOT NULL,
    model_name VARCHAR(100),
    floorplan_code VARCHAR(20),
    floorplan_desc VARCHAR(200),
    length_feet INT,
    length_str VARCHAR(20),
    beam_length DECIMAL(5,2),
    beam_str VARCHAR(20),
    loa DECIMAL(6,2) COMMENT 'Length Overall',
    loa_str VARCHAR(20),
    seats INT,
    visible BOOLEAN DEFAULT TRUE COMMENT 'Active/visible in catalog',
    image_link VARCHAR(500),

    -- Additional metadata
    engine_configuration VARCHAR(100),
    has_arch BOOLEAN DEFAULT FALSE,
    has_windshield BOOLEAN DEFAULT FALSE,
    twin_engine BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (series_id) REFERENCES Series(series_id) ON DELETE CASCADE,
    INDEX idx_series (series_id),
    INDEX idx_visible (visible),
    INDEX idx_length (length_feet),
    INDEX idx_floorplan (floorplan_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- ModelPricing Table
-- ----------------------------------------------------------------------------
-- Stores MSRP pricing with effective dates for historical tracking
-- Multiple rows per model to track price changes over time

CREATE TABLE ModelPricing (
    pricing_id INT AUTO_INCREMENT PRIMARY KEY,
    model_id VARCHAR(20) NOT NULL,
    msrp DECIMAL(10,2) NOT NULL,
    effective_date DATE NOT NULL,
    end_date DATE NULL COMMENT 'NULL means currently active',
    year INT NOT NULL COMMENT 'Model year (e.g., 2026)',
    discount DECIMAL(10,2) DEFAULT 0.00,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (model_id) REFERENCES Models(model_id) ON DELETE CASCADE,
    INDEX idx_model_effective (model_id, effective_date),
    INDEX idx_current (model_id, end_date),
    INDEX idx_year (year),

    UNIQUE KEY unique_model_date (model_id, effective_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- PERFORMANCE DATA TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- PerformancePackages Table
-- ----------------------------------------------------------------------------
-- Master list of performance packages (25_IN_22, SPS+_22, ESP_22, etc.)

CREATE TABLE PerformancePackages (
    perf_package_id VARCHAR(50) PRIMARY KEY,
    package_name VARCHAR(100),
    description TEXT,
    active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_active (active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- ModelPerformance Table
-- ----------------------------------------------------------------------------
-- Performance specifications for each model × performance package combination
-- One row per model-perfpack combo (some models have multiple perf packages)

CREATE TABLE ModelPerformance (
    performance_id INT AUTO_INCREMENT PRIMARY KEY,
    model_id VARCHAR(20) NOT NULL,
    perf_package_id VARCHAR(50) NOT NULL,
    year INT NOT NULL COMMENT 'Data year (e.g., 2026)',

    -- Performance specifications
    max_hp DECIMAL(6,1),
    no_of_tubes DECIMAL(3,1),
    person_capacity VARCHAR(50),
    hull_weight DECIMAL(8,1) COMMENT 'in pounds',
    pontoon_gauge DECIMAL(4,2) COMMENT 'thickness in inches',
    transom VARCHAR(20) COMMENT 'height in inches',
    tube_height VARCHAR(20),
    tube_center_to_center VARCHAR(20),
    max_width VARCHAR(20),
    fuel_capacity VARCHAR(50),

    -- Cable/hose lengths (in feet)
    mech_str_cable_no_ead INT COMMENT 'Mechanical steering cable without EAD',
    mech_str_cable_ead INT COMMENT 'Mechanical steering cable with EAD',
    hyd_str_hose INT COMMENT 'Hydraulic steering hose',
    ctrl_cable_no_ead INT COMMENT 'Control cable without EAD',
    ctrl_cable_ead INT COMMENT 'Control cable with EAD',
    brp_harness_len INT,
    honda_harness_len INT,
    merc_harness_len INT,
    yamaha_harness_len INT,
    suzuki_harness_len INT,
    pow_assist_hose INT COMMENT 'Power assist hose',

    -- Tube measurements
    tube_length_str VARCHAR(20),
    tube_length_num DECIMAL(6,2),
    deck_length_str VARCHAR(20),
    deck_length_num DECIMAL(6,2),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (model_id) REFERENCES Models(model_id) ON DELETE CASCADE,
    FOREIGN KEY (perf_package_id) REFERENCES PerformancePackages(perf_package_id) ON DELETE CASCADE,
    INDEX idx_model (model_id),
    INDEX idx_perf_package (perf_package_id),
    INDEX idx_year (year),

    UNIQUE KEY unique_model_perf_year (model_id, perf_package_id, year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- STANDARD FEATURES TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- StandardFeatures Table
-- ----------------------------------------------------------------------------
-- Master list of all standard features
-- Organized by Area (Console Features, Seating, etc.)

CREATE TABLE StandardFeatures (
    feature_id INT AUTO_INCREMENT PRIMARY KEY,
    feature_code VARCHAR(50) UNIQUE COMMENT 'Unique code for feature',
    area VARCHAR(100) NOT NULL COMMENT 'Feature category/area',
    description TEXT NOT NULL COMMENT 'Feature description',
    sort_order INT DEFAULT 0 COMMENT 'Display order',
    active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_area (area),
    INDEX idx_active (active),
    INDEX idx_sort (sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- ModelStandardFeatures Table
-- ----------------------------------------------------------------------------
-- Junction table linking models to their standard features
-- Only stores records where feature is "Standard" (value = 'S')
-- If a feature is NOT standard for a model, there's no row

CREATE TABLE ModelStandardFeatures (
    model_feature_id INT AUTO_INCREMENT PRIMARY KEY,
    model_id VARCHAR(20) NOT NULL,
    feature_id INT NOT NULL,
    year INT NOT NULL COMMENT 'Data year (e.g., 2026)',
    is_standard BOOLEAN DEFAULT TRUE COMMENT 'Always TRUE - feature is standard',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (model_id) REFERENCES Models(model_id) ON DELETE CASCADE,
    FOREIGN KEY (feature_id) REFERENCES StandardFeatures(feature_id) ON DELETE CASCADE,
    INDEX idx_model (model_id),
    INDEX idx_feature (feature_id),
    INDEX idx_year (year),

    UNIQUE KEY unique_model_feature_year (model_id, feature_id, year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- VIEWS FOR EASY QUERYING
-- ============================================================================

-- ----------------------------------------------------------------------------
-- View: CurrentModelPricing
-- ----------------------------------------------------------------------------
-- Shows current active pricing for all models

CREATE OR REPLACE VIEW CurrentModelPricing AS
SELECT
    m.model_id,
    m.model_name,
    m.series_id,
    s.series_name,
    m.floorplan_desc,
    m.length_feet,
    m.seats,
    p.msrp,
    p.year,
    p.effective_date
FROM Models m
JOIN Series s ON m.series_id = s.series_id
JOIN ModelPricing p ON m.model_id = p.model_id
WHERE m.visible = TRUE
  AND p.end_date IS NULL
ORDER BY s.series_id, m.length_feet, m.model_id;

-- ----------------------------------------------------------------------------
-- View: ModelWithCurrentPrice
-- ----------------------------------------------------------------------------
-- Complete model information with current pricing

CREATE OR REPLACE VIEW ModelWithCurrentPrice AS
SELECT
    m.*,
    s.series_name,
    s.parent_series,
    p.msrp,
    p.year AS price_year,
    p.effective_date AS price_effective_date
FROM Models m
JOIN Series s ON m.series_id = s.series_id
LEFT JOIN ModelPricing p ON m.model_id = p.model_id AND p.end_date IS NULL
ORDER BY m.series_id, m.length_feet, m.model_id;

-- ----------------------------------------------------------------------------
-- View: ModelStandardFeaturesList
-- ----------------------------------------------------------------------------
-- Easy view of which standard features each model has

CREATE OR REPLACE VIEW ModelStandardFeaturesList AS
SELECT
    m.model_id,
    m.model_name,
    m.series_id,
    sf.area,
    sf.description AS feature_description,
    sf.sort_order,
    msf.year
FROM Models m
JOIN ModelStandardFeatures msf ON m.model_id = msf.model_id
JOIN StandardFeatures sf ON msf.feature_id = sf.feature_id
WHERE m.visible = TRUE
  AND sf.active = TRUE
ORDER BY m.model_id, sf.area, sf.sort_order;

-- ----------------------------------------------------------------------------
-- View: ModelPerformanceDetails
-- ----------------------------------------------------------------------------
-- Complete performance details for all models

CREATE OR REPLACE VIEW ModelPerformanceDetails AS
SELECT
    m.model_id,
    m.model_name,
    m.series_id,
    s.series_name,
    mp.perf_package_id,
    pp.package_name,
    mp.max_hp,
    mp.no_of_tubes,
    mp.person_capacity,
    mp.hull_weight,
    mp.pontoon_gauge,
    mp.fuel_capacity,
    mp.year
FROM Models m
JOIN Series s ON m.series_id = s.series_id
JOIN ModelPerformance mp ON m.model_id = mp.model_id
JOIN PerformancePackages pp ON mp.perf_package_id = pp.perf_package_id
WHERE m.visible = TRUE
ORDER BY m.series_id, m.model_id, mp.perf_package_id;

-- ============================================================================
-- EXAMPLE QUERIES
-- ============================================================================

/*

-- 1. Get all LXS models with current pricing
SELECT * FROM ModelWithCurrentPrice
WHERE series_id = 'LXS'
ORDER BY length_feet, model_id;

-- 2. Get all standard features for model 24LXSFB
SELECT area, feature_description
FROM ModelStandardFeaturesList
WHERE model_id = '24LXSFB'
ORDER BY area, sort_order;

-- 3. Get performance specs for model 24LXSFB
SELECT * FROM ModelPerformanceDetails
WHERE model_id = '24LXSFB';

-- 4. Find all models with a specific feature
SELECT model_id, model_name, series_id
FROM ModelStandardFeaturesList
WHERE feature_description LIKE '%Console Courtesy Light%'
GROUP BY model_id, model_name, series_id;

-- 5. Get models by price range
SELECT model_id, model_name, series_id, msrp
FROM ModelWithCurrentPrice
WHERE msrp BETWEEN 45000 AND 55000
ORDER BY msrp;

-- 6. Count standard features per model
SELECT
    model_id,
    COUNT(*) as feature_count
FROM ModelStandardFeatures
WHERE year = 2026
GROUP BY model_id
ORDER BY feature_count DESC;

-- 7. Get all models in a series with their performance packages
SELECT
    m.model_id,
    m.model_name,
    GROUP_CONCAT(DISTINCT mp.perf_package_id ORDER BY mp.perf_package_id) as perf_packages,
    p.msrp
FROM Models m
JOIN ModelPerformance mp ON m.model_id = mp.model_id
JOIN ModelPricing p ON m.model_id = p.model_id AND p.end_date IS NULL
WHERE m.series_id = 'LXS'
GROUP BY m.model_id, m.model_name, p.msrp
ORDER BY m.length_feet, m.model_id;

-- 8. Price history for a specific model
SELECT
    model_id,
    msrp,
    effective_date,
    end_date,
    DATEDIFF(COALESCE(end_date, CURDATE()), effective_date) as days_active
FROM ModelPricing
WHERE model_id = '24LXSFB'
ORDER BY effective_date DESC;

*/

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Additional composite indexes for common queries
CREATE INDEX idx_models_series_visible ON Models(series_id, visible);
CREATE INDEX idx_models_length_series ON Models(length_feet, series_id);
CREATE INDEX idx_pricing_year_current ON ModelPricing(year, end_date);
CREATE INDEX idx_performance_year ON ModelPerformance(year, model_id);
CREATE INDEX idx_standards_year ON ModelStandardFeatures(year, model_id);

-- ============================================================================
-- STORED PROCEDURES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Procedure: GetModelFullDetails
-- ----------------------------------------------------------------------------
-- Get complete information for a model including price, performance, and features

DELIMITER //

CREATE PROCEDURE GetModelFullDetails(
    IN p_model_id VARCHAR(20),
    IN p_year INT
)
BEGIN
    -- Model basic info with current price
    SELECT
        m.*,
        s.series_name,
        s.parent_series,
        p.msrp,
        p.effective_date
    FROM Models m
    JOIN Series s ON m.series_id = s.series_id
    LEFT JOIN ModelPricing p ON m.model_id = p.model_id AND p.end_date IS NULL
    WHERE m.model_id = p_model_id;

    -- Performance data
    SELECT
        mp.*,
        pp.package_name
    FROM ModelPerformance mp
    JOIN PerformancePackages pp ON mp.perf_package_id = pp.perf_package_id
    WHERE mp.model_id = p_model_id AND mp.year = p_year;

    -- Standard features
    SELECT
        sf.area,
        sf.description,
        sf.sort_order
    FROM ModelStandardFeatures msf
    JOIN StandardFeatures sf ON msf.feature_id = sf.feature_id
    WHERE msf.model_id = p_model_id AND msf.year = p_year
    ORDER BY sf.area, sf.sort_order;
END //

DELIMITER ;

-- ----------------------------------------------------------------------------
-- Procedure: UpdateModelPrice
-- ----------------------------------------------------------------------------
-- Update model price and manage effective dates

DELIMITER //

CREATE PROCEDURE UpdateModelPrice(
    IN p_model_id VARCHAR(20),
    IN p_new_msrp DECIMAL(10,2),
    IN p_effective_date DATE,
    IN p_year INT
)
BEGIN
    -- End the current active price
    UPDATE ModelPricing
    SET end_date = DATE_SUB(p_effective_date, INTERVAL 1 DAY)
    WHERE model_id = p_model_id
      AND end_date IS NULL;

    -- Insert new price
    INSERT INTO ModelPricing (model_id, msrp, effective_date, year)
    VALUES (p_model_id, p_new_msrp, p_effective_date, p_year);
END //

DELIMITER ;

-- ============================================================================
-- DATA INTEGRITY CONSTRAINTS
-- ============================================================================

-- Add check constraints (MySQL 8.0.16+)
ALTER TABLE ModelPricing
    ADD CONSTRAINT chk_msrp_positive CHECK (msrp >= 0);

ALTER TABLE ModelPerformance
    ADD CONSTRAINT chk_max_hp_positive CHECK (max_hp >= 0),
    ADD CONSTRAINT chk_hull_weight_positive CHECK (hull_weight >= 0);

ALTER TABLE Models
    ADD CONSTRAINT chk_length_positive CHECK (length_feet > 0),
    ADD CONSTRAINT chk_seats_positive CHECK (seats >= 0);

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

ALTER TABLE Series COMMENT = 'Boat series codes (Q, QX, R, LXS, M, S, etc.)';
ALTER TABLE Models COMMENT = 'Central catalog of all boat models';
ALTER TABLE ModelPricing COMMENT = 'MSRP pricing with effective date tracking';
ALTER TABLE PerformancePackages COMMENT = 'Performance package definitions';
ALTER TABLE ModelPerformance COMMENT = 'Technical specifications per model-perfpack';
ALTER TABLE StandardFeatures COMMENT = 'Master list of standard features';
ALTER TABLE ModelStandardFeatures COMMENT = 'Junction table: which models have which features';

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================

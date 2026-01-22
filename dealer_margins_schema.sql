-- ============================================================================
-- Dealer Margins - MySQL Database Schema Extension
-- ============================================================================
-- Purpose: Store dealer information and margin configurations per series
-- Source Data: Infor CPQ API (C_GD_DealerMargin entity)
-- Created: 2026-01-22
-- ============================================================================

-- Drop tables in reverse order of dependencies
DROP TABLE IF EXISTS DealerMargins;
DROP TABLE IF EXISTS Dealers;

-- ============================================================================
-- DEALER TABLES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Dealers Table
-- ----------------------------------------------------------------------------
-- Stores dealer information
-- One row per unique dealer location

CREATE TABLE Dealers (
    dealer_id VARCHAR(20) PRIMARY KEY COMMENT 'CPQ Dealer ID (e.g., 00333836)',
    dealer_name VARCHAR(200) NOT NULL COMMENT 'Dealer name/location',
    dealer_code VARCHAR(50) COMMENT 'Internal dealer code',

    -- Contact information
    address VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    country VARCHAR(50) DEFAULT 'USA',
    phone VARCHAR(50),
    email VARCHAR(100),

    -- Business information
    territory VARCHAR(100) COMMENT 'Sales territory',
    region VARCHAR(100) COMMENT 'Geographic region',
    dealer_type VARCHAR(50) COMMENT 'Type of dealership (e.g., Marine, RV)',
    active BOOLEAN DEFAULT TRUE COMMENT 'Dealer is active/enabled',

    -- Account status
    account_status VARCHAR(50) DEFAULT 'ACTIVE' COMMENT 'ACTIVE, INACTIVE, SUSPENDED',
    credit_hold BOOLEAN DEFAULT FALSE,
    preferred_dealer BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_dealer_name (dealer_name),
    INDEX idx_active (active),
    INDEX idx_territory (territory),
    INDEX idx_region (region),
    INDEX idx_account_status (account_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- DealerMargins Table
-- ----------------------------------------------------------------------------
-- Stores margin percentages for each dealer × series combination
-- One row per dealer-series pair
-- Margins are stored as percentages (e.g., 27.0 = 27%)

CREATE TABLE DealerMargins (
    margin_id INT AUTO_INCREMENT PRIMARY KEY,
    dealer_id VARCHAR(20) NOT NULL,
    series_id VARCHAR(10) NOT NULL,

    -- Margin percentages (stored as decimal, e.g., 27.0 = 27%)
    base_boat_margin DECIMAL(5,2) NOT NULL DEFAULT 0.00 COMMENT 'Base boat margin %',
    engine_margin DECIMAL(5,2) NOT NULL DEFAULT 0.00 COMMENT 'Engine margin %',
    options_margin DECIMAL(5,2) NOT NULL DEFAULT 0.00 COMMENT 'Options margin %',
    freight_margin DECIMAL(5,2) NOT NULL DEFAULT 0.00 COMMENT 'Freight margin %',
    prep_margin DECIMAL(5,2) NOT NULL DEFAULT 0.00 COMMENT 'Prep margin %',
    volume_discount DECIMAL(5,2) NOT NULL DEFAULT 0.00 COMMENT 'Volume discount %',

    -- Configuration status
    enabled BOOLEAN DEFAULT FALSE COMMENT 'Margin config is active',

    -- Effective dates for historical tracking
    effective_date DATE NOT NULL COMMENT 'When these margins become effective',
    end_date DATE NULL COMMENT 'NULL means currently active',

    -- Additional metadata
    year INT NOT NULL COMMENT 'Model year these margins apply to',
    notes TEXT COMMENT 'Notes about this margin configuration',

    -- Audit fields
    created_by VARCHAR(100) COMMENT 'User who created this config',
    updated_by VARCHAR(100) COMMENT 'User who last updated this config',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (dealer_id) REFERENCES Dealers(dealer_id) ON DELETE CASCADE,
    FOREIGN KEY (series_id) REFERENCES Series(series_id) ON DELETE CASCADE,

    INDEX idx_dealer (dealer_id),
    INDEX idx_series (series_id),
    INDEX idx_enabled (enabled),
    INDEX idx_current (dealer_id, series_id, end_date),
    INDEX idx_year (year),
    INDEX idx_dealer_series (dealer_id, series_id),

    UNIQUE KEY unique_dealer_series_date (dealer_id, series_id, effective_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- VIEWS FOR EASY QUERYING
-- ============================================================================

-- ----------------------------------------------------------------------------
-- View: CurrentDealerMargins
-- ----------------------------------------------------------------------------
-- Shows current active margins for all dealer-series combinations

CREATE OR REPLACE VIEW CurrentDealerMargins AS
SELECT
    d.dealer_id,
    d.dealer_name,
    d.city,
    d.state,
    d.territory,
    d.active AS dealer_active,
    dm.series_id,
    s.series_name,
    dm.base_boat_margin,
    dm.engine_margin,
    dm.options_margin,
    dm.freight_margin,
    dm.prep_margin,
    dm.volume_discount,
    dm.enabled AS margins_enabled,
    dm.effective_date,
    dm.year
FROM Dealers d
JOIN DealerMargins dm ON d.dealer_id = dm.dealer_id
JOIN Series s ON dm.series_id = s.series_id
WHERE dm.end_date IS NULL
ORDER BY d.dealer_name, dm.series_id;

-- ----------------------------------------------------------------------------
-- View: DealerMarginsSummary
-- ----------------------------------------------------------------------------
-- Summary of dealer margins with calculated dealer cost examples

CREATE OR REPLACE VIEW DealerMarginsSummary AS
SELECT
    d.dealer_id,
    d.dealer_name,
    dm.series_id,
    s.series_name,
    dm.base_boat_margin,
    dm.engine_margin,
    dm.options_margin,
    dm.enabled,
    dm.year,
    -- Calculate average margin across all categories
    ROUND((dm.base_boat_margin + dm.engine_margin + dm.options_margin +
           dm.freight_margin + dm.prep_margin) / 5, 2) AS avg_margin,
    -- Example: What would dealer cost be for $100k MSRP
    ROUND(100000 * (1 - dm.base_boat_margin / 100), 2) AS dealer_cost_at_100k,
    ROUND(100000 * (dm.base_boat_margin / 100), 2) AS dealer_savings_at_100k
FROM Dealers d
JOIN DealerMargins dm ON d.dealer_id = dm.dealer_id
JOIN Series s ON dm.series_id = s.series_id
WHERE dm.end_date IS NULL
  AND d.active = TRUE
ORDER BY d.dealer_name, dm.series_id;

-- ----------------------------------------------------------------------------
-- View: ActiveDealersWithMargins
-- ----------------------------------------------------------------------------
-- Lists all active dealers and which series they have margins configured for

CREATE OR REPLACE VIEW ActiveDealersWithMargins AS
SELECT
    d.dealer_id,
    d.dealer_name,
    d.city,
    d.state,
    d.territory,
    GROUP_CONCAT(DISTINCT dm.series_id ORDER BY dm.series_id) AS configured_series,
    COUNT(DISTINCT dm.series_id) AS series_count,
    AVG(dm.base_boat_margin) AS avg_base_margin,
    MAX(dm.updated_at) AS last_updated
FROM Dealers d
LEFT JOIN DealerMargins dm ON d.dealer_id = dm.dealer_id AND dm.end_date IS NULL
WHERE d.active = TRUE
GROUP BY d.dealer_id, d.dealer_name, d.city, d.state, d.territory
ORDER BY d.dealer_name;

-- ============================================================================
-- STORED PROCEDURES
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Procedure: GetDealerMarginDetails
-- ----------------------------------------------------------------------------
-- Get complete margin information for a dealer and series

DELIMITER //

CREATE PROCEDURE GetDealerMarginDetails(
    IN p_dealer_name VARCHAR(200),
    IN p_series_id VARCHAR(10)
)
BEGIN
    SELECT
        d.dealer_id,
        d.dealer_name,
        d.city,
        d.state,
        d.territory,
        d.active AS dealer_active,
        dm.series_id,
        s.series_name,
        dm.base_boat_margin,
        dm.engine_margin,
        dm.options_margin,
        dm.freight_margin,
        dm.prep_margin,
        dm.volume_discount,
        dm.enabled AS margins_enabled,
        dm.effective_date,
        dm.year,
        dm.notes
    FROM Dealers d
    JOIN DealerMargins dm ON d.dealer_id = dm.dealer_id
    JOIN Series s ON dm.series_id = s.series_id
    WHERE d.dealer_name = p_dealer_name
      AND dm.series_id = p_series_id
      AND dm.end_date IS NULL;
END //

DELIMITER ;

-- ----------------------------------------------------------------------------
-- Procedure: CalculateDealerCost
-- ----------------------------------------------------------------------------
-- Calculate dealer cost based on MSRP and dealer margins

DELIMITER //

CREATE PROCEDURE CalculateDealerCost(
    IN p_dealer_id VARCHAR(20),
    IN p_series_id VARCHAR(10),
    IN p_base_msrp DECIMAL(10,2),
    IN p_engine_msrp DECIMAL(10,2),
    IN p_options_msrp DECIMAL(10,2),
    IN p_freight DECIMAL(10,2),
    IN p_prep DECIMAL(10,2)
)
BEGIN
    DECLARE v_base_margin DECIMAL(5,2);
    DECLARE v_engine_margin DECIMAL(5,2);
    DECLARE v_options_margin DECIMAL(5,2);
    DECLARE v_freight_margin DECIMAL(5,2);
    DECLARE v_prep_margin DECIMAL(5,2);
    DECLARE v_volume_discount DECIMAL(5,2);

    -- Get margins
    SELECT base_boat_margin, engine_margin, options_margin,
           freight_margin, prep_margin, volume_discount
    INTO v_base_margin, v_engine_margin, v_options_margin,
         v_freight_margin, v_prep_margin, v_volume_discount
    FROM DealerMargins
    WHERE dealer_id = p_dealer_id
      AND series_id = p_series_id
      AND end_date IS NULL
    LIMIT 1;

    -- Calculate dealer costs
    SELECT
        p_base_msrp AS base_msrp,
        p_engine_msrp AS engine_msrp,
        p_options_msrp AS options_msrp,
        p_freight AS freight_msrp,
        p_prep AS prep_msrp,
        v_base_margin AS base_margin_pct,
        v_engine_margin AS engine_margin_pct,
        v_options_margin AS options_margin_pct,
        v_freight_margin AS freight_margin_pct,
        v_prep_margin AS prep_margin_pct,
        v_volume_discount AS volume_discount_pct,
        ROUND(p_base_msrp * (1 - v_base_margin / 100), 2) AS base_dealer_cost,
        ROUND(p_engine_msrp * (1 - v_engine_margin / 100), 2) AS engine_dealer_cost,
        ROUND(p_options_msrp * (1 - v_options_margin / 100), 2) AS options_dealer_cost,
        ROUND(p_freight * (1 - v_freight_margin / 100), 2) AS freight_dealer_cost,
        ROUND(p_prep * (1 - v_prep_margin / 100), 2) AS prep_dealer_cost,
        ROUND(
            (p_base_msrp * (1 - v_base_margin / 100)) +
            (p_engine_msrp * (1 - v_engine_margin / 100)) +
            (p_options_msrp * (1 - v_options_margin / 100)) +
            (p_freight * (1 - v_freight_margin / 100)) +
            (p_prep * (1 - v_prep_margin / 100)),
            2
        ) AS total_dealer_cost,
        ROUND(
            p_base_msrp + p_engine_msrp + p_options_msrp + p_freight + p_prep,
            2
        ) AS total_msrp,
        ROUND(
            (p_base_msrp + p_engine_msrp + p_options_msrp + p_freight + p_prep) -
            (
                (p_base_msrp * (1 - v_base_margin / 100)) +
                (p_engine_msrp * (1 - v_engine_margin / 100)) +
                (p_options_msrp * (1 - v_options_margin / 100)) +
                (p_freight * (1 - v_freight_margin / 100)) +
                (p_prep * (1 - v_prep_margin / 100))
            ),
            2
        ) AS total_savings;
END //

DELIMITER ;

-- ----------------------------------------------------------------------------
-- Procedure: UpdateDealerMargins
-- ----------------------------------------------------------------------------
-- Update dealer margins and manage effective dates

DELIMITER //

CREATE PROCEDURE UpdateDealerMargins(
    IN p_dealer_id VARCHAR(20),
    IN p_series_id VARCHAR(10),
    IN p_base_margin DECIMAL(5,2),
    IN p_engine_margin DECIMAL(5,2),
    IN p_options_margin DECIMAL(5,2),
    IN p_freight_margin DECIMAL(5,2),
    IN p_prep_margin DECIMAL(5,2),
    IN p_volume_discount DECIMAL(5,2),
    IN p_enabled BOOLEAN,
    IN p_effective_date DATE,
    IN p_year INT,
    IN p_updated_by VARCHAR(100)
)
BEGIN
    -- End the current active margins
    UPDATE DealerMargins
    SET end_date = DATE_SUB(p_effective_date, INTERVAL 1 DAY)
    WHERE dealer_id = p_dealer_id
      AND series_id = p_series_id
      AND end_date IS NULL;

    -- Insert new margins
    INSERT INTO DealerMargins (
        dealer_id, series_id,
        base_boat_margin, engine_margin, options_margin,
        freight_margin, prep_margin, volume_discount,
        enabled, effective_date, year, updated_by
    )
    VALUES (
        p_dealer_id, p_series_id,
        p_base_margin, p_engine_margin, p_options_margin,
        p_freight_margin, p_prep_margin, p_volume_discount,
        p_enabled, p_effective_date, p_year, p_updated_by
    );
END //

DELIMITER ;

-- ============================================================================
-- DATA INTEGRITY CONSTRAINTS
-- ============================================================================

-- Add check constraints
ALTER TABLE DealerMargins
    ADD CONSTRAINT chk_base_margin_range CHECK (base_boat_margin BETWEEN 0 AND 100),
    ADD CONSTRAINT chk_engine_margin_range CHECK (engine_margin BETWEEN 0 AND 100),
    ADD CONSTRAINT chk_options_margin_range CHECK (options_margin BETWEEN 0 AND 100),
    ADD CONSTRAINT chk_freight_margin_range CHECK (freight_margin BETWEEN 0 AND 100),
    ADD CONSTRAINT chk_prep_margin_range CHECK (prep_margin BETWEEN 0 AND 100),
    ADD CONSTRAINT chk_volume_discount_range CHECK (volume_discount BETWEEN 0 AND 100);

-- ============================================================================
-- EXAMPLE QUERIES
-- ============================================================================

/*

-- 1. Get all current margins for a dealer
SELECT * FROM CurrentDealerMargins
WHERE dealer_name = 'NICHOLS MARINE - NORMAN'
ORDER BY series_id;

-- 2. Get margin summary for all dealers
SELECT * FROM DealerMarginsSummary
ORDER BY dealer_name, series_id;

-- 3. Find dealers with highest base boat margins for QX series
SELECT dealer_name, base_boat_margin, dealer_cost_at_100k
FROM DealerMarginsSummary
WHERE series_id = 'QX'
ORDER BY base_boat_margin DESC;

-- 4. Calculate dealer cost for a specific quote
CALL CalculateDealerCost(
    '00333836',  -- dealer_id
    'QX',        -- series_id
    103726.00,   -- base_msrp
    0.00,        -- engine_msrp
    0.00,        -- options_msrp
    0.00,        -- freight
    0.00         -- prep
);

-- 5. Get dealer margin details
CALL GetDealerMarginDetails('NICHOLS MARINE - NORMAN', 'QX');

-- 6. List all active dealers and their configured series
SELECT * FROM ActiveDealersWithMargins
ORDER BY dealer_name;

-- 7. Find dealers without margin configurations
SELECT d.dealer_id, d.dealer_name, d.city, d.state
FROM Dealers d
LEFT JOIN DealerMargins dm ON d.dealer_id = dm.dealer_id AND dm.end_date IS NULL
WHERE d.active = TRUE
  AND dm.margin_id IS NULL
ORDER BY d.dealer_name;

-- 8. Margin history for a dealer-series combination
SELECT
    dealer_id,
    series_id,
    base_boat_margin,
    engine_margin,
    enabled,
    effective_date,
    end_date,
    DATEDIFF(COALESCE(end_date, CURDATE()), effective_date) AS days_active
FROM DealerMargins
WHERE dealer_id = '00333836'
  AND series_id = 'QX'
ORDER BY effective_date DESC;

-- 9. Compare margins across dealers for same series
SELECT
    dealer_name,
    base_boat_margin,
    engine_margin,
    options_margin,
    avg_margin,
    dealer_cost_at_100k
FROM DealerMarginsSummary
WHERE series_id = 'QX'
ORDER BY base_boat_margin DESC;

*/

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

ALTER TABLE Dealers COMMENT = 'Dealer locations and contact information';
ALTER TABLE DealerMargins COMMENT = 'Margin configurations per dealer-series combination';

-- ============================================================================
-- END OF DEALER MARGINS SCHEMA
-- ============================================================================

-- ============================================================================
-- CPQ Database Schema
-- ============================================================================
-- Creates new cpq database with empty tables for CPQ boat data
--
-- Tables will be populated by:
--   - load_cpq_data.py (Models, Performance, Features, etc.)
--   - import_boatoptions_production.py (BoatOptions)
--
-- Author: Claude Code
-- Date: 2026-02-11
-- ============================================================================

-- Create database
CREATE DATABASE IF NOT EXISTS cpq CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE cpq;

-- ============================================================================
-- Tables without foreign key dependencies (created first)
-- ============================================================================

-- BoatOptions - CPQ boat transaction data
-- Renamed from BoatOptions26 (no year suffix - holds all CPQ boats)
-- Populated by: import_boatoptions_production.py
CREATE TABLE IF NOT EXISTS `BoatOptions` (
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
  `MSRP` decimal(10,2) DEFAULT NULL,
  `CfgName` varchar(100) DEFAULT NULL,
  `CfgPage` varchar(50) DEFAULT NULL,
  `CfgScreen` varchar(50) DEFAULT NULL,
  `CfgValue` varchar(100) DEFAULT NULL,
  `CfgAttrType` varchar(20) DEFAULT NULL,
  `order_date` date DEFAULT NULL,
  `external_confirmation_ref` varchar(50) DEFAULT NULL,
  `ConfigID` varchar(30) DEFAULT NULL,
  `ValueText` varchar(100) DEFAULT NULL,
  `C_Series` varchar(5) DEFAULT NULL,
  PRIMARY KEY (`BoatSerialNo`,`InvoiceNo`,`LineNo`,`LineSeqNo`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- Series - Boat series codes
CREATE TABLE IF NOT EXISTS `Series` (
  `series_id` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `series_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `parent_series` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `active` tinyint(1) DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`series_id`),
  KEY `idx_active` (`active`),
  KEY `idx_parent` (`parent_series`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Boat series codes (Q, QX, R, LXS, M, S, etc.)';

-- PerformancePackages - Performance package definitions
CREATE TABLE IF NOT EXISTS `PerformancePackages` (
  `perf_package_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `package_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `active` tinyint(1) DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`perf_package_id`),
  KEY `idx_active` (`active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Performance package definitions';

-- StandardFeatures - Master list of standard features
CREATE TABLE IF NOT EXISTS `StandardFeatures` (
  `feature_id` int NOT NULL AUTO_INCREMENT,
  `feature_code` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Unique code for feature',
  `area` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Feature category/area',
  `description` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Feature description',
  `sort_order` int DEFAULT '0' COMMENT 'Display order',
  `active` tinyint(1) DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`feature_id`),
  UNIQUE KEY `feature_code` (`feature_code`),
  KEY `idx_area` (`area`),
  KEY `idx_active` (`active`),
  KEY `idx_sort` (`sort_order`)
) ENGINE=InnoDB AUTO_INCREMENT=9742 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Master list of standard features';

-- Dealers - Dealer locations and contact information
CREATE TABLE IF NOT EXISTS `Dealers` (
  `dealer_id` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'CPQ Dealer ID (e.g., 00333836)',
  `dealer_name` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Dealer name/location',
  `dealer_code` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Internal dealer code',
  `address` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `city` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `state` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `zip_code` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `country` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT 'USA',
  `phone` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `email` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `territory` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Sales territory',
  `region` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Geographic region',
  `dealer_type` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Type of dealership (e.g., Marine, RV)',
  `active` tinyint(1) DEFAULT '1' COMMENT 'Dealer is active/enabled',
  `account_status` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT 'ACTIVE' COMMENT 'ACTIVE, INACTIVE, SUSPENDED',
  `credit_hold` tinyint(1) DEFAULT '0',
  `preferred_dealer` tinyint(1) DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`dealer_id`),
  KEY `idx_dealer_name` (`dealer_name`),
  KEY `idx_active` (`active`),
  KEY `idx_territory` (`territory`),
  KEY `idx_region` (`region`),
  KEY `idx_account_status` (`account_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Dealer locations and contact information';

-- ============================================================================
-- Tables with foreign key dependencies (created after their dependencies)
-- ============================================================================

-- Models - Central catalog of all boat models (depends on Series)
CREATE TABLE IF NOT EXISTS `Models` (
  `model_id` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `series_id` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `model_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `floorplan_code` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `floorplan_desc` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `length_feet` int DEFAULT NULL,
  `length_str` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `beam_length` decimal(5,2) DEFAULT NULL,
  `beam_str` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `loa` decimal(6,2) DEFAULT NULL COMMENT 'Length Overall',
  `loa_str` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `seats` int DEFAULT NULL,
  `visible` tinyint(1) DEFAULT '1' COMMENT 'Active/visible in catalog',
  `image_link` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `engine_configuration` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `has_arch` tinyint(1) DEFAULT '0',
  `has_windshield` tinyint(1) DEFAULT '0',
  `twin_engine` tinyint(1) DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`model_id`),
  KEY `idx_series` (`series_id`),
  KEY `idx_visible` (`visible`),
  KEY `idx_length` (`length_feet`),
  KEY `idx_floorplan` (`floorplan_code`),
  KEY `idx_models_series_visible` (`series_id`,`visible`),
  KEY `idx_models_length_series` (`length_feet`,`series_id`),
  CONSTRAINT `Models_ibfk_1` FOREIGN KEY (`series_id`) REFERENCES `Series` (`series_id`) ON DELETE CASCADE,
  CONSTRAINT `chk_length_positive` CHECK ((`length_feet` > 0)),
  CONSTRAINT `chk_seats_positive` CHECK ((`seats` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Central catalog of all boat models';

-- ModelPricing - MSRP pricing with effective date tracking (depends on Models)
CREATE TABLE IF NOT EXISTS `ModelPricing` (
  `pricing_id` int NOT NULL AUTO_INCREMENT,
  `model_id` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `msrp` decimal(10,2) NOT NULL,
  `effective_date` date NOT NULL COMMENT 'When this pricing becomes effective',
  `end_date` date DEFAULT NULL COMMENT 'NULL means currently active',
  `year` int NOT NULL COMMENT 'Model year (e.g., 2026)',
  `discount` decimal(10,2) DEFAULT '0.00',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`pricing_id`),
  UNIQUE KEY `unique_model_date` (`model_id`,`effective_date`),
  KEY `idx_model_effective` (`model_id`,`effective_date`),
  KEY `idx_current` (`model_id`,`end_date`),
  KEY `idx_year` (`year`),
  CONSTRAINT `ModelPricing_ibfk_1` FOREIGN KEY (`model_id`) REFERENCES `Models` (`model_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='MSRP pricing with effective date tracking';

-- ModelPerformance - Technical specifications (depends on Models and PerformancePackages)
CREATE TABLE IF NOT EXISTS `ModelPerformance` (
  `performance_id` int NOT NULL AUTO_INCREMENT,
  `model_id` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `perf_package_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `year` int NOT NULL COMMENT 'Data year (e.g., 2026)',
  `max_hp` decimal(6,1) DEFAULT NULL,
  `no_of_tubes` decimal(3,1) DEFAULT NULL,
  `person_capacity` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `hull_weight` decimal(8,1) DEFAULT NULL COMMENT 'in pounds',
  `pontoon_gauge` decimal(4,2) DEFAULT NULL COMMENT 'thickness in inches',
  `transom` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'height in inches',
  `tube_height` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `tube_center_to_center` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `max_width` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `fuel_capacity` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `mech_str_cable_no_ead` int DEFAULT NULL COMMENT 'Mechanical steering cable without EAD',
  `mech_str_cable_ead` int DEFAULT NULL COMMENT 'Mechanical steering cable with EAD',
  `hyd_str_hose` int DEFAULT NULL COMMENT 'Hydraulic steering hose',
  `ctrl_cable_no_ead` int DEFAULT NULL COMMENT 'Control cable without EAD',
  `ctrl_cable_ead` int DEFAULT NULL COMMENT 'Control cable with EAD',
  `brp_harness_len` int DEFAULT NULL,
  `honda_harness_len` int DEFAULT NULL,
  `merc_harness_len` int DEFAULT NULL,
  `yamaha_harness_len` int DEFAULT NULL,
  `suzuki_harness_len` int DEFAULT NULL,
  `pow_assist_hose` int DEFAULT NULL COMMENT 'Power assist hose',
  `tube_length_str` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `tube_length_num` decimal(6,2) DEFAULT NULL,
  `deck_length_str` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `deck_length_num` decimal(6,2) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`performance_id`),
  UNIQUE KEY `unique_model_perf_year` (`model_id`,`perf_package_id`,`year`),
  KEY `idx_model` (`model_id`),
  KEY `idx_perf_package` (`perf_package_id`),
  KEY `idx_year` (`year`),
  KEY `idx_performance_year` (`year`,`model_id`),
  CONSTRAINT `ModelPerformance_ibfk_1` FOREIGN KEY (`model_id`) REFERENCES `Models` (`model_id`) ON DELETE CASCADE,
  CONSTRAINT `ModelPerformance_ibfk_2` FOREIGN KEY (`perf_package_id`) REFERENCES `PerformancePackages` (`perf_package_id`) ON DELETE CASCADE,
  CONSTRAINT `chk_hull_weight_positive` CHECK ((`hull_weight` >= 0)),
  CONSTRAINT `chk_max_hp_positive` CHECK ((`max_hp` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=7582 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Technical specifications per model-perfpack';

-- ModelStandardFeatures - Junction table (depends on Models and StandardFeatures)
CREATE TABLE IF NOT EXISTS `ModelStandardFeatures` (
  `model_feature_id` int NOT NULL AUTO_INCREMENT,
  `model_id` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `feature_id` int NOT NULL,
  `year` int NOT NULL COMMENT 'Data year (e.g., 2026)',
  `is_standard` tinyint(1) DEFAULT '1' COMMENT 'Always TRUE - feature is standard',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`model_feature_id`),
  UNIQUE KEY `unique_model_feature_year` (`model_id`,`feature_id`,`year`),
  KEY `idx_model` (`model_id`),
  KEY `idx_feature` (`feature_id`),
  KEY `idx_year` (`year`),
  KEY `idx_standards_year` (`year`,`model_id`),
  CONSTRAINT `ModelStandardFeatures_ibfk_1` FOREIGN KEY (`model_id`) REFERENCES `Models` (`model_id`) ON DELETE CASCADE,
  CONSTRAINT `ModelStandardFeatures_ibfk_2` FOREIGN KEY (`feature_id`) REFERENCES `StandardFeatures` (`feature_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=81930 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Junction table: which models have which features';

-- DealerMargins - Margin configurations (depends on Dealers and Series)
CREATE TABLE IF NOT EXISTS `DealerMargins` (
  `margin_id` int NOT NULL AUTO_INCREMENT,
  `dealer_id` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `series_id` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `base_boat_margin` decimal(5,2) NOT NULL DEFAULT '0.00' COMMENT 'Base boat margin %',
  `engine_margin` decimal(5,2) NOT NULL DEFAULT '0.00' COMMENT 'Engine margin %',
  `options_margin` decimal(5,2) NOT NULL DEFAULT '0.00' COMMENT 'Options margin %',
  `freight_margin` decimal(5,2) NOT NULL DEFAULT '0.00' COMMENT 'Freight margin %',
  `prep_margin` decimal(5,2) NOT NULL DEFAULT '0.00' COMMENT 'Prep margin %',
  `volume_discount` decimal(5,2) NOT NULL DEFAULT '0.00' COMMENT 'Volume discount %',
  `enabled` tinyint(1) DEFAULT '0' COMMENT 'Margin config is active',
  `effective_date` date NOT NULL COMMENT 'When these margins become effective',
  `end_date` date DEFAULT NULL COMMENT 'NULL means currently active',
  `year` int NOT NULL COMMENT 'Model year these margins apply to',
  `notes` text COLLATE utf8mb4_unicode_ci COMMENT 'Notes about this margin configuration',
  `created_by` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'User who created this config',
  `updated_by` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'User who last updated this config',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`margin_id`),
  UNIQUE KEY `unique_dealer_series_date` (`dealer_id`,`series_id`,`effective_date`),
  KEY `idx_dealer` (`dealer_id`),
  KEY `idx_series` (`series_id`),
  KEY `idx_enabled` (`enabled`),
  KEY `idx_current` (`dealer_id`,`series_id`,`end_date`),
  KEY `idx_year` (`year`),
  KEY `idx_dealer_series` (`dealer_id`,`series_id`),
  CONSTRAINT `DealerMargins_ibfk_1` FOREIGN KEY (`dealer_id`) REFERENCES `Dealers` (`dealer_id`) ON DELETE CASCADE,
  CONSTRAINT `DealerMargins_ibfk_2` FOREIGN KEY (`series_id`) REFERENCES `Series` (`series_id`) ON DELETE CASCADE,
  CONSTRAINT `chk_base_margin_range` CHECK ((`base_boat_margin` between 0 and 100)),
  CONSTRAINT `chk_engine_margin_range` CHECK ((`engine_margin` between 0 and 100)),
  CONSTRAINT `chk_freight_margin_range` CHECK ((`freight_margin` between 0 and 100)),
  CONSTRAINT `chk_options_margin_range` CHECK ((`options_margin` between 0 and 100)),
  CONSTRAINT `chk_prep_margin_range` CHECK ((`prep_margin` between 0 and 100)),
  CONSTRAINT `chk_volume_discount_range` CHECK ((`volume_discount` between 0 and 100))
) ENGINE=InnoDB AUTO_INCREMENT=101 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Margin configurations per dealer-series combination';

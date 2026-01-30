-- =====================================================================
-- GetCompleteBoatInformation - Complete Window Sticker & Dealer Margin Data
-- =====================================================================
-- Purpose: Get ALL boat information for window sticker generation
--          Takes ONLY Hull# as input - queries everything else
--
-- Usage:   CALL GetCompleteBoatInformation('ETWP6278J324');
--
-- Returns 5 Result Sets:
--   1. Boat Header (model, dealer, invoice, colors, specs)
--   2. Line Items (from BoatOptions{YY} table determined by SN_MY)
--   3. MSRP Summary (totals by category)
--   4. Dealer Margins (from warrantyparts.DealerMargins)
--   5. Dealer Cost Calculations (MSRP with margins applied)
--
-- Database: warrantyparts_test (calls warrantyparts tables)
-- =====================================================================

DROP PROCEDURE IF EXISTS GetCompleteBoatInformation;

DELIMITER $$

CREATE PROCEDURE GetCompleteBoatInformation(
    IN p_hull_no VARCHAR(20)
)
proc_label: BEGIN
    -- Variables for boat header
    DECLARE v_boat_item_no VARCHAR(14) DEFAULT NULL;
    DECLARE v_dealer_number VARCHAR(10);
    DECLARE v_dealer_name VARCHAR(200);
    DECLARE v_series VARCHAR(5);
    DECLARE v_model_year INT;
    DECLARE v_invoice_no VARCHAR(30);
    DECLARE v_invoice_date_yyyymmdd VARCHAR(8);
    DECLARE v_erp_order_no VARCHAR(30);
    DECLARE v_boat_description VARCHAR(100);

    -- Variables for margin lookup
    DECLARE v_series_column_prefix VARCHAR(10);
    DECLARE v_dealer_id_normalized VARCHAR(10);

    -- Variables for dynamic SQL
    DECLARE v_table_name VARCHAR(50);

    -- =====================================================================
    -- STEP 1: Get Boat Header from SerialNumberMaster
    -- =====================================================================
    SELECT
        BoatItemNo,
        DealerNumber,
        DealerName,
        Series,
        SN_MY,
        InvoiceNo,
        InvoiceDateYYYYMMDD,
        ERP_OrderNo,
        BoatDesc1
    INTO
        v_boat_item_no,
        v_dealer_number,
        v_dealer_name,
        v_series,
        v_model_year,
        v_invoice_no,
        v_invoice_date_yyyymmdd,
        v_erp_order_no,
        v_boat_description
    FROM warrantyparts.SerialNumberMaster
    WHERE Boat_SerialNo = p_hull_no
    LIMIT 1;

    -- Check if boat exists
    IF v_boat_item_no IS NULL THEN
        SELECT 'ERROR' as status,
               CONCAT('Hull number not found: ', p_hull_no) as message;
        LEAVE proc_label;
    END IF;

    -- =====================================================================
    -- RESULT SET 1: Boat Header Information
    -- =====================================================================
    SELECT
        p_hull_no as hull_serial_no,
        snm.BoatItemNo as model_no,
        snm.BoatDesc1 as model_description,
        snm.BoatDesc2 as model_description_2,
        snm.Series as series,
        snm.SN_MY as model_year,
        snm.SerialModelYear as serial_model_year,
        snm.DealerNumber as dealer_id,
        snm.DealerName as dealer_name,
        snm.DealerCity as dealer_city,
        snm.DealerState as dealer_state,
        snm.DealerZip as dealer_zip,
        snm.DealerCountry as dealer_country,
        snm.InvoiceNo as invoice_no,
        snm.InvoiceDateYYYYMMDD as invoice_date_yyyymmdd,
        snm.ERP_OrderNo as erp_order_no,
        snm.WebOrderNo as web_order_no,
        snm.PanelColor as panel_color,
        snm.AccentPanel as accent_panel,
        snm.TrimAccent as trim_accent,
        snm.BaseVinyl as base_vinyl,
        snm.ColorPackage as color_package,
        snm.ParentRepName as rep_name,
        snm.Presold as presold,
        snm.Active as active
    FROM warrantyparts.SerialNumberMaster snm
    WHERE snm.Boat_SerialNo = p_hull_no;

    -- =====================================================================
    -- STEP 2: Get Line Items from BoatOptions{YY} table (Dynamic SQL)
    -- =====================================================================

    -- Determine table name based on model year
    SET v_table_name = CONCAT('BoatOptions', v_model_year);

    -- Create temporary table to store line items
    DROP TEMPORARY TABLE IF EXISTS tmp_line_items;
    CREATE TEMPORARY TABLE tmp_line_items (
        line_no INT,
        item_no VARCHAR(30),
        item_desc VARCHAR(255),
        product_category VARCHAR(10),
        quantity INT,
        ext_sales_amount DECIMAL(10,2)
    );

    -- Build and execute dynamic query
    SET @query = CONCAT('
        INSERT INTO tmp_line_items
        SELECT
            LineNo as line_no,
            ItemNo as item_no,
            ItemDesc1 as item_desc,
            ItemMasterProdCat as product_category,
            QuantitySold as quantity,
            ExtSalesAmount as ext_sales_amount
        FROM warrantyparts.', v_table_name, '
        WHERE BoatSerialNo = ?
        ORDER BY LineNo
    ');

    PREPARE stmt FROM @query;
    SET @hull_param = p_hull_no;
    EXECUTE stmt USING @hull_param;
    DEALLOCATE PREPARE stmt;

    -- =====================================================================
    -- RESULT SET 2: Line Items
    -- =====================================================================
    SELECT
        line_no,
        item_no,
        item_desc,
        product_category,
        quantity,
        ext_sales_amount,
        CASE product_category
            WHEN 'BS1' THEN 'Base Boat'
            WHEN 'EN7' THEN 'Engine'
            WHEN 'ACC' THEN 'Accessories'
            WHEN 'ENG' THEN 'Engine Related'
            WHEN 'MTR' THEN 'Motor'
            WHEN 'H1' THEN 'Colors/Options'
            WHEN 'L2' THEN 'Labor'
            WHEN 'C1L' THEN 'Discounts'
            WHEN 'GRO' THEN 'Fees'
            ELSE product_category
        END as category_name,
        v_table_name as source_table
    FROM tmp_line_items
    ORDER BY line_no;

    
    -- Create temp table for MSRP summary (to avoid reopening tmp_line_items)
    DROP TEMPORARY TABLE IF EXISTS tmp_msrp_summary;
    CREATE TEMPORARY TABLE tmp_msrp_summary (
        category VARCHAR(50),
        category_code VARCHAR(10),
        msrp DECIMAL(10,2)
    );

    -- Populate MSRP summary with INSERT statements (avoids "can't reopen table" error)
    INSERT INTO tmp_msrp_summary SELECT 'Base Boat', 'BS1', COALESCE(SUM(CASE WHEN product_category = 'BS1' THEN ext_sales_amount END), 0) FROM tmp_line_items;
    INSERT INTO tmp_msrp_summary SELECT 'Engine', 'EN7', COALESCE(SUM(CASE WHEN product_category IN ('EN7', 'ENG', 'MTR') THEN ext_sales_amount END), 0) FROM tmp_line_items;
    INSERT INTO tmp_msrp_summary SELECT 'Accessories', 'ACC', COALESCE(SUM(CASE WHEN product_category = 'ACC' THEN ext_sales_amount END), 0) FROM tmp_line_items;
    INSERT INTO tmp_msrp_summary SELECT 'Colors/Options', 'H1', COALESCE(SUM(CASE WHEN product_category = 'H1' THEN ext_sales_amount END), 0) FROM tmp_line_items;
    INSERT INTO tmp_msrp_summary SELECT 'Labor/Prep', 'L2', COALESCE(SUM(CASE WHEN product_category = 'L2' THEN ext_sales_amount END), 0) FROM tmp_line_items;
    INSERT INTO tmp_msrp_summary SELECT 'Discounts', 'C1L', COALESCE(SUM(CASE WHEN product_category = 'C1L' THEN ext_sales_amount END), 0) FROM tmp_line_items;
    INSERT INTO tmp_msrp_summary SELECT 'Fees', 'GRO', COALESCE(SUM(CASE WHEN product_category = 'GRO' THEN ext_sales_amount END), 0) FROM tmp_line_items;
    INSERT INTO tmp_msrp_summary SELECT 'TOTAL', 'TOTAL', COALESCE(SUM(ext_sales_amount), 0) FROM tmp_line_items;

    -- =====================================================================
    -- RESULT SET 3: MSRP Summary by Category
    -- =====================================================================
    SELECT * FROM tmp_msrp_summary;

    -- =====================================================================
    -- STEP 3: Get Dealer Margins from warrantyparts.DealerMargins
    -- =====================================================================

    -- Normalize dealer ID (remove leading zeros)
    SET v_dealer_id_normalized = CAST(v_dealer_number AS UNSIGNED);

    -- Map series name to column prefix (S → S_23, SV → SV_23, others stay same)
    SET v_series_column_prefix = CASE
        WHEN v_series = 'S' THEN 'S_23'
        WHEN v_series = 'SV' THEN 'SV_23'
        ELSE v_series
    END;

    -- Build dynamic query for dealer margins
    SET @margin_query = CONCAT('
        INSERT INTO tmp_margins
        SELECT
            DealerID as dealer_id,
            Dealership as dealer_name,
            ''', v_series, ''' as series,
            ''', v_series_column_prefix, ''' as column_prefix,
            `', v_series_column_prefix, '_BASE_BOAT` as base_boat_margin_pct,
            `', v_series_column_prefix, '_ENGINE` as engine_margin_pct,
            `', v_series_column_prefix, '_OPTIONS` as options_margin_pct,
            `', v_series_column_prefix, '_FREIGHT` as freight_value,
            `', v_series_column_prefix, '_PREP` as prep_value,
            `', v_series_column_prefix, '_VOL_DISC` as volume_discount_pct,
            ''warrantyparts.DealerMargins'' as data_source
        FROM warrantyparts.DealerMargins
        WHERE CAST(DealerID AS UNSIGNED) = ?
        LIMIT 1
    ');

    -- Execute margin query
    DROP TEMPORARY TABLE IF EXISTS tmp_margins;
    CREATE TEMPORARY TABLE tmp_margins (
        dealer_id VARCHAR(10),
        dealer_name VARCHAR(255),
        series VARCHAR(5),
        column_prefix VARCHAR(10),
        base_boat_margin_pct DECIMAL(10,2),
        engine_margin_pct DECIMAL(10,2),
        options_margin_pct DECIMAL(10,2),
        freight_value DECIMAL(10,2),
        prep_value DECIMAL(10,2),
        volume_discount_pct DECIMAL(10,2),
        data_source VARCHAR(50)
    );

    PREPARE margin_stmt FROM @margin_query;
    SET @dealer_param = v_dealer_id_normalized;
    EXECUTE margin_stmt USING @dealer_param;
    DEALLOCATE PREPARE margin_stmt;

    -- =====================================================================
    -- RESULT SET 4: Dealer Margins
    -- =====================================================================
    SELECT
        dealer_id,
        dealer_name,
        series,
        base_boat_margin_pct,
        engine_margin_pct,
        options_margin_pct,
        freight_value,
        CASE
            WHEN freight_value > 100 THEN 'FIXED_AMOUNT'
            ELSE 'PERCENTAGE'
        END as freight_type,
        prep_value,
        CASE
            WHEN prep_value > 100 THEN 'FIXED_AMOUNT'
            ELSE 'PERCENTAGE'
        END as prep_type,
        volume_discount_pct,
        data_source
    FROM tmp_margins;

    -- =====================================================================
    -- RESULT SET 5: Dealer Cost Calculations
    -- =====================================================================
    -- Note: TOTAL row costs should be calculated by summing individual categories
    SELECT
        msrp.category,
        msrp.category_code,
        msrp.msrp,
        CASE msrp.category_code
            WHEN 'BS1' THEN m.base_boat_margin_pct
            WHEN 'EN7' THEN m.engine_margin_pct
            WHEN 'ACC' THEN m.options_margin_pct
            WHEN 'H1' THEN m.options_margin_pct
            ELSE 0
        END as margin_pct,
        CASE msrp.category_code
            WHEN 'BS1' THEN ROUND(msrp.msrp * (1 - m.base_boat_margin_pct/100), 2)
            WHEN 'EN7' THEN ROUND(msrp.msrp * (1 - m.engine_margin_pct/100), 2)
            WHEN 'ACC' THEN ROUND(msrp.msrp * (1 - m.options_margin_pct/100), 2)
            WHEN 'H1' THEN ROUND(msrp.msrp * (1 - m.options_margin_pct/100), 2)
            WHEN 'L2' THEN msrp.msrp
            WHEN 'C1L' THEN msrp.msrp
            WHEN 'GRO' THEN msrp.msrp
            WHEN 'TOTAL' THEN 0  -- Calculate in application by summing other rows
            ELSE msrp.msrp
        END as dealer_cost,
        CASE msrp.category_code
            WHEN 'BS1' THEN ROUND(msrp.msrp * (m.base_boat_margin_pct/100), 2)
            WHEN 'EN7' THEN ROUND(msrp.msrp * (m.engine_margin_pct/100), 2)
            WHEN 'ACC' THEN ROUND(msrp.msrp * (m.options_margin_pct/100), 2)
            WHEN 'H1' THEN ROUND(msrp.msrp * (m.options_margin_pct/100), 2)
            WHEN 'TOTAL' THEN 0  -- Calculate in application: MSRP - dealer_cost
            ELSE 0
        END as dealer_savings
    FROM tmp_msrp_summary msrp
    CROSS JOIN tmp_margins m;

    -- Clean up
    DROP TEMPORARY TABLE IF EXISTS tmp_line_items;
    DROP TEMPORARY TABLE IF EXISTS tmp_msrp_summary;
    DROP TEMPORARY TABLE IF EXISTS tmp_margins;

END proc_label$$

DELIMITER ;

-- =====================================================================
-- Test the procedure
-- =====================================================================
-- CALL GetCompleteBoatInformation('ETWP6278J324');
-- CALL GetCompleteBoatInformation('ETWC6109F526');
-- CALL GetCompleteBoatInformation('ETWS0235L526');

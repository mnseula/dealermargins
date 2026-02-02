-- =====================================================================
-- GetCompleteBoatInformation - Complete with MSRP & Sale Price
-- =====================================================================

DROP PROCEDURE IF EXISTS GetCompleteBoatInformation;

DELIMITER $$

CREATE PROCEDURE GetCompleteBoatInformation(
    IN p_hull_no VARCHAR(20),
    IN p_msrp_margin DECIMAL(5,4),
    IN p_msrp_volume DECIMAL(5,4)
)
proc_label: BEGIN
    DECLARE v_boat_item_no VARCHAR(14) DEFAULT NULL;
    DECLARE v_dealer_number VARCHAR(10);
    DECLARE v_dealer_name VARCHAR(200);
    DECLARE v_series VARCHAR(5);
    DECLARE v_model_year INT;
    DECLARE v_invoice_no VARCHAR(30);
    DECLARE v_invoice_date_yyyymmdd VARCHAR(8);
    DECLARE v_erp_order_no VARCHAR(30);
    DECLARE v_boat_description VARCHAR(100);
    DECLARE v_series_column_prefix VARCHAR(10);
    DECLARE v_dealer_id_normalized VARCHAR(10);
    DECLARE v_table_name VARCHAR(50);
    DECLARE v_msrp_margin DECIMAL(5,4);
    DECLARE v_msrp_volume DECIMAL(5,4);
    
    -- Set defaults if NULL passed
    SET v_msrp_margin = IFNULL(p_msrp_margin, 0.7500);
    SET v_msrp_volume = IFNULL(p_msrp_volume, 1.0000);

    -- Get boat header
    SELECT
        BoatItemNo, DealerNumber, DealerName, Series, SN_MY,
        InvoiceNo, InvoiceDateYYYYMMDD, ERP_OrderNo,
        CONCAT(SN_MY + 2000, ' ', BoatItemNo, ' - ', BoatModelName)
    INTO
        v_boat_item_no, v_dealer_number, v_dealer_name, v_series, v_model_year,
        v_invoice_no, v_invoice_date_yyyymmdd, v_erp_order_no, v_boat_description
    FROM warrantyparts.SerialNumberMaster
    WHERE Boat_SerialNo = p_hull_no LIMIT 1;

    IF v_boat_item_no IS NULL THEN
        SELECT 'ERROR' as status, CONCAT('Hull not found: ', p_hull_no) as message;
        LEAVE proc_label;
    END IF;

    -- RESULT SET 1: Boat Header
    SELECT
        Boat_SerialNo as hull_serial_no, BoatItemNo as model_no,
        BoatModelName as model_name, v_boat_description as boat_description,
        SN_MY as model_year, Series as series, DealerNumber as dealer_id,
        DealerName as dealer_name, InvoiceNo as invoice_no,
        InvoiceDateYYYYMMDD as invoice_date_yyyymmdd,
        PanelColor as panel_color, AccentColor as accent_color,
        CanvasColor as canvas_color, VinylColor as vinyl_color
    FROM warrantyparts.SerialNumberMaster
    WHERE Boat_SerialNo = p_hull_no;

    -- Determine table name
    SET v_table_name = CONCAT('BoatOptions', v_model_year);

    -- Create temp table for line items
    DROP TEMPORARY TABLE IF EXISTS tmp_line_items;
    CREATE TEMPORARY TABLE tmp_line_items (
        item_no VARCHAR(30), item_description VARCHAR(255),
        product_category VARCHAR(10), mct_desc VARCHAR(50),
        quantity_sold INT, dealer_cost DECIMAL(10,2), sort_order INT
    );

    SET @query = CONCAT('
        INSERT INTO tmp_line_items
        SELECT ItemNo, ItemDesc1, ItemMasterProdCat, MCTDesc,
               COALESCE(QuantitySold, 1), COALESCE(ExtSalesAmount, 0),
               CASE WHEN MCTDesc = ''PONTOONS'' THEN 1
                    WHEN MCTDesc IN (''ENGINES'', ''ENGINES I/O'') THEN 2
                    WHEN MCTDesc = ''PRE-RIG'' THEN 3
                    WHEN ItemMasterProdCat = ''ACC'' THEN 4
                    WHEN ItemMasterMCT IN (''DIS'', ''DIV'') THEN 5
                    WHEN ItemMasterProdCat IN (''C1L'', ''C2'', ''C3P'') THEN 6
                    WHEN ItemMasterProdCat = ''GRO'' THEN 7
                    ELSE 8 END
        FROM warrantyparts.', v_table_name, '
        WHERE BoatSerialNo = ? ORDER BY 7, ItemNo');
    
    PREPARE stmt FROM @query;
    EXECUTE stmt USING p_hull_no;
    DEALLOCATE PREPARE stmt;

    -- Get dealer margins
    SET v_dealer_id_normalized = LPAD(v_dealer_number, 8, '0');
    SET v_series_column_prefix = CASE
        WHEN v_series LIKE '%23' THEN CONCAT(SUBSTRING(v_series, 1, LENGTH(v_series) - 2), '_23')
        ELSE v_series END;

    DROP TEMPORARY TABLE IF EXISTS tmp_margins;
    CREATE TEMPORARY TABLE tmp_margins (
        dealer_id VARCHAR(10), dealer_name VARCHAR(255),
        base_boat_margin_pct DECIMAL(10,2), engine_margin_pct DECIMAL(10,2),
        options_margin_pct DECIMAL(10,2), vol_disc DECIMAL(10,4)
    );

    SET @margin_query = CONCAT('
        INSERT INTO tmp_margins
        SELECT DealerID, Dealership,
               ', v_series_column_prefix, '_BASE_BOAT,
               ', v_series_column_prefix, '_ENGINE,
               ', v_series_column_prefix, '_OPTIONS,
               ', v_series_column_prefix, '_VOL_DISC / 100.0
        FROM warrantyparts.DealerMargins WHERE DealerID = ? LIMIT 1');
    
    PREPARE stmt FROM @margin_query;
    EXECUTE stmt USING v_dealer_id_normalized;
    DEALLOCATE PREPARE stmt;

    -- RESULT SET 2: LINE ITEMS with 3 prices
    SELECT
        li.item_no, li.item_description, li.product_category, li.mct_desc,
        li.quantity_sold, li.dealer_cost,
        ROUND(CASE
            WHEN li.mct_desc = 'PONTOONS' THEN (li.dealer_cost * m.vol_disc) / (m.base_boat_margin_pct / 100.0)
            WHEN li.mct_desc IN ('ENGINES', 'ENGINES I/O') THEN (li.dealer_cost * m.vol_disc) / (m.engine_margin_pct / 100.0)
            WHEN li.mct_desc = 'PRE-RIG' OR li.product_category = 'ACC' THEN (li.dealer_cost * m.vol_disc) / (m.options_margin_pct / 100.0)
            ELSE li.dealer_cost END, 2) as sale_price,
        ROUND(CASE
            WHEN li.dealer_cost > 0 THEN (li.dealer_cost * v_msrp_volume) / v_msrp_margin
            ELSE li.dealer_cost END, 2) as msrp
    FROM tmp_line_items li CROSS JOIN tmp_margins m
    ORDER BY li.sort_order, li.item_no;

    -- RESULT SET 3: PRICING SUMMARY
    DROP TEMPORARY TABLE IF EXISTS tmp_pricing_summary;
    CREATE TEMPORARY TABLE tmp_pricing_summary (
        category VARCHAR(50), category_code VARCHAR(10),
        dealer_cost DECIMAL(10,2), sale_price DECIMAL(10,2), msrp DECIMAL(10,2)
    );

    INSERT INTO tmp_pricing_summary
    SELECT 'Base Boat', 'BS1', COALESCE(SUM(li.dealer_cost), 0),
           COALESCE(SUM(ROUND((li.dealer_cost * m.vol_disc) / (m.base_boat_margin_pct / 100.0), 2)), 0),
           COALESCE(SUM(ROUND((li.dealer_cost * v_msrp_volume) / v_msrp_margin, 2)), 0)
    FROM tmp_line_items li CROSS JOIN tmp_margins m WHERE li.mct_desc = 'PONTOONS';

    INSERT INTO tmp_pricing_summary
    SELECT 'Engine', 'EN7', COALESCE(SUM(li.dealer_cost), 0),
           COALESCE(SUM(ROUND((li.dealer_cost * m.vol_disc) / (m.engine_margin_pct / 100.0), 2)), 0),
           COALESCE(SUM(ROUND((li.dealer_cost * v_msrp_volume) / v_msrp_margin, 2)), 0)
    FROM tmp_line_items li CROSS JOIN tmp_margins m WHERE li.mct_desc IN ('ENGINES', 'ENGINES I/O');

    INSERT INTO tmp_pricing_summary
    SELECT 'Pre-Rig', 'L2', COALESCE(SUM(li.dealer_cost), 0),
           COALESCE(SUM(ROUND((li.dealer_cost * m.vol_disc) / (m.options_margin_pct / 100.0), 2)), 0),
           COALESCE(SUM(ROUND((li.dealer_cost * v_msrp_volume) / v_msrp_margin, 2)), 0)
    FROM tmp_line_items li CROSS JOIN tmp_margins m WHERE li.mct_desc = 'PRE-RIG';

    INSERT INTO tmp_pricing_summary
    SELECT 'Accessories', 'ACC', COALESCE(SUM(li.dealer_cost), 0),
           COALESCE(SUM(ROUND((li.dealer_cost * m.vol_disc) / (m.options_margin_pct / 100.0), 2)), 0),
           COALESCE(SUM(ROUND((li.dealer_cost * v_msrp_volume) / v_msrp_margin, 2)), 0)
    FROM tmp_line_items li CROSS JOIN tmp_margins m WHERE li.product_category = 'ACC';

    INSERT INTO tmp_pricing_summary
    SELECT 'Discounts', 'C1L', COALESCE(SUM(li.dealer_cost), 0),
           COALESCE(SUM(li.dealer_cost), 0), COALESCE(SUM(li.dealer_cost), 0)
    FROM tmp_line_items li WHERE li.product_category IN ('C1L', 'C2', 'C3P');

    INSERT INTO tmp_pricing_summary
    SELECT 'Fees', 'GRO', COALESCE(SUM(li.dealer_cost), 0),
           COALESCE(SUM(li.dealer_cost), 0), COALESCE(SUM(li.dealer_cost), 0)
    FROM tmp_line_items li WHERE li.product_category = 'GRO';

    INSERT INTO tmp_pricing_summary
    SELECT 'TOTAL', 'TOTAL', SUM(dealer_cost), SUM(sale_price), SUM(msrp)
    FROM tmp_pricing_summary;

    SELECT * FROM tmp_pricing_summary;

    -- RESULT SET 4: DEALER MARGINS
    SELECT dealer_id, dealer_name, base_boat_margin_pct, engine_margin_pct,
           options_margin_pct, vol_disc, v_msrp_margin as msrp_margin_divisor,
           v_msrp_volume as msrp_volume_multiplier
    FROM tmp_margins;

    -- RESULT SET 5: GRAND TOTALS
    SELECT v_boat_description as boat, v_dealer_name as dealer,
           dealer_cost as total_dealer_cost, sale_price as total_sale_price,
           msrp as total_msrp, (msrp - sale_price) as customer_savings_vs_msrp,
           ROUND(((msrp - sale_price) / msrp) * 100, 2) as savings_percentage
    FROM tmp_pricing_summary WHERE category = 'TOTAL';

    DROP TEMPORARY TABLE IF EXISTS tmp_line_items;
    DROP TEMPORARY TABLE IF EXISTS tmp_margins;
    DROP TEMPORARY TABLE IF EXISTS tmp_pricing_summary;

END proc_label$$

DELIMITER ;

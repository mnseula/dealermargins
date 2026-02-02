-- Simple test procedure to debug the issue
DROP PROCEDURE IF EXISTS TestBoatLookup;

DELIMITER $$

CREATE PROCEDURE TestBoatLookup(IN p_hull_no VARCHAR(20))
BEGIN
    -- Result Set 1: Boat header
    SELECT
        Boat_SerialNo as hull_serial_no,
        BoatItemNo as model_no,
        BoatDesc1 as model_description,
        Series as series,
        SN_MY as model_year,
        DealerNumber as dealer_id,
        DealerName as dealer_name,
        InvoiceNo as invoice_no,
        InvoiceDate as invoice_date,
        ERP_OrderNo as erp_order_no
    FROM warrantyparts.SerialNumberMaster
    WHERE Boat_SerialNo = p_hull_no
    LIMIT 1;
END$$

DELIMITER ;

-- Test it
CALL TestBoatLookup('ETWP6278J324');

-- ============================================================================
-- Add ETWTEST26 Test Boat to Production Tables
-- ============================================================================
-- Purpose: Copy ETWTEST26 from test database to production for testing
-- Boat: 23ML (M-Series 2023), Order SO00936065, Invoice 25217358
-- Dealer: 50 (PONTOON BOAT, LLC) - internal test data, not visible to customers
-- ============================================================================


-- ============================================================================
-- 1/3: Copy ETWTEST26 from test to production BoatOptions26
-- ============================================================================
-- Copies all 63 records (boat, engine, accessories, config attributes)

INSERT INTO warrantyparts.BoatOptions26
SELECT *
FROM warrantyparts_boatoptions_test.BoatOptions26
WHERE BoatSerialNo = 'ETWTEST26';


-- ============================================================================
-- 2/3: Add ETWTEST26 to SerialNumberMaster
-- ============================================================================
-- Creates master boat record with details from ETWTEST26

INSERT INTO warrantyparts.SerialNumberMaster (
    Boat_SerialNo,
    BoatItemNo,
    Series,
    BoatDesc1,
    ColorPackage,
    PanelColor,
    AccentPanel,
    TrimAccent,
    BaseVinyl,
    SerialModelYear,
    ERP_OrderNo,
    InvoiceNo,
    InvoiceDate,
    DealerNumber,
    DealerName,
    DealerAddress,
    DealerCity,
    DealerState,
    DealerZip,
    DealerCountry,
    DealerPhone,
    Active,
    CPQConfigID,
    WebOrderNo
)
SELECT
    'ETWTEST26',                                  -- Serial number
    '23ML',                                       -- Model
    'M',                                          -- Series
    snm.BoatDesc1,
    snm.ColorPackage,
    'Metallic Silver',                            -- Panel color
    'No Accent',                                  -- Accent panel
    'Zebrawood Slate Trim Accents',               -- Trim accent
    'Shadow Grey Veneto',                         -- Base vinyl
    '23',                                         -- Model year
    'SO00936065',                                 -- Order number
    '25217358',                                   -- Invoice number
    '20260101',                                   -- Invoice date
    snm.DealerNumber,                             -- Dealer 50 from template
    snm.DealerName,
    snm.DealerAddress,
    snm.DealerCity,
    snm.DealerState,
    snm.DealerZip,
    snm.DealerCountry,
    snm.DealerPhone,
    0,                                            -- Active (0 = test boat)
    NULL,                                         -- CPQ Config ID
    'SOBHO00707'                                  -- Web order number
FROM warrantyparts.SerialNumberMaster snm
WHERE snm.Boat_SerialNo = 'ETWTEST024';


-- ============================================================================
-- 3/3: Add ETWTEST26 to SerialNumberRegistrationStatus
-- ============================================================================
-- Creates registration status record (unregistered test boat)

INSERT INTO warrantyparts.SerialNumberRegistrationStatus (
    SN_MY,
    Boat_SerialNo,
    Registered,
    FieldInventory,
    Unknown,
    SND,
    BenningtonOwned
)
VALUES (
    '23',           -- Model year
    'ETWTEST26',    -- Serial number
    0,              -- Not registered
    0,              -- Not in field inventory
    0,              -- Status is known
    0,              -- Not sold-not-delivered
    0               -- Not Bennington owned
);

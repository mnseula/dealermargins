-- ============================================================================
-- Hide ETWINVTEST01 from Dealer Selection (UPDATE - Don't Delete)
-- ============================================================================
-- Purpose: Set Active = 0 and Registered = 1 to hide this boat from dealer views
-- Boat: ETWINVTEST01 (Order SO00936074)
-- ============================================================================

USE warrantyparts;

-- Check current status
SELECT 
    'SerialNumberMaster' as table_name,
    Boat_SerialNo,
    BoatItemNo,
    Series,
    BoatDesc1,
    ERP_OrderNo,
    Active,
    CASE 
        WHEN Active = 1 THEN 'VISIBLE to dealers'
        WHEN Active = 0 THEN 'HIDDEN from dealers'
        ELSE 'UNKNOWN status'
    END as visibility_status
FROM SerialNumberMaster
WHERE Boat_SerialNo = 'ETWINVTEST01'
   OR ERP_OrderNo = 'SO00936074';

SELECT 
    'SerialNumberRegistrationStatus' as table_name,
    Boat_SerialNo,
    SN_MY,
    Registered,
    FieldInventory,
    CASE 
        WHEN Registered = 1 THEN 'SHOWING as registered'
        WHEN Registered = 0 THEN 'Not registered'
        ELSE 'UNKNOWN'
    END as registration_status
FROM SerialNumberRegistrationStatus
WHERE Boat_SerialNo = 'ETWINVTEST01';

-- Hide the boat by setting Active = 0 in SerialNumberMaster
UPDATE SerialNumberMaster
SET Active = 0
WHERE Boat_SerialNo = 'ETWINVTEST01'
   OR ERP_OrderNo = 'SO00936074';

-- Also update SerialNumberRegistrationStatus to mark as registered (hides from available inventory)
UPDATE SerialNumberRegistrationStatus
SET Registered = 1,
    FieldInventory = 0
WHERE Boat_SerialNo = 'ETWINVTEST01';

-- Verify the changes
SELECT 
    'SerialNumberMaster (AFTER)' as table_name,
    Boat_SerialNo,
    BoatItemNo,
    ERP_OrderNo,
    Active,
    CASE 
        WHEN Active = 1 THEN 'VISIBLE to dealers'
        WHEN Active = 0 THEN 'HIDDEN from dealers'
        ELSE 'UNKNOWN status'
    END as visibility_status
FROM SerialNumberMaster
WHERE Boat_SerialNo = 'ETWINVTEST01'
   OR ERP_OrderNo = 'SO00936074';

SELECT 
    'SerialNumberRegistrationStatus (AFTER)' as table_name,
    Boat_SerialNo,
    SN_MY,
    Registered,
    FieldInventory,
    CASE 
        WHEN Registered = 1 THEN 'SHOWING as registered/sold'
        WHEN Registered = 0 THEN 'Not registered'
        ELSE 'UNKNOWN'
    END as registration_status
FROM SerialNumberRegistrationStatus
WHERE Boat_SerialNo = 'ETWINVTEST01';

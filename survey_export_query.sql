-- ============================================================================
-- Warranty Survey Export Query
-- ============================================================================
-- Purpose: Fetch approved warranty claims with CUSTOMER data for Aimbase survey export
--
-- Key Features:
-- - Uses PartsOrderID AS CLAIMNO (unique identifier)
-- - Gets customer data from OwnerRegistrations (NOT dealer data from warranty claims)
-- - Filters for Approved/Completed claims only
-- - Returns only required fields for Aimbase format
--
-- Date: 2026-01-27
-- ============================================================================

SELECT
    wc.PartsOrderID AS CLAIMNO,
    wc.OrdHdrBoatSerialNo AS HIN,
    wc.OrdHdrStatusLastUpd AS CLAIMDT,
    wc.OrdHdrDealerNo AS DLRNUMBR,
    wc.OrdOptOut,
    sn.Series AS MODELBRD,
    sn.BoatDesc1 AS MODELCOD,
    sn.SerialModelYear AS MODELYER,
    owner.OwnerFirstName AS CFSTNAME,
    owner.OwnerLastName AS CLSTNAME,
    owner.OwnerEmail AS CEMAIL,
    owner.OwnerAddress1 AS CADDRES1,
    owner.OwnerCity AS CCITY,
    owner.OwnerState AS CSTATE,
    owner.OwnerZip AS CPSTCODE,
    owner.OwnerCountry AS CCOUNTRY,
    owner.OwnerDayPhone AS CHMPHONE
FROM WarrantyClaimOrderHeaders wc
LEFT JOIN SerialNumberMaster sn ON wc.OrdHdrBoatSerialNo = sn.Boat_SerialNo
LEFT JOIN OwnerRegistrations owner ON wc.OrdHdrBoatSerialNo = owner.Boat_SerialNo
WHERE wc.OrdHdrPublicStatus IN ('Approved', 'Completed')
  -- Uncomment below to filter for last 7 days (for weekly run):
  -- AND STR_TO_DATE(wc.OrdHdrStatusLastUpd, '%c/%e/%Y') >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
GROUP BY wc.PartsOrderID
ORDER BY STR_TO_DATE(wc.OrdHdrStatusLastUpd, '%c/%e/%Y') DESC;

-- ============================================================================
-- Field Mapping to Aimbase Format:
-- ============================================================================
-- CLAIMNO    = PartsOrderID (unique warranty claim ID)
-- HIN        = Boat Serial Number
-- CLAIMDT    = Claim status last updated date
-- DLRNUMBR   = Dealer number
-- OrdOptOut  = Customer opt-out flag (0=send survey, 1=opted out)
-- MODELBRD   = Boat series (S, M, L, QX, etc.)
-- MODELCOD   = Boat model description
-- MODELYER   = Model year
-- CFSTNAME   = Customer First Name (from OwnerRegistrations)
-- CLSTNAME   = Customer Last Name (from OwnerRegistrations)
-- CEMAIL     = Customer Email (from OwnerRegistrations)
-- CADDRES1   = Customer Address (from OwnerRegistrations)
-- CCITY      = Customer City (from OwnerRegistrations)
-- CSTATE     = Customer State (from OwnerRegistrations)
-- CPSTCODE   = Customer Zipcode (from OwnerRegistrations)
-- CCOUNTRY   = Customer Country (from OwnerRegistrations)
-- CHMPHONE   = Customer Phone (from OwnerRegistrations)

-- ============================================================================
-- Data Quality Notes:
-- ============================================================================
-- Coverage Statistics (as of 2026-01-27):
-- - Total claims: 118,801
-- - With customer email: 114,916 (96.7%)
-- - With first name: 126,546 (100%)
-- - With last name: 126,546 (100%)
-- - With zipcode: 126,471 (99.9%)
--
-- Why OwnerRegistrations instead of WarrantyClaimOrderHeaders?
-- - OrdHdrEmail contains DEALER emails (parts@dealer.com)
-- - OrdHdrOwnerZip is 99.7% EMPTY (only 0.3% populated)
-- - OwnerRegistrations contains actual CUSTOMER contact data
--
-- ============================================================================

-- ============================================================================
-- DEALER CREDIT HOLD - EOS Stored Statements
-- Add each block below as a sStatement in the EOS admin interface
-- ============================================================================


-- ============================================================================
-- DLRS_GET_ALL_ON_HOLD
-- Params: none
-- Returns all dealers currently on hold with columns the JS expects:
--   DlrNo, DealerName, Address, Date_added, Added_by, isOnHold
-- ============================================================================
SELECT
    h.DlrNo,
    d.DealerName,
    CONCAT_WS(' ', d.Add1, d.City, d.State, d.Zip) AS Address,
    h.Date_added,
    h.Added_by,
    h.Is_on_hold AS isOnHold
FROM warrantyparts.Dealers_on_hold h
LEFT JOIN Eos.dealers d ON h.DlrNo = d.DlrNo
WHERE h.Is_on_hold = '1'
ORDER BY h.DlrNo


-- ============================================================================
-- DLRS_GET_ALL
-- Params: none
-- Returns all active dealers for the Add dropdown
-- ============================================================================
SELECT DlrNo, DealerName
FROM Eos.dealers
WHERE DoNotShowFlag = 0
ORDER BY DealerName


-- ============================================================================
-- DLRS_ADD_ON_HOLD
-- Params: @PARAM1 = DlrNo, @PARAM2 = Added_by, @PARAM3 = Updated_by
-- Called as: sStatement('DLRS_ADD_ON_HOLD', [dlrNo, eos.user.username, eos.user.username])
-- ============================================================================
INSERT INTO warrantyparts.Dealers_on_hold
    (DlrNo, Is_on_hold, Added_by, Date_added, Updated_by, Date_updated)
VALUES
    (@PARAM1, '1', @PARAM2, CURDATE(), @PARAM3, CURDATE())
ON DUPLICATE KEY UPDATE
    Is_on_hold   = '1',
    Updated_by   = @PARAM3,
    Date_updated = CURDATE()


-- ============================================================================
-- DLRS_REMOVE_ON_HOLD
-- Params: @PARAM1 = DlrNo
-- Called as: sStatement('DLRS_REMOVE_ON_HOLD', [dlrNo])
-- ============================================================================
UPDATE warrantyparts.Dealers_on_hold
SET
    Is_on_hold   = '0',
    Date_updated = CURDATE()
WHERE DlrNo = @PARAM1

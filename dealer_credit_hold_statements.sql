-- ============================================================================
-- DEALER CREDIT HOLD - EOS Stored Statements
-- Add each query below as a new sStatement in the EOS admin interface
-- ============================================================================


-- ============================================================================
-- IS_CREDIT_HOLD_MANAGER
-- Params: @PARAM1 = username (from getValue('EOS','USER'))
-- Returns: 1 row if authorized, 0 rows if not
-- ============================================================================
SELECT username FROM warrantyparts.credit_hold_managers WHERE username = @PARAM1


-- ============================================================================
-- GET_DEALER_HOLD_STATUS
-- Params: @PARAM1 = DlrNo (8-char dealer number)
-- Returns: hold record if it exists (check Is_on_hold = '1' for active hold)
-- ============================================================================
SELECT
    h.DlrNo,
    h.Is_on_hold,
    h.Added_by,
    h.Date_added,
    h.Updated_by,
    h.Date_updated,
    d.DealerName
FROM warrantyparts.Dealers_on_hold h
LEFT JOIN Eos.dealers d ON h.DlrNo = d.DlrNo
WHERE h.DlrNo = @PARAM1


-- ============================================================================
-- GET_ALL_HELD_DEALERS
-- Params: none
-- Returns: all dealers currently on hold (Is_on_hold = '1')
-- ============================================================================
SELECT
    h.DlrNo,
    h.Is_on_hold,
    h.Added_by,
    h.Date_added,
    h.Updated_by,
    h.Date_updated,
    d.DealerName
FROM warrantyparts.Dealers_on_hold h
LEFT JOIN Eos.dealers d ON h.DlrNo = d.DlrNo
WHERE h.Is_on_hold = '1'
ORDER BY d.DealerName


-- ============================================================================
-- SET_DEALER_ON_HOLD
-- Params: @PARAM1 = DlrNo, @PARAM2 = user email (Added_by / Updated_by)
-- Inserts new hold or updates existing row to Is_on_hold = '1'
-- ============================================================================
INSERT INTO warrantyparts.Dealers_on_hold
    (DlrNo, Is_on_hold, Added_by, Date_added, Updated_by, Date_updated)
VALUES
    (@PARAM1, '1', @PARAM2, CURDATE(), @PARAM2, CURDATE())
ON DUPLICATE KEY UPDATE
    Is_on_hold  = '1',
    Updated_by  = @PARAM2,
    Date_updated = CURDATE()


-- ============================================================================
-- REMOVE_DEALER_HOLD
-- Params: @PARAM1 = DlrNo, @PARAM2 = user email (Updated_by)
-- Sets Is_on_hold = '0', does NOT delete the row (preserves audit trail)
-- ============================================================================
UPDATE warrantyparts.Dealers_on_hold
SET
    Is_on_hold   = '0',
    Updated_by   = @PARAM2,
    Date_updated = CURDATE()
WHERE DlrNo = @PARAM1

# Sales Rep Block Triggers (2026-03-05)

## Purpose
Prevent Jake Jackson (SalesPersonNo=300) and Sam Girten (SalesPersonNo=38) from being
re-inserted into dealer tables by the CSIPRD sync job.

## Active Triggers

| Database | Table | Trigger Name | Status |
|----------|-------|-------------|--------|
| Eos | dealers | trg_block_salesrep_dealers | ACTIVE |
| warrantyparts | dealer_labor_misc | trg_block_salesrep_dealer_labor_misc | ACTIVE |

## Removed Trigger (2026-03-16)

| Database | Table | Trigger Name | Reason |
|----------|-------|-------------|--------|
| Update_Tables | dealerlist | trg_block_salesrep_dealerlist | DROPPED — caused JAMS job failure |

The `dealerlist` trigger was dropped because MySQL does not allow a trigger to modify
the same table being operated on by `LOAD DATA LOCAL INFILE` (error 1442). The JAMS
job `upload_dealer_list_mysql.php` uses bulk load into `dealerlist`, which conflicted.

Blocking at `Eos.dealers` is sufficient — `DLR_UPDATE` writes to `Eos.dealers` after
reading from `dealerlist`, so the reps are still blocked before they reach the live table.

## Behavior
- Fires AFTER INSERT only
- Only acts on rows where `SalesPerson IN ('JAKE JACKSON', 'SAM GIRTEN')`
- Silently deletes the offending row — no error raised to the calling process
- All other inserts pass through completely unaffected

## Important Warning
If these reps ever need to be legitimately re-added, the triggers must be dropped first
or the inserts will silently fail.

## Drop Triggers (if needed)
```sql
DROP TRIGGER IF EXISTS Eos.trg_block_salesrep_dealers;
DROP TRIGGER IF EXISTS warrantyparts.trg_block_salesrep_dealer_labor_misc;
```

# Sales Rep Block Triggers (2026-03-05)

## Purpose
Prevent Jake Jackson (SalesPersonNo=300) and Sam Girten (SalesPersonNo=38) from being
re-inserted into dealer tables by the CSIPRD sync job.

## Triggers Created

| Database | Table | Trigger Name |
|----------|-------|-------------|
| Update_Tables | dealerlist | trg_block_salesrep_dealerlist |
| Eos | dealers | trg_block_salesrep_dealers |
| warrantyparts | dealer_labor_misc | trg_block_salesrep_dealer_labor_misc |

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
DROP TRIGGER IF EXISTS Update_Tables.trg_block_salesrep_dealerlist;
DROP TRIGGER IF EXISTS Eos.trg_block_salesrep_dealers;
DROP TRIGGER IF EXISTS warrantyparts.trg_block_salesrep_dealer_labor_misc;
```

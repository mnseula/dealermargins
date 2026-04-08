# How to Generate Family Code SQL Files from Excel

## Overview

John provides an Excel file with family codes, descriptions, and item mappings. Generate two SQL files from this data.

## Input: Excel File Structure

The Excel file (e.g., `Bennington Purchasing Commodities_SQL.xlsx`) contains:
- **Family Codes tab** (or columns): family_code, description
- **Items tab** (or columns): item number, family_code

## Output: Two SQL Files

### 1. Query1InsertFamilyCodes.sql

INSERT statements for `famcode_mst` table:

```sql
insert into famcode_mst (site_ref,family_code,[description]) VALUES('BENN','CMP-PLASTC','FORMED/MOLDED/CNC PLASTIC & PLASTIC ASSEMBLIES');
insert into famcode_mst (site_ref,family_code,[description]) VALUES('BENN','CMP-STEER','STEERING SYSTEMS, THRUSTERS');
```

**Rules:**
- `site_ref` is always `'BENN'`
- `description` is capped at 40 characters (truncated if longer)
- One INSERT per family code
- Skip any family codes that already exist in the database

### 2. Query2UpdateItems.sql

UPDATE statements for `item_mst` table:

```sql
update item_mst set family_code = 'CMP-PRDSUP' where item = '021901' and site_ref = 'BENN';
update item_mst set family_code = 'EXT-PNTRLS' where item = '017694' and site_ref = 'BENN';
```

**Rules:**
- `site_ref` is always `'BENN'`
- One UPDATE per item
- No semicolons needed (optional but recommended)

## Excel Formula Approach

In Excel, create a formula column that generates the SQL:

### For Query1 (Family Codes):
```
="insert into famcode_mst (site_ref,family_code,[description]) VALUES('BENN','" & A2 & "','" & LEFT(B2,40) & "');"
```
Where:
- Column A = family_code
- Column B = description (LEFT truncates to 40 chars)

### For Query2 (Item Updates):
```
="update item_mst set family_code = '" & B2 & "' where item = '" & A2 & "' and site_ref = 'BENN';"
```
Where:
- Column A = item number
- Column B = family_code

## Process

1. Open John's Excel file
2. Generate SQL using formulas above
3. Copy formula results to text files:
   - Save family code INSERTs as `Query1InsertFamilyCodes.sql`
   - Save item UPDATEs as `Query2UpdateItems.sql`
4. Review for duplicates (can wrap UPDATEs in a transaction or use DISTINCT)
5. Run against database

## Database Tables

- `famcode_mst` - stores family codes and descriptions
- `item_mst` - stores items, with `family_code` column for assignment

## Notes

- The OLD_ prefixed files show the previous version for reference
- Family codes use prefixes: CMP- (Commodity), INT- (Interior), EXT- (Exterior), ELE- (Electrical)
- Always check if family codes already exist before inserting (INSERT may fail on duplicates)

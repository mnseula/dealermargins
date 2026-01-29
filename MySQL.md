# MySQL Database Import Documentation

**Database:** `warrantyparts_test`  
**Server:** `ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com:3306`  
**User:** `awsmaster`  
**Password:** `VWvHG9vfG23g7gD`  

---

## Overview

This document describes the C# .NET data synchronization process that imports boat order data from Microsoft SQL Server (CSI/ERP system) into MySQL tables. The primary purpose is to sync actual sold boat data with pricing for use in the dealer margin and quote system.

**Source System:** Microsoft SQL Server (CSISTG database)  
**Destination System:** MySQL (warrantyparts_test database)  
**Import Method:** Export to CSV → LOAD DATA LOCAL INFILE

---

## Primary Import Table: `BoatOptions25_test`

### Table Purpose
Stores line item details for sold boats including pricing, quantities, and product categorization. Used for calculating actual MSRP and generating window stickers.

### Connection Details
```csharp
MySqlConnectionString = "Server=ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com;" +
                        "Port=3306;" +
                        "Database=warrantyparts_test;" +
                        "Uid=awsmaster;" +
                        "Pwd=VWvHG9vfG23g7gD;" +
                        "AllowLoadLocalInfile=True;" +
                        "AllowUserVariables=true;";

MySqlTargetTable = "BoatOptions25_test";
```

### Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  SQL SERVER (Source)                                            │
│  Server: MPL1STGSQL086.POLARISSTAGE.COM                        │
│  Database: CSISTG                                               │
│  Tables: coitem_mst, item_mst, inv_item_mst, etc.              │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          │ C# DataSync_Process
                          │ ExportFromSqlServerAndImportToMySql()
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  TEMPORARY CSV FILE                                             │
│  Format: Comma-separated values                                 │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          │ LoadCsvToMySql()
                          │ LOAD DATA LOCAL INFILE
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  MYSQL (Destination)                                            │
│  Database: warrantyparts_test                                   │
│  Table: BoatOptions25_test                                      │
└─────────────────────────────────────────────────────────────────┘
```

### SQL Server Source Tables

The import query joins multiple SQL Server tables:

| Table | Purpose |
|-------|---------|
| `coitem_mst` | Customer order line items (primary data source) |
| `inv_item_mst` | Invoice items (links orders to invoices) |
| `arinv_mst` | Accounts receivable invoices (invoice dates) |
| `co_mst` | Customer orders (order type) |
| `item_mst` | Item master (descriptions, series, product codes) |
| `prodcode_mst` | Product codes (MCT descriptions) |
| `serial_mst` | Serial number master (HIN/serial numbers) |

### SQL Query (Source)

```sql
SELECT DISTINCT
    LEFT(coi.co_num, 30) AS [ERP_OrderNo],
    LEFT(coi.Uf_BENN_BoatSerialNumber, 15) AS [BoatSerialNo],
    LEFT(coi.Uf_BENN_BoatModel, 14) AS [BoatModelNo],
    coi.co_line AS [LineNo],
    LEFT(coi.item, 30) AS [ItemNo],
    LEFT(im.description, 50) AS [ItemDesc1],
    LEFT(im.Uf_BENN_Description2, 50) AS [ItemDesc2],
    CAST((coi.price * coi.qty_ordered) AS DECIMAL(10,2)) AS [ExtSalesAmount],
    coi.qty_invoiced AS [QuantitySold],
    LEFT(im.Uf_BENN_Series, 5) AS [Series],
    LEFT(coi.Uf_BENN_BoatWebOrderNumber, 30) AS [WebOrderNo],
    LEFT(co.type, 1) AS [Orig_Ord_Type],
    ah.apply_to_inv_num AS [ApplyToNo]
FROM [CSISTG].[dbo].[coitem_mst] coi
LEFT JOIN [CSISTG].[dbo].[inv_item_mst] iim 
    ON coi.co_num = iim.co_num 
    AND coi.co_line = iim.co_line 
    AND coi.co_release = iim.co_release 
    AND coi.site_ref = iim.site_ref
LEFT JOIN [CSISTG].[dbo].[arinv_mst] ah 
    ON iim.inv_num = ah.inv_num 
    AND iim.site_ref = ah.site_ref
LEFT JOIN [CSISTG].[dbo].[co_mst] co 
    ON coi.co_num = co.co_num 
    AND coi.site_ref = co.site_ref
LEFT JOIN [CSISTG].[dbo].[item_mst] im 
    ON coi.item = im.item 
    AND coi.site_ref = im.site_ref
LEFT JOIN [CSISTG].[dbo].[prodcode_mst] pcm 
    ON im.Uf_BENN_MaterialCostType = pcm.product_code 
    AND im.site_ref = pcm.site_ref
LEFT JOIN [CSISTG].[dbo].[serial_mst] ser 
    ON coi.co_num = ser.ref_num 
    AND coi.co_line = ser.ref_line 
    AND coi.co_release = ser.ref_release 
    AND coi.item = ser.item 
    AND coi.site_ref = ser.site_ref 
    AND ser.ref_type = 'O'
ORDER BY [ERP_OrderNo], [LineNo];
```

### Fields Imported to MySQL

| Field | Source | Description |
|-------|--------|-------------|
| `ERP_OrderNo` | coi.co_num | ERP Order Number (e.g., "SO00935977") |
| `BoatSerialNo` | coi.Uf_BENN_BoatSerialNumber | Boat HIN/Serial Number |
| `BoatModelNo` | coi.Uf_BENN_BoatModel | Boat model number |
| `LineNo` | coi.co_line | Line number within order |
| `ItemNo` | coi.item | Item number |
| `ItemDesc1` | im.description | Primary item description |
| `ItemDesc2` | im.Uf_BENN_Description2 | Secondary description |
| `ExtSalesAmount` | (coi.price * qty_ordered) | Extended sales amount (pricing) |
| `QuantitySold` | coi.qty_invoiced | Quantity invoiced |
| `Series` | im.Uf_BENN_Series | Boat series (Q, QX, SV, etc.) |
| `WebOrderNo` | coi.Uf_BENN_BoatWebOrderNumber | Web order reference |
| `Orig_Ord_Type` | co.type | Original order type |
| `ApplyToNo` | ah.apply_to_inv_num | Apply-to invoice number |

### Import Process (Two-Step)

#### Step 1: Export to CSV
```csharp
private long ExportSqlServerToCsv()
{
    using (System.Data.SqlClient.SqlConnection sqlConn = 
           new System.Data.SqlClient.SqlConnection(SqlServerConnectionString))
    {
        sqlConn.Open();
        using (System.Data.SqlClient.SqlCommand cmd = 
               new System.Data.SqlClient.SqlCommand(QUERY, sqlConn))
        {
            using (System.Data.SqlClient.SqlDataReader reader = cmd.ExecuteReader())
            {
                // Write to CSV file
                while (reader.Read())
                {
                    // Format and write each row
                }
            }
        }
    }
}
```

#### Step 2: Load to MySQL
```csharp
private void LoadCsvToMySql()
{
    using (MySqlConnection mySqlConn = new MySqlConnection(MySqlConnectionString))
    {
        mySqlConn.Open();
        
        string loadQuery = $@"
            LOAD DATA LOCAL INFILE '{csvFilePath}'
            INTO TABLE {MySqlTargetTable}
            FIELDS TERMINATED BY ','
            OPTIONALLY ENCLOSED BY '\"'
            LINES TERMINATED BY '\n'
            IGNORE 1 LINES;
        ";
        
        using (MySqlCommand cmd = new MySqlCommand(loadQuery, mySqlConn))
        {
            cmd.ExecuteNonQuery();
        }
    }
}
```

### Connection Prerequisites
```csharp
MySqlConnectionString += "AllowLoadLocalInfile=True;AllowUserVariables=true;";
```

---

## Secondary Tables

### 1. `PartsOrderLines` (EOS Database)

**Purpose:** Updates UPS tracking information for warranty parts orders

**Connection:** Uses `EOS_ConnectionString` from config

**Update Query:**
```csharp
string updateQuery = @"
    UPDATE PartsOrderLines 
    SET OrdLineShipmentTrackingNo = @trackingNo, 
        OrdLineStatus = 'completed', 
        OrdLinePublicStatus = 'Completed', 
        OrdLineSttusLastUpd = @date 
    WHERE ERP_OrderNo = @orderNo;
";
```

**Fields Updated:**
- `OrdLineShipmentTrackingNo` - UPS tracking number
- `OrdLineStatus` - Order status ('completed')
- `OrdLinePublicStatus` - Public status ('Completed')
- `OrdLineSttusLastUpd` - Last update timestamp

### 2. `CustAddr` (EOS Database)

**Purpose:** Customer shipping addresses

**Source:** `custaddr_mst` table from SQL Server

**Fields:**
- `cust_num` - Customer number
- `cust_seq` - Address sequence
- `name` - Customer/address name
- `is_default_ship_to` - Flag for default shipping address (1 = default)

**Logic:**
```csharp
CASE 
    WHEN ca.cust_seq = (SELECT [customer_mst].default_ship_to 
                        FROM [customer_mst] 
                        WHERE [customer_mst].cust_num = ca.cust_num) 
    THEN 1
    ELSE 0
END AS [is_default_ship_to]
```

### 3. Warranty Parts Table

**Purpose:** Parts catalog with pricing and vendor information

**Source Tables:**
- `item_mst` - Item master
- `itemprice_mst` - Item pricing (latest effective date)
- `itemvend_mst` - Vendor information (highest rank)

**Excluded Family Codes:**
```sql
family_code NOT IN (
    '2Tube SPS', '2TubeELFW', '2TubeELSW', '3Tube SPS', '3TubeELSPS', 
    '3TubeExp', 'AccentPnl', 'AcntPnlAft', 'BaseVinyl', 'BOA-IO-L', 
    'BOA-IO-Q', 'BOA-IO-QX', 'BOA-IO-R', 'BOA-IO-RX', 'BOA-IO-S', 
    'BOA-L', 'BOA-LT', 'BOA-LX', 'BOA-LXS', 'BOA-Q', 'BOA-QX', 
    'BOA-QXS', 'BOA-R', 'BOA-RT', 'BOA-RX', 'BOA-S', 'BOA-SV', 
    'BOA-SX', 'ColorPkg', 'CUSTOM', 'DISC', ...
)
```

---

## Other Related Tables

### `BoatConfigurationAttributes`

**Purpose:** Stores customer configuration choices

**Populated by:** `import_configuration_attributes.py` (Python script)

**Fields:**
- `boat_serial_no` - HIN
- `boat_model_no` - Model number
- `erp_order_no` - ERP order number
- `web_order_no` - Web order number
- `config_id` - Configuration ID
- `attr_name` - Attribute name (e.g., "Performance Package")
- `attr_value` - Selected value
- `cfg_value` - Configuration value
- `comp_id` - Component ID
- `series` - Boat series

### `SerialNumberMaster`

**Purpose:** Master registry of all boats produced

**Records:** 62,781+ boats

**Fields:**
- `SerialNumber` - HIN
- `BoatModel` - Model number
- `DealerID` - Dealer identifier
- `InvoiceDate` - Invoice date

---

## Data Usage

### Window Sticker Generation

The imported data is used to calculate actual MSRP for sold boats:

```sql
-- Calculate MSRP breakdown from BoatOptions25_test
SELECT
    SUM(CASE WHEN ItemMasterProdCat='BS1' THEN ExtSalesAmount END) as base_boat,
    SUM(CASE WHEN ItemMasterProdCat='EN7' THEN ExtSalesAmount END) as engine,
    SUM(CASE WHEN ItemMasterProdCat='ACC' THEN ExtSalesAmount END) as accessories
FROM BoatOptions25_test
WHERE BoatSerialNo = 'ETWP6278J324'
```

**Example:**
```
Base Boat (BS1):      $25,895.00
Engine (EN7):         $9,011.00
Accessories (ACC):    $712.00
─────────────────────────────────
TOTAL MSRP:           $35,618.00
```

### Product Categories

Data is categorized by `ItemMasterProdCat`:

| Code | Description | Used For |
|------|-------------|----------|
| `BS1` | Base Boat | Base boat MSRP |
| `EN7` / `ENG` | Engine | Engine package pricing |
| `ACC` | Accessories | Option/accessory pricing |
| `L2` | Level 2 | Secondary options |
| `MTR` | Motor | Motor-related items |
| `OA` | Optional Accessories | Optional add-ons |
| `PL` | Pontoons | Pontoon components |
| `DC` | Deck Components | Deck parts |
| `ENI` | Engine Installation | Installation charges |

---

## Comparison: C# Import vs Python Import

| Aspect | C# Import | Python Import |
|--------|-----------|---------------|
| **Script** | `DataSync_Process` | `import_line_items.py` |
| **Method** | Export to CSV → LOAD DATA INFILE | Direct pymssql → mysql.connector |
| **Speed** | Fast (bulk load) | Slower (row-by-row) |
| **Use Case** | Production sync | Development/testing |
| **Table** | `BoatOptions25_test` | `BoatOptions25_test` |

---

## Connection Strings Reference

### SQL Server (Source)
```csharp
// Production
Server=MPL1STGSQL086.POLARISSTAGE.COM;
Database=CSISTG;
User ID=svccsimarine;
Password=CNKmoFxEsXs0D9egZQXH;
Encrypt=True;
TrustServerCertificate=True;
```

### MySQL (Destination)
```csharp
Server=ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com;
Port=3306;
Database=warrantyparts_test;
Uid=awsmaster;
Pwd=VWvHG9vfG23g7gD;
AllowLoadLocalInfile=True;
AllowUserVariables=true;
```

### EOS Database (UPS Tracking)
```csharp
// From ConfigurationManager
ConnectionStrings["EOS_ConnectionString"]
```

### Syteline Database
```csharp
// From ConfigurationManager
ConnectionStrings["Syteline_ConnectionString"]
```

### BRAIN Database (UPS Import)
```csharp
// From ConfigurationManager
ConnectionStrings["BRAIN_ConnectionString"]
```

---

## Security Notes

⚠️ **Important:** Connection strings with credentials are hardcoded in the C# source code. Consider:
- Using configuration files or environment variables
- Implementing proper secret management
- Restricting database user permissions
- Using SSL/TLS encryption for connections

---

## Troubleshooting

### Import Issues

**No data imported:**
- Check SQL Server connectivity to MPL1STGSQL086.POLARISSTAGE.COM
- Verify CSISTG database is accessible
- Confirm site_ref = 'BENN' filter is correct

**LOAD DATA INFILE fails:**
- Ensure `AllowLoadLocalInfile=True` is in connection string
- Verify MySQL user has FILE privilege
- Check CSV file permissions

**Duplicate key errors:**
- Table likely has unique constraints on key fields
- Consider using `ON DUPLICATE KEY UPDATE` or truncating first

### Data Quality

**Missing serial numbers:**
- Check `Uf_BENN_BoatSerialNumber` field in source
- Filter may be excluding valid records

**Zero or NULL prices:**
- Verify `coi.price` and `qty_ordered` are populated
- Check for unshipped/uninvoiced orders

---

## Related Files

- `import_line_items.py` - Python alternative import script
- `import_configuration_attributes.py` - Configuration attributes import
- `generate_window_sticker_with_pricing.py` - Uses BoatOptions data
- `MSSQL.md` - MSSQL database documentation
- `upload_margin.py` - Uploads dealer margins to CPQ

---

## Last Updated

January 29, 2026

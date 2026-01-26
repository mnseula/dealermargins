namespace CustomerPortalTools
{
    /// <summary>
    /// Imports boat configuration attributes from SQL Server to MySQL
    /// Pulls Performance Package and other configuration data from cfg_attr_mst table
    /// </summary>
    public class ConfigurationAttributesImporter
    {
        // --- SQL Server Configuration ---
        private const string SqlServerConnectionString = "Server=MPL1STGSQL086.POLARISSTAGE.COM;Database=CSISTG;User ID=svccsimarine;Password=CNKmoFxEsXs0D9egZQXH;Encrypt=True;TrustServerCertificate=True;";

        // --- MySQL Configuration ---
        private const string MySqlConnectionString = "Server=ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com;Port=3306;Database=warrantyparts_test;Uid=awsmaster;Pwd=VWvHG9vfG23g7gD;AllowLoadLocalInfile=True;AllowUserVariables=true;";
        private const string MySqlTargetTable = "BoatConfigurationAttributes";

        // --- CSV File Configuration ---
        private const string CsvFilePath = @"C:\temp\boat_config_attrs_export.csv";

        /// <summary>
        /// SQL Query to extract configuration attributes from SQL Server
        /// Key field: cfgaUf_BENN_Cfg_Value contains the actual configuration value
        /// Focuses on key attributes like Performance Package, Console, Fuel, etc.
        /// </summary>
        private const string SqlServerQuery = @"
SELECT
    LEFT(coi.Uf_BENN_BoatSerialNumber, 15) AS [BoatSerialNo],
    LEFT(coi.Uf_BENN_BoatModel, 14) AS [BoatModelNo],
    LEFT(coi.co_num, 30) AS [ERP_OrderNo],
    LEFT(coi.Uf_BENN_BoatWebOrderNumber, 30) AS [WebOrderNo],
    LEFT(coi.config_id, 50) AS [ConfigID],

    -- Attribute details
    LEFT(attr.attr_name, 100) AS [AttrName],
    LEFT(attr.attr_value, 255) AS [AttrValue],
    LEFT(attr.cfgaUf_BENN_Cfg_Value, 255) AS [CfgValue],
    LEFT(attr.comp_id, 50) AS [CompID],

    -- Boat metadata
    LEFT(im.Uf_BENN_Series, 5) AS [Series],
    LEFT(iim.inv_num, 30) AS [InvoiceNo],
    CASE
        WHEN ah.inv_date IS NOT NULL
        THEN CONVERT(INT, CONVERT(VARCHAR(8), ah.inv_date, 112))
        ELSE NULL
    END AS [InvoiceDate]

FROM [CSISTG].[dbo].[coitem_mst] coi

-- Join to configuration attributes table
INNER JOIN [CSISTG].[dbo].[cfg_attr_mst] attr
    ON coi.config_id = attr.config_id
    AND coi.site_ref = attr.site_ref

-- Join to get boat/item details
LEFT JOIN [CSISTG].[dbo].[item_mst] im
    ON coi.item = im.item
    AND coi.site_ref = im.site_ref

-- Join to get invoice details
LEFT JOIN [CSISTG].[dbo].[inv_item_mst] iim
    ON coi.co_num = iim.co_num
    AND coi.co_line = iim.co_line
    AND coi.co_release = iim.co_release
    AND coi.site_ref = iim.site_ref

LEFT JOIN [CSISTG].[dbo].[arinv_mst] ah
    ON iim.inv_num = ah.inv_num
    AND iim.site_ref = ah.site_ref

WHERE
    coi.config_id IS NOT NULL
    AND coi.site_ref = 'BENN'
    AND attr.attr_name IS NOT NULL
    -- Focus on key configuration attributes
    AND attr.attr_name IN (
        'Performance Package',
        'Fuel',
        'Console',
        'Canvas Color',
        'Captain''s Chairs',
        'Co-Captain''s Chairs',
        'Trim Accents',
        'BASE VINYL',
        'FLOORING',
        'FURNITURE UPGRADE',
        'Tables - Bow',
        'Tables - Aft',
        'Rockford Fosgate Stereo',
        'Main Display',
        'Additional Display',
        'Exterior Color Packages',
        'Bimini Cable Stays',
        'Aft Bimini Tops',
        'Bow Bimini Tops',
        'Arch',
        'Steering Wheels',
        'Lifting Strakes',
        'Saltwater Package'
    )
    -- Uncomment to test with specific order:
    -- AND coi.co_num = 'SO00930192'

ORDER BY
    coi.co_num,
    attr.attr_name;
";

        public void ExportFromSqlServerAndImportToMySql()
        {
            Console.WriteLine("Starting Boat Configuration Attributes Import Process...");
            long rowsExported = ExportSqlServerToCsv();

            if (rowsExported > 0)
            {
                LoadCsvToMySql();
            }
            else
            {
                Console.WriteLine("No rows were exported from SQL Server. MySQL import will be skipped.");
            }
            Console.WriteLine("\nBoat Configuration Attributes import process finished.");
        }

        private long ExportSqlServerToCsv()
        {
            long rowsExported = 0;
            Console.WriteLine("Starting SQL Server configuration attributes export to CSV...");
            try
            {
                using (System.Data.SqlClient.SqlConnection sqlConn = new System.Data.SqlClient.SqlConnection(SqlServerConnectionString))
                {
                    sqlConn.Open();
                    Console.WriteLine("Connected to SQL Server.");
                    using (System.Data.SqlClient.SqlCommand sqlCmd = new System.Data.SqlClient.SqlCommand(SqlServerQuery, sqlConn))
                    {
                        sqlCmd.CommandTimeout = 300; // 5 minutes

                        using (System.Data.SqlClient.SqlDataReader reader = sqlCmd.ExecuteReader())
                        {
                            Console.WriteLine($"Executing query and writing to CSV: {CsvFilePath}");
                            using (StreamWriter writer = new StreamWriter(CsvFilePath, false, Encoding.UTF8))
                            {
                                var columnNames = Enumerable.Range(0, reader.FieldCount)
                                                            .Select(i => FormatCsvField(reader.GetName(i)))
                                                            .ToList();
                                writer.WriteLine(string.Join(",", columnNames));

                                object[] rowValues = new object[reader.FieldCount];
                                while (reader.Read())
                                {
                                    reader.GetValues(rowValues);
                                    var fieldValues = rowValues.Select(FormatCsvField).ToList();
                                    writer.WriteLine(string.Join(",", fieldValues));
                                    rowsExported++;
                                    if (rowsExported % 1000 == 0)
                                    {
                                        Console.WriteLine($"Exported {rowsExported} configuration attributes from SQL Server...");
                                    }
                                }
                            }
                            Console.WriteLine($"Successfully exported {rowsExported} configuration attributes from SQL Server to {CsvFilePath}");
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error during SQL Server export: {ex.Message}");
                Console.WriteLine($"Details: {ex}");
                return 0;
            }
            return rowsExported;
        }

        private void LoadCsvToMySql()
        {
            Console.WriteLine($"\nStarting CSV data import into MySQL table {MySqlTargetTable} from {CsvFilePath}...");
            try
            {
                using (MySqlConnection mysqlConn = new MySqlConnection(MySqlConnectionString))
                {
                    mysqlConn.Open();

                    // Truncate the table before loading new data
                    Console.WriteLine("Truncating existing data...");
                    using (MySqlCommand truncateCommand = new MySqlCommand($"TRUNCATE TABLE {MySqlTargetTable}", mysqlConn))
                    {
                        truncateCommand.ExecuteNonQuery();
                    }

                    Console.WriteLine("Connected to MySQL Server.");

                    // MySQL expects forward slashes or double-backslashes for Windows paths
                    string escapedCsvFilePath = CsvFilePath.Replace(@"\", @"\\");
                    string loadDataQuery =
                        "LOAD DATA LOCAL INFILE '" + escapedCsvFilePath + "' " +
                        "INTO TABLE `" + MySqlTargetTable + "` " +
                        "FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '\"' " +
                        "LINES TERMINATED BY '\\r\\n' " +
                        "IGNORE 1 LINES " +
                        "(boat_serial_no, boat_model_no, erp_order_no, web_order_no, config_id, " +
                        "attr_name, attr_value, cfg_value, comp_id, series, invoice_no, invoice_date);";

                    using (MySqlCommand mysqlCmd = new MySqlCommand(loadDataQuery, mysqlConn))
                    {
                        mysqlCmd.CommandTimeout = 600; // 10 minutes
                        int affectedRows = mysqlCmd.ExecuteNonQuery();
                        Console.WriteLine($"Successfully loaded {affectedRows} configuration attributes into MySQL.");
                    }

                    // Show summary statistics
                    Console.WriteLine("\nImport Summary:");
                    using (MySqlCommand statsCmd = new MySqlCommand(
                        "SELECT attr_name, COUNT(*) as count FROM BoatConfigurationAttributes GROUP BY attr_name ORDER BY count DESC",
                        mysqlConn))
                    {
                        using (var reader = statsCmd.ExecuteReader())
                        {
                            Console.WriteLine("\nConfiguration Attributes Imported:");
                            while (reader.Read())
                            {
                                Console.WriteLine($"  {reader["attr_name"]}: {reader["count"]} records");
                            }
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error during MySQL import: {ex.Message}");
                Console.WriteLine($"Details: {ex}");
                throw;
            }
        }

        private string FormatCsvField(object field)
        {
            if (field == null || field == DBNull.Value) return "";
            string value = field.ToString();
            if (value.Contains("\""))
            {
                value = value.Replace("\"", "\"\"");
            }
            if (value.Contains(",") || value.Contains("\n") || value.Contains("\r") || value.Contains("\""))
            {
                return "\"" + value + "\"";
            }
            return value;
        }
    }
}

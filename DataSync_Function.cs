using System;
using System.Collections.Generic;
using System.Data.SqlClient;
using System.Data;
using System.Diagnostics.Eventing.Reader;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Net.Http;
using IdentityModel.Client;
using Newtonsoft.Json;
using System.Reflection;
using System.Security.Permissions;
using Newtonsoft.Json.Linq;
using System.Net;
using System.Numerics;
using MySql.Data;
using MySql.Data.MySqlClient;
using System.IO;
using Mysqlx.Crud;
using MySqlX.XDevAPI.Relational;
using Org.BouncyCastle.Asn1.X509.Qualified;
using Mysqlx;
using System.Diagnostics;
using System.Text.RegularExpressions;
using System.Configuration;


namespace CustomerPortalTools
{
    internal class DataSync_Functions
    {




#if DEBUG
        // DEV CONNECTION SETTINGS
        private const string ClientId = "infor~eyNXA1u0X6-3H7e6EJ2cgnja0E_ZpTi9Y7rY9w7yDnM";
        private const string ClientSecret = "jNUe6UsDOMnG2-cMhTtMEEDaT2k9NXKFA6d0DxXHdapC9_vDF9zTnBceEmlHG4piLxmKrJY8wzOStm7_IBq6QA";
        private const string TokenEndpoint = "https://inforosmarine.polarisdev.com/InforIntSTS/connect/token";
        private const string ServiceAccountAccessKey = "infor#sBd7sS2nqU42D6LB6x1AEmaXDhPhmCXNNr7K2rzEQdSQtXZdw99NyWh0Yby0NclvzwOqwM4QvnI9UrusnAnDpQ";
        private const string ServiceAccountSecretKey = "rqwbYLHqYwloDXaNJFhMPuHezu9FA5GFsCp3gwYo7VTayFC_Uj_MWHRyAJRk_GEP6h7lKG4IvMYFHs_LT1Qwgw";
        private const string Config = "BENN";
        private const string WebString = "https://inforosmarine.polarisdev.com:7443/infor/CSI/IDORequestService/ido";
#else
        
        //ProdConnection
        private const string ClientId = "infor~s7OR4MFZNE9-KUkiSMgTYksHPogEDyLrE7lWQi__jkY";
        private const string ClientSecret = "rHlJJIQDUSfyjS9VpKt_ES9PqMiqgMrLzeuqO_RHktgHpYqWc6i_3Mb7Qi0fTbpN2WviWB7ortwOxD1qBVUPtg";
        private const string TokenEndpoint = "https://inforosmarine.polarisind.com/InforIntSTS/connect/token";
        private const string ServiceAccountAccessKey = "infor#qEgvEU6jCyxlqd1WYdGXv0r28wVX1ykZz2W5Exir0iWwjOCitHou9mdwRx1IutTEb5cXj9vZdzC3mCbh3ObdAA";
        private const string ServiceAccountSecretKey = "aCcZFWf0AlREKiwNs1dZCNjG7i9qdnkQr2W6P4zoMZaocDytA0Y4AYA-OLHTb-cr8tq5CvB5uq-5_TpH4JDTpA";
        private const string Config = "CSIPRD_BENN";
        public const string WebString = "https://inforosmarine.polarisind.com:7443/infor/CSI/IDORequestService/ido";

#endif


        private static DataTable SalesOrders_w_UPS_Tracking = new DataTable();
        private static DataTable SalesOrders_w_Tracking = new DataTable();
        private static string SalesOrder, UPS_VALUE;
        private static int actionResult = 1;

        public static int DataSync_Action()
        {
            SalesOrders_w_UPS_Tracking = get_Brain_UPS_TRACKING();

            if (SalesOrders_w_UPS_Tracking.Rows.Count > 0)
            {
                //There is data in brain with WN or WP in its sales order, try to update it!

                // Count the rows from today's date
                int todayCount = SalesOrders_w_UPS_Tracking.AsEnumerable()
                    .Count(row => DateTime.TryParseExact(row.Field<string>("UPS_Date"), "yyyyMMddHHmmss", null, System.Globalization.DateTimeStyles.None, out DateTime upsDate) && upsDate.Date == DateTime.Today);

                if (todayCount == 0)
                {

                    //This catches the case where there were rows to process but none of them were from today.
                    Email.sendMail("specs@benningtonmarine.com;DWallace@benningtonmarine.com;kmiller@benningtonmarine.com;collinvandeventer@benningtonmarine.com", "There was no new UPS data to process. Please verify WorldShip completed it's End Of Day procedures.", "No UPS Tracking Data", "");
                    Console.WriteLine("No rows from today's date.");
                    // You can add additional actions here if needed
                }
                //Loop through BRAIN records from UPS, push to Syteline. 
                foreach (DataRow row in SalesOrders_w_UPS_Tracking.Rows)
                {
                    SalesOrder = row["ERP_OrderNo"].ToString().Replace("\r\n", "");
                    UPS_VALUE = row["UPSTrackingNo"].ToString().Replace("\r\n", "");
                    DateTime UPS_Date = DateTime.ParseExact(row["UPS_Date"].ToString(), "yyyyMMddHHmmss", null);
                    //2. Update Customer Portal DB table field
                    if (SalesOrder.Length > 0 && SalesOrder.Trim() != "")
                    {
                        UPDATE_EOS_UPS_TRACKING(SalesOrder, UPS_VALUE, UPS_Date);
                        //3. Update Syteline EDF field
                        Update_UPSTracking_Syteline(SalesOrder, UPS_VALUE);
                        //4. Query Eos and Syteline to ensure the fields were properly updated. If the changes were verified, update the BRAIN table with a status of success.
                        bool updateComplete = Verify_Changes(SalesOrder, UPS_VALUE);
                        if (updateComplete)
                        {
                            Update_Brain_UPS_Complete(SalesOrder);
                        }
                        else
                        {
                            Update_Brain_Attempts(SalesOrder);
                        }
                    }
                }
            }
            else
            {
                //This catches the cases where there were no rows to process at all.
                Email.sendMail("specs@benningtonmarine.com;sarsenault@benningtonmarine.com;kmiller@benningtonmarine.com", "There was no new UPS data to process. Please verify WorldShip completed it's End Of Day procedures.", "No UPS Tracking Data", "");
                Console.WriteLine("No rows from today's date.");
            }

            CallMethodWithTiming(BulkUpdate_Eos);


            return actionResult;
        }

        private static void WriteDataTableToCsv(System.Data.DataTable table, string filePath)
        {
            using (StreamWriter writer = new StreamWriter(filePath))
            {
                foreach (DataRow row in table.Rows)
                {
                    writer.WriteLine(string.Join(",", row.ItemArray));
                }
            }
        }

        static void CallMethodWithTiming(System.Action method)
        {
                sw.Start();
                method();
                sw.Stop();

                Console.WriteLine("{0}() completed in {1} seconds", method.Method.Name, sw.Elapsed.TotalSeconds);


            }
            catch (Exception ex)
            {
                Console.WriteLine(ex.Message);

            }


                    using (SqlCommand selectCommand = new SqlCommand(SELECT_query, sytelinecon))
                    {
                        selectCommand.Parameters.AddWithValue("@backdate", DateTime.Now.AddDays(-90));
                        using (SqlDataAdapter adapter = new SqlDataAdapter(selectCommand))
                        {
                            adapter.Fill(tbl);
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine(ex.Message);
            }

            return tbl;
        }
        // Function to execute a SQL query and insert the results into a MySQL database
        public static void UploadWarrantyPartsList()
        {
            //Syteline used to pull part information from item_mst
            string sqlServerConnectionString = ConfigurationManager.ConnectionStrings["Syteline_ConnectionString"].ConnectionString;
            string EOS_WarrantyPartsConnStr = ConfigurationManager.ConnectionStrings["EOS_ConnectionString"].ConnectionString;

            string query = @"
                -- Get the latest prices for each item
                WITH LatestPrices AS (
                    SELECT 
                        itemprice_mst.item,
                        itemprice_mst.effect_date,
                        itemprice_mst.unit_price2,
                        ROW_NUMBER() OVER (PARTITION BY itemprice_mst.item ORDER BY itemprice_mst.effect_date DESC) AS rn
                    FROM 
                        [itemprice_mst]
                ),
                -- Get the highest-ranked vendor for each item
                RankedVendors AS (
                    SELECT 
                        itemvend_mst.item,
                        itemvend_mst.vend_item,
                        itemvend_mst.rank,
                        itemvend_mst.vend_num,
                        ROW_NUMBER() OVER (PARTITION BY itemvend_mst.item ORDER BY itemvend_mst.rank DESC) AS rn
                    FROM 
                    (item_mst.family_code NOT IN (
                        '2Tube SPS', '2TubeELFW', '2TubeELSW', '3Tube SPS', '3TubeELSPS', '3TubeExp', 'AccentPnl', 'AcntPnlAft', 
                        'BaseVinyl', 'BOA-IO-L', 'BOA-IO-Q', 'BOA-IO-QX', 'BOA-IO-R', 'BOA-IO-RX', 'BOA-IO-S', 'BOA-L', 'BOA-LT', 
                        'BOA-LX', 'BOA-LXS', 'BOA-Q', 'BOA-QX', 'BOA-QXS', 'BOA-R', 'BOA-RT', 'BOA-RX', 'BOA-S', 'BOA-SV', 'BOA-SX', 
                        'ColorPkg', 'CUSTOM', 'DISC', 'ELE-ELECT', 'ELU-YAM', 'ENG-IO-MER', 'ENG-IO-VOL', 'ENG-OB-BRP', 'ENG-OB-HON', 
                        'ENG-OB-MER', 'ENG-OB-SUZ', 'ENG-OB-VOL', 'ENG-OB-YAM', 'FR-CCPART', 'FR-ENGINES', 'FR-FRT-IN', 'FR-LOCDEL', 
                        'FR-SURCHGE', 'FR-UPSPART', 'FUNDS-ADM', 'FUNDS-WHSL', 'Knockdown', 'NI-0020', 'NI-0040', 'NI-0060', 'NI-0080', 
                        'NI-0090', 'NI-0130', 'NI-GROBOAT', 'NI-SLSTAX', 'NON-Inv', 'PanelColor', 'PP-0001', 'PP-0040', 'PP-0290', 
                        'PP-0291', 'PP-0320', 'PRE-ELECT', 'PRE-HON-L', 'PRE-HON-P', 'PRE-HON-U', 'PRE-MER-IO', 'PRE-MER-L', 'PRE-MER-P', 
                        'PRE-MER-U', 'PRE-OMC-L', 'PRE-OMC-P', 'PRE-OMC-U', 'PRE-SUZ-L', 'PRE-SUZ-P', 'PRE-SUZ-U', 'PRE-VOL-IO', 
                        'PRE-VOL-U', 'PRE-YAM-L', 'PRE-YAM-P', 'PRE-YAM-U', 'ProdComm', 'TowerColor', 'TrimAccent', 'WA-0001', 'WA-0005', 
                        'WA-0010', 'WA-0015', 'WA-0020', 'WA-0030', 'WA-0100', 'WIP-0020', 'YamAnodPkg')
            DataTable dataTable = new DataTable();

            try
            {
                // Execute the SQL query and fill the DataTable
                using (SqlConnection sqlConnection = new SqlConnection(sqlServerConnectionString))
                {
                    sqlConnection.Open();
                    using (SqlCommand command = new SqlCommand(query, sqlConnection))
                    {
                        using (SqlDataAdapter adapter = new SqlDataAdapter(command))
                        {
                            adapter.Fill(dataTable);
                        }
                    }
                }

                using (MySqlConnection mySqlConnection = new MySqlConnection(EOS_WarrantyPartsConnStr))
                {
                    mySqlConnection.Open();

                    // Clear the table before inserting new data
                            MySqlHelper.EscapeString(row["ItemDesc1"].ToString()),
                            MySqlHelper.EscapeString(row["ItemDesc2"].ToString()),
                            MySqlHelper.EscapeString(row["Loc"].ToString()),
                            MySqlHelper.EscapeString(row["VendorName"].ToString()),
                            MySqlHelper.EscapeString(row["ActivityCode"].ToString()),
                            MySqlHelper.EscapeString(row["PurchObsolete"].ToString()),
                            MySqlHelper.EscapeString(row["MCT"].ToString()),
                            MySqlHelper.EscapeString(row["MCTDesc"].ToString()),
                            MySqlHelper.EscapeString(row["ProdCat"].ToString()),
                            MySqlHelper.EscapeString(row["ProdCatDesc"].ToString()),
                            MySqlHelper.EscapeString(row["LastItemRev_MY"].ToString()),
                            MySqlHelper.EscapeString(row["Price"].ToString())));
                    }

                    sCommand.Append(string.Join(",", rows));
                    sCommand.Append(";");

                    // Execute the bulk insert command
                    using (MySqlCommand myCmd = new MySqlCommand(sCommand.ToString(), mySqlConnection))
                    {
                        myCmd.CommandType = CommandType.Text;
                        myCmd.ExecuteNonQuery();
                    }
                }

                Console.WriteLine("Data successfully inserted into MySQL database.");
            }
            catch (Exception ex)
            {
                Console.WriteLine("An error occurred: " + ex.Message);
            }
        }

        public static void BulkUpdate_Eos()
        {
            DataTable SytelineTracking = get_Syteline_TRACKING();

            // Extract ERP_OrderNo values into a list of strings
            List<string> erpOrderNos = new List<string>();
            foreach (DataRow row in SytelineTracking.Rows)
            {
                erpOrderNos.Add(row["ERP_OrderNo"].ToString());
            }

            DataTable EOS_Tracking = get_EOS_TRACKING(erpOrderNos);

            // Join the DataTables and filter the rows where UPSTrackingNo values do not match
            var mismatchedRows = (from eosRow in EOS_Tracking.AsEnumerable()
                                  join sytelineRow in SytelineTracking.AsEnumerable()
                                  on eosRow.Field<string>("ERP_OrderNo") equals sytelineRow.Field<string>("ERP_OrderNo")
                                  where eosRow.Field<string>("TrackingNo") != sytelineRow.Field<string>("UPSTrackingNo")
                                  select new
                                  {
                                      ERP_OrderNo = eosRow.Field<string>("ERP_OrderNo"),
                                      NewUPSTrackingNo = sytelineRow.Field<string>("UPSTrackingNo")
                                  }).Distinct();



            string eosConnStr = ConfigurationManager.ConnectionStrings["EOS_ConnectionString"].ConnectionString;
            using (MySqlConnection EOS_SqlConnection = new MySqlConnection(eosConnStr))
            {
                EOS_SqlConnection.Open();

                using (MySqlTransaction transaction = EOS_SqlConnection.BeginTransaction())
                {
                    try
                    {
                        string updateQuery = @"UPDATE PartsOrderLines 
                                       SET OrdLineShipmentTrackingNo = @trackingNo, 
                                           OrdLineStatus = 'completed', 
                                           OrdLinePublicStatus = 'Completed', 
                                           OrdLineSttusLastUpd = @date 
                                       WHERE ERP_OrderNo = @orderNo;";

                        using (MySqlCommand updateCommand = new MySqlCommand(updateQuery, EOS_SqlConnection, transaction))
                        {
                            updateCommand.Parameters.Add("@trackingNo", MySqlDbType.VarChar);
                            updateCommand.Parameters.Add("@date", MySqlDbType.DateTime);
                            updateCommand.Parameters.Add("@orderNo", MySqlDbType.VarChar);

                            foreach (var row in mismatchedRows)
                            {
                                try
                                {
                                    updateCommand.Parameters["@trackingNo"].Value = row.NewUPSTrackingNo;
                                    updateCommand.Parameters["@date"].Value = DateTime.Now;
                                    updateCommand.Parameters["@orderNo"].Value = row.ERP_OrderNo;

                                    updateCommand.ExecuteNonQuery();
                                }
                                catch (Exception ex)
                                {
                                    Console.WriteLine(ex.Message);
                                }
                            }
                        }

                        transaction.Commit();
                    }
                    catch
                    {
                        transaction.Rollback();
                        throw;
                    }
                }
            }
        }

        private static bool Verify_Changes(string CoNum, string UPS_VALUE)
        {
            DataTable tbl = new DataTable();
            bool EOS_Check = false;
            bool Syteline_Check = false;
            try
            {
                string eosConnStr = ConfigurationManager.ConnectionStrings["EOS_ConnectionString"].ConnectionString;
                using (MySqlConnection eos_con = new MySqlConnection(eosConnStr))
                {
                    string select_sql = "SELECT OrdLineShipmentTrackingNo FROM  PartsOrderLines " +
                                     "WHERE ERP_OrderNo = @key and OrdLineShipmentTrackingNo IS NOT NULL AND OrdLineShipmentTrackingNo <> ''";


                    using (MySqlCommand selectCommand = new MySqlCommand(select_sql, eos_con))
                    {

                        selectCommand.Parameters.AddWithValue("@key", CoNum);

                        using (MySqlDataAdapter adapter = new MySqlDataAdapter(selectCommand))
                        {
                            adapter.Fill(tbl);
                            if (tbl.Rows.Count > 0)
                            {
                                EOS_Check = true;
                            }
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                actionResult = -1;
                Console.WriteLine(ex.Message);
            }
            DataTable tbl2 = new DataTable();

            try
            {
                string sqlServerSyteline = ConfigurationManager.ConnectionStrings["Syteline_ConnectionString"].ConnectionString;
                using (SqlConnection sytelinecon = new SqlConnection(sqlServerSyteline))
                {
                    string SELECT_query = "SELECT  Uf_BENN_ShipmentTracking FROM [coitem_mst] WHERE co_num = @conum AND  Uf_BENN_ShipmentTracking IS NOT NULL AND Uf_BENN_ShipmentTracking <> ''";

                    using (SqlCommand selectCommand = new SqlCommand(SELECT_query, sytelinecon))
                    {
                        selectCommand.Parameters.AddWithValue("@conum", CoNum);
                        using (SqlDataAdapter adapter = new SqlDataAdapter(selectCommand))
                        {
                            adapter.Fill(tbl2);
                            if (tbl2.Rows.Count > 0)
                            {
                                Syteline_Check = true;
                            }
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine(ex.Message);
            }

            if (Syteline_Check && EOS_Check)
            {
                return true;
            }
            else
            {
                return false;
            }

        }
        private static void Update_Brain_UPS_Complete(String SalesOrder)
        {
            DataTable tbl = new DataTable();

            try
            {
                string sqlServerBrain = ConfigurationManager.ConnectionStrings["BRAIN_ConnectionString"].ConnectionString;
                using (SqlConnection braincon = new SqlConnection(sqlServerBrain))
                {
                    string SELECT_query = "UPDATE [UPS_Tracking] SET Status = '1' WHERE ERP_OrderNo LIKE '" + SalesOrder + "%'";

                    using (SqlCommand selectCommand = new SqlCommand(SELECT_query, braincon))
                    {

                        using (SqlDataAdapter adapter = new SqlDataAdapter(selectCommand))
                        {
                            adapter.Fill(tbl);
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine(ex.Message);
            }



        }

        private static void Update_Brain_Attempts(String SalesOrder)
        {

            // Get the number of attempts. If the number is less than 5 update the attempt count and the last attempt date.
            DataTable Attempttbl = new DataTable();
            try
            {
                string sqlServerBrain = ConfigurationManager.ConnectionStrings["BRAIN_ConnectionString"].ConnectionString;
                using (SqlConnection braincon = new SqlConnection(sqlServerBrain))
                {
                    //string SELECT_query = "UPDATE [UPS_Tracking] SET Status = '1' WHERE ERP_OrderNo LIKE '"+SalesOrder+"%'";
                    string SELECT_query = "SELECT AttemptCount FROM [UPS_Tracking] WHERE ERP_OrderNo LIKE '" + SalesOrder + "%'";

                    using (SqlCommand selectCommand = new SqlCommand(SELECT_query, braincon))
                    {

                        using (SqlDataAdapter adapter = new SqlDataAdapter(selectCommand))
                        {
                            adapter.Fill(Attempttbl);
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine(ex.Message);
            }
            //If the number of attempts is at 2, update the status to 2 so we don't keep trying to update one that doesn't match and the last attempt date
            // Iterate through the results and update the attempt count and last attempt date if necessary
            foreach (DataRow row in Attempttbl.Rows)
            {                // Check if the value is DBNull before converting
                int attemptCount = row["AttemptCount"] != DBNull.Value ? Convert.ToInt32(row["AttemptCount"]) : 0;
                if (attemptCount < 2)
                {
                    // Increment the attempt count and update the last attempt date
                    attemptCount++;
                    try
                    {
                        string sqlServerBrain = ConfigurationManager.ConnectionStrings["BRAIN_ConnectionString"].ConnectionString;
                        using (SqlConnection braincon = new SqlConnection(sqlServerBrain))
                        {
                            string UPDATE_query = "UPDATE [UPS_Tracking] SET AttemptCount = @attemptCount, LastAttemptDate = @lastAttemptDate WHERE ERP_OrderNo LIKE '" + SalesOrder + "%'";

                            using (SqlCommand updateCommand = new SqlCommand(UPDATE_query, braincon))
                            {
                                updateCommand.Parameters.AddWithValue("@attemptCount", attemptCount);
                                updateCommand.Parameters.AddWithValue("@lastAttemptDate", DateTime.Now);

                                braincon.Open();
                                updateCommand.ExecuteNonQuery();
                            }
                        }
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine(ex.Message);
                    }
                }
                else if (attemptCount == 2)
                {
                    // If the number of attempts is at 2, update the status to 2 and the last attempt date so we don't keep trying to update one that doesn't match.
                    try
                    {
                        string sqlServerBrain = ConfigurationManager.ConnectionStrings["BRAIN_ConnectionString"].ConnectionString;
                        using (SqlConnection braincon = new SqlConnection(sqlServerBrain))
                        {
                            string UPDATE_query = "UPDATE [UPS_Tracking] SET Status = 2, LastAttemptDate = @lastAttemptDate WHERE ERP_OrderNo LIKE '" + SalesOrder + "%'";

                            using (SqlCommand updateCommand = new SqlCommand(UPDATE_query, braincon))
                            {
                                updateCommand.Parameters.AddWithValue("@lastAttemptDate", DateTime.Now);

                                braincon.Open();
                                updateCommand.ExecuteNonQuery();
                            }
                        }
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine(ex.Message);
                    }
                }
            }



        }

        public static DataTable get_EOS_TRACKING(List<string> ListErpOrders)
        {
            DataTable tbl = new DataTable();
            try
            {
                string eosConnStr = ConfigurationManager.ConnectionStrings["EOS_ConnectionString"].ConnectionString;
                using (MySqlConnection EOS_Conn = new MySqlConnection(eosConnStr))
                {
                    // Join the list of ERP_OrderNo into a comma-separated string, each enclosed in single quotes
                    string erpOrderNos = string.Join(",", ListErpOrders.Select(order => $"'{order}'"));
                    string SELECT_query = $"SELECT ERP_OrderNo, OrdLineShipmentTrackingNo AS TrackingNo FROM PartsOrderLines WHERE ERP_OrderNo IN ({erpOrderNos})";

                    using (MySqlCommand selectCommand = new MySqlCommand(SELECT_query, EOS_Conn))
                    {
                        using (MySqlDataAdapter adapter = new MySqlDataAdapter(selectCommand))
                        {
                            adapter.Fill(tbl);
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine(ex.Message);
            }

            return tbl;
        }





        public static DataTable get_Brain_UPS_TRACKING()
        {
            DataTable tbl = new DataTable();

            try
            {
                string sqlServerBrain = ConfigurationManager.ConnectionStrings["BRAIN_ConnectionString"].ConnectionString;
                using (SqlConnection braincon = new SqlConnection(sqlServerBrain))
                {
                    string SELECT_query = "SELECT ERP_OrderNo, UPSTrackingNo, AttemptCount,UPS_Date FROM [UPS_Tracking] WHERE Status = '0' AND (ERP_OrderNo LIKE 'WP%' OR ERP_OrderNo LIKE 'WN%')";

                    using (SqlCommand selectCommand = new SqlCommand(SELECT_query, braincon))
                    {

                        using (SqlDataAdapter adapter = new SqlDataAdapter(selectCommand))
                        {
                            adapter.Fill(tbl);
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine(ex.Message);
            }

            return tbl;
        }

        //public static void UPDATE_EOS_UPS_TRACKING(string CoNum, string UPS_VALUE, DateTime UPS_Date)
        //{
        //    DataTable tbl = new DataTable();

        //    try
        //    {
        //        string eosConnStr = ConfigurationManager.ConnectionStrings["EOS_ConnectionString"].ConnectionString;
        //        using (MySqlConnection eos_con = new MySqlConnection(eosConnStr))
        //        {
        //            string update = "UPDATE PartsOrderLines " +
        //                    "SET OrdLineShipmentTrackingNo = @value, " +
        //                    "OrdLineStatus = 'completed', " +
        //                    "OrdLinePublicStatus = 'Completed', " +
        //                    "OrdLineSttusLastUpd = @date, " +
        //                    "OrdLineActShipDate = @shipDate " +
        //                    "WHERE ERP_OrderNo = @key";


        //            using (MySqlCommand updateCommand = new MySqlCommand(update, eos_con))
        //            {
        //                updateCommand.Parameters.AddWithValue("@value", UPS_VALUE);
        //                updateCommand.Parameters.AddWithValue("@key", CoNum);
        //                updateCommand.Parameters.AddWithValue("@date", DateTime.Now.ToString("MM/dd/yyyy, h:mm:ss tt"));
        //                updateCommand.Parameters.AddWithValue("@shipDate", UPS_Date.ToString("M/d/yyyy"));

        //                using (MySqlDataAdapter adapter = new MySqlDataAdapter(updateCommand))
        //                {
        //                    if (CoNum.Length > 0)
        //                    {
        //                        adapter.Fill(tbl);
        //                    }

        //                }
        //            }
        //        }
        //    }
        //    catch (Exception ex)
        //    {
        //        actionResult = -1;
        //        Console.WriteLine(ex.Message);
        //    }




        //}
        public static void UPDATE_EOS_UPS_TRACKING(string CoNum, string UPS_VALUE, DateTime UPS_Date)
        {
            try
            {
                string eosConnStr = ConfigurationManager.ConnectionStrings["EOS_ConnectionString"].ConnectionString;
                Console.WriteLine($"DEBUG: EOS Connection String = {eosConnStr}"); 
                using (MySqlConnection eos_con = new MySqlConnection(eosConnStr))
                        if (CoNum.Length > 0)
                        {
                            eos_con.Open();  // ✅ Open the connection
                            int rowsAffected = updateCommand.ExecuteNonQuery();  // ✅ Execute the UPDATE
                            Console.WriteLine($"Updated {rowsAffected} row(s) for order {CoNum} with tracking {UPS_VALUE}");  // ✅ Better logging
                {
                    new { Name = "CoNum", Value = CoNum },
                    new { Name = "CoLine", Value = lineItem.CoLine },
                    new { Name = "CoRelease", Value = lineItem.CoRelease },
                changesList.Add(lineChange);
            }

            var batchUpdateJson = new
            {
                IDOName = "SLCoitems",
                Changes = changesList
            };

            string jsonString = JsonConvert.SerializeObject(batchUpdateJson);
            var content = new StringContent(jsonString, Encoding.UTF8, "application/json");

            string token = RequestNewToken(httpClient);

            httpClient.SetBearerToken(token);
            httpClient.DefaultRequestHeaders.Add("X-Infor-MongooseConfig", Config);

            var response = httpClient.PostAsync(new Uri($"{WebString}/update/SLCoitems"), content).Result;

            if (response.IsSuccessStatusCode)
            try
            {
                string sqlServerBrain = ConfigurationManager.ConnectionStrings["BRAIN_ConnectionString"].ConnectionString;
                                    "(@UPS_Date, @UPSTrackingNo, @ERP_OrderNo, @ERP_Dealer_No, @UPSVoid, @RGA);";

                    using (SqlCommand insertCommand = new SqlCommand(insert, braincon))
                    {
                        insertCommand.Parameters.AddWithValue("@UPS_Date", UPS_Date);
                        insertCommand.Parameters.AddWithValue("@UPSTrackingNo", UPSTrackingNo);
                        insertCommand.Parameters.AddWithValue("@ERP_OrderNo", ERP_OrderNo);
                        insertCommand.Parameters.AddWithValue("@ERP_Dealer_No", ERP_Dealer_No);
                        insertCommand.Parameters.AddWithValue("@UPSVoid", UPSVoid);
                        insertCommand.Parameters.AddWithValue("@RGA", RGA);

                        using (SqlDataAdapter adapter = new SqlDataAdapter(insertCommand))
                        {
                            adapter.Fill(tbl);
                        }
                    }
            }
        }

        public static void UploadCustAddr()
        {
            string query = @"
                -- Get the customer addressess
SELECT 
    ca.[cust_num],
    ca.[cust_seq],
    ca.[name],
    CASE 
        WHEN ca.cust_seq = (SELECT [customer_mst].default_ship_to 
                            FROM [customer_mst] 
                            WHERE [customer_mst].cust_num = ca.cust_num  
                              AND [customer_mst].cust_seq = 0) THEN 1
        ELSE 0
    END AS [is_default_ship_to]
FROM 
    [custaddr_mst] ca;";

            try
            {
                // Execute the SQL query and fill the DataTable
                {
                    sqlConnection.Open();
                    using (SqlCommand command = new SqlCommand(query, sqlConnection))
                    {
                        using (SqlDataAdapter adapter = new SqlDataAdapter(command))
                        {
                            adapter.Fill(dataTable);
                        }
                    }
                }

                using (MySqlConnection mySqlConnection = new MySqlConnection(EOS_WarrantyPartsConnStr))
                {
                    mySqlConnection.Open();

                    {
                        clearCommand.ExecuteNonQuery();
                            MySqlHelper.EscapeString(row["cust_num"].ToString()),
                            MySqlHelper.EscapeString(row["cust_seq"].ToString()),
        }

    }
6.POLARISSTAGE.COM;Database=CSISTG;User ID=svccsimarine;Password=CNKmoFxEsXs0D9egZQXH;Encrypt=True;TrustServerCertificate=True;"; // Adjust Encrypt/TrustServerCertificate as needed
        private const string MySqlConnectionString = "Server=ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com;Port=3306;Database=warrantyparts_test;Uid=awsmaster;Pwd=VWvHG9vfG23g7gD;AllowLoadLocalInfile=True;AllowUserVariables=true;";
        private const string MySqlTargetTable = "BoatOptions25_test"; // Specify your target MySQL table name
    LEFT(coi.Uf_BENN_BoatWebOrderNumber, 30) AS [WebOrderNo],
    LEFT(im.Uf_BENN_Series, 5) AS [Series],
    coi.qty_invoiced AS [QuantitySold],
    LEFT(co.type, 1) AS [Orig_Ord_Type],
    ah.apply_to_inv_num AS [ApplyToNo]
FROM [CSISTG].[dbo].[coitem_mst] coi
LEFT JOIN [CSISTG].[dbo].[inv_item_mst] iim ON coi.co_num = iim.co_num AND coi.co_line = iim.co_line AND coi.co_release = iim.co_release AND coi.site_ref = iim.site_ref
LEFT JOIN [CSISTG].[dbo].[arinv_mst] ah ON iim.inv_num = ah.inv_num AND iim.site_ref = ah.site_ref
LEFT JOIN [CSISTG].[dbo].[co_mst] co ON coi.co_num = co.co_num AND coi.site_ref = co.site_ref
LEFT JOIN [CSISTG].[dbo].[item_mst] im ON coi.item = im.item AND coi.site_ref = im.site_ref
LEFT JOIN [CSISTG].[dbo].[prodcode_mst] pcm ON im.Uf_BENN_MaterialCostType = pcm.product_code AND im.site_ref = pcm.site_ref
LEFT JOIN [CSISTG].[dbo].[serial_mst] ser ON coi.co_num = ser.ref_num AND coi.co_line = ser.ref_line AND coi.co_release = ser.ref_release AND coi.item = ser.item AND coi.site_ref = ser.site_ref AND ser.ref_type = 'O'
--WHERE
    [ERP_OrderNo],
    [LineNo];
";

        public void ExportFromSqlServerAndImportToMySql()
        {
            Console.WriteLine("Starting Boat Options Data Import Process...");
            long rowsExported = ExportSqlServerToCsv();

            if (rowsExported > 0)
            {
                LoadCsvToMySql();
            }
            else
            {
                Console.WriteLine("No rows were exported from SQL Server. MySQL import will be skipped.");
            }
            Console.WriteLine("\nBoat Options Data export and import process finished.");
        }

        private long ExportSqlServerToCsv()
        {
            long rowsExported = 0;
            Console.WriteLine("Starting SQL Server data export to CSV...");
            try
            {
                // Using System.Data.SqlClient as it's likely the standard for .NET Framework 4.7.2 projects
                using (System.Data.SqlClient.SqlConnection sqlConn = new System.Data.SqlClient.SqlConnection(SqlServerConnectionString))
                {
                    sqlConn.Open();
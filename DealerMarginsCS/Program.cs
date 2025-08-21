using System;
using System.Collections.Generic;
using System.Data;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using CsvHelper;
using CsvHelper.Configuration;
using Newtonsoft.Json;
using Newtonsoft.Json.Serialization;

public static class Config
{
    public const string ClientId = "QA2FNBZCKUAUH7QB_TRN~H80EoFmxpr1RMXqY4TeW-u2c5vCw1sGRIr18qppHoPY";
    public const string ClientSecret = "rmmqE4W5K3ANN-hid34kbC7r78mYHGIs9Wg6fzCdLImCH33JCt6L3x8ThLzBbvwS49f6PunHG8eMM19z_u1diw";
    public const string TokenEndpoint = "https://mingle-sso.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/as/token.oauth2";
    public const string ServiceAccountAccessKey = "QA2FNBZCKUAUH7QB_TRN#OXBbg16XPKc5tDaOb_v2MzynsS2bnjFtvTBiOuUJhWXrO62s7arC7juObUL2iqYkWVWsCPV26XzB0VDXAvq1mw";
    public const string ServiceAccountSecretKey = "Xp6Iam1HR4So1rs4KfbKOZmWOf1oFEWQkC1m55TvbBS7vql-HpSMd4J37ioB3tm-B1bpSo5apjwxxdxAw1WJsg";
    public const string DealerMarginEndpoint = "https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/CPQEQ/RuntimeApi/EnterpriseQuoting/Entities/C_GD_DealerMargin";

    public const int RequestTimeoutSeconds = 60;
    public const int ItemsPerPage = 1000;
    public const int MaxWorkers = 8;
    public const int MaxRetries = 3;
    public const int RetryDelaySeconds = 1;
}

public class TokenManager
{
    private string? _token;
    private DateTime _expiresAt = DateTime.MinValue;
    private readonly SemaphoreSlim _lock = new(1, 1);
    private static readonly HttpClient HttpClient = new(new HttpClientHandler
    {
        ServerCertificateCustomValidationCallback = (message, cert, chain, errors) => true
    });

    public async Task<string?> GetTokenAsync()
    {
        await _lock.WaitAsync();
        try
        {
            if (_token != null && DateTime.UtcNow < _expiresAt.AddMinutes(-5))
            {
                return _token;
            }
            return await RefreshTokenAsync();
        }
        finally
        {
            _lock.Release();
        }
    }

    private async Task<string?> RefreshTokenAsync()
    {
        Console.WriteLine("🔄 Refreshing access token...");
        var payload = new Dictionary<string, string>
        {
            { "grant_type", "password" },
            { "client_id", Config.ClientId },
            { "client_secret", Config.ClientSecret },
            { "username", Config.ServiceAccountAccessKey },
            { "password", Config.ServiceAccountSecretKey }
        };

        try
        {
            using var request = new HttpRequestMessage(HttpMethod.Post, Config.TokenEndpoint)
            {
                Content = new FormUrlEncodedContent(payload)
            };

            var response = await HttpClient.SendAsync(request);
            response.EnsureSuccessStatusCode();

            var content = await response.Content.ReadAsStringAsync();
            var tokenData = JsonConvert.DeserializeObject<TokenResponse>(content);

            if (tokenData?.AccessToken == null)
            {
                Console.WriteLine("❌ Error: Access token not found in response.");
                return null;
            }

            _token = tokenData.AccessToken;
            _expiresAt = DateTime.UtcNow.AddSeconds(tokenData.ExpiresIn);
            Console.WriteLine("✅ Token refreshed successfully");
            return _token;
        }
        catch (Exception e)
        {
            Console.WriteLine($"❌ Error refreshing token: {e.Message}");
            return null;
        }
    }
}

public class ApiService
{
    private readonly TokenManager _tokenManager;
    private static readonly HttpClient HttpClient = new(new HttpClientHandler
    {
        ServerCertificateCustomValidationCallback = (message, cert, chain, errors) => true
    })
    {
        Timeout = TimeSpan.FromSeconds(Config.RequestTimeoutSeconds)
    };

    public ApiService(TokenManager tokenManager)
    {
        _tokenManager = tokenManager;
    }

    public async Task<List<MarginData>?> GetAllDealerMarginsAsync(List<string> seriesFilters)
    {
        var filterQuery = "";
        if (seriesFilters.Any())
        {
            var uniqueSeries = seriesFilters.Distinct().ToList();
            Console.WriteLine($"🔍 Filtering for series: {string.Join(", ", uniqueSeries)}");
            var filterConditions = uniqueSeries.Select(s => $"C_Series eq '{s}'");
            filterQuery = "&$filter=" + string.Join(" or ", filterConditions);
        }

        var metadata = await GetDownloadMetadataAsync(filterQuery);
        if (metadata == null) return null;

        var (totalItems, totalPages) = metadata.Value;
        if (totalItems == 0) return new List<MarginData>();

        var allItems = new List<MarginData>();
        var progress = 0;

        var parallelOptions = new ParallelOptions { MaxDegreeOfParallelism = Config.MaxWorkers };

        await Parallel.ForEachAsync(Enumerable.Range(1, totalPages), parallelOptions, async (page, token) =>
        {
            var items = await FetchPageWithRetryAsync(page, Config.ItemsPerPage, filterQuery);
            if (items != null)
            {
                lock (allItems)
                {
                    allItems.AddRange(items);
                }
                var newProgress = Interlocked.Add(ref progress, items.Count);
                Console.Write($"\rDownloading Margins... {newProgress:N0} / {totalItems:N0} records");
            }
        });

        Console.WriteLine($"\n✅ Successfully downloaded {allItems.Count:N0} records from {totalPages} pages");
        return allItems;
    }

    private async Task<(int totalItems, int totalPages)?> GetDownloadMetadataAsync(string filterQuery = "")
    {
        var token = await _tokenManager.GetTokenAsync();
        if (token == null) return null;

        var url = $"{Config.DealerMarginEndpoint}?top=1{filterQuery}";
        try
        {
            using var request = new HttpRequestMessage(HttpMethod.Get, url);
            request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);

            var response = await HttpClient.SendAsync(request);
            response.EnsureSuccessStatusCode();

            var content = await response.Content.ReadAsStringAsync();
            var data = JsonConvert.DeserializeObject<ApiResponse>(content);

            if (data?.TotalItems == null)
            {
                Console.WriteLine("❌ Could not find 'totalItems' in response.");
                return null;
            }

            var totalItems = data.TotalItems.Value;
            var totalPages = (totalItems + Config.ItemsPerPage - 1) / Config.ItemsPerPage;
            Console.WriteLine($"📊 Found {totalItems:N0} total items across {totalPages} pages.");
            return (totalItems, totalPages);
        }
        catch (Exception e)
        {
            Console.WriteLine($"❌ Error fetching total pages: {e.Message}");
            return null;
        }
    }

    private async Task<List<MarginData>?> FetchPageWithRetryAsync(int page, int itemsPerPage, string filterQuery = "")
    {
        var skipCount = (page - 1) * itemsPerPage;
        var url = $"{Config.DealerMarginEndpoint}?top={itemsPerPage}&skip={skipCount}{filterQuery}";

        for (var attempt = 0; attempt < Config.MaxRetries; attempt++)
        {
            try
            {
                var token = await _tokenManager.GetTokenAsync();
                if (token == null) return null;

                using var request = new HttpRequestMessage(HttpMethod.Get, url);
                request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);

                var response = await HttpClient.SendAsync(request);
                response.EnsureSuccessStatusCode();

                var content = await response.Content.ReadAsStringAsync();
                return JsonConvert.DeserializeObject<ApiResponse>(content)?.Items;
            }
            catch (Exception e)
            {
                if (attempt < Config.MaxRetries - 1)
                {
                    Console.WriteLine($"⚠️  Page {page} attempt {attempt + 1} failed: {e.Message}. Retrying...");
                    await Task.Delay(Config.RetryDelaySeconds * 1000 * (attempt + 1));
                }
                else
                {
                    Console.WriteLine($"❌ Page {page} failed after {Config.MaxRetries} attempts: {e.Message}");
                    return null;
                }
            }
        }
        return null;
    }
}

public class PivotService
{
    public DataTable PivotData(List<MarginData> items)
    {
        var pivotTable = new DataTable();
        pivotTable.Columns.Add("DealerID", typeof(int));
        pivotTable.Columns.Add("Dealership", typeof(string));

        var groupedByDealer = items.GroupBy(i => new { i.DealerId, i.DealerName });

        foreach (var dealerGroup in groupedByDealer)
        {
            var row = pivotTable.NewRow();
            row["DealerID"] = int.TryParse(dealerGroup.Key.DealerId, out var dealerId) ? dealerId : 0;
            row["Dealership"] = dealerGroup.Key.DealerName;

            foreach (var item in dealerGroup)
            {
                var series = item.Series?.Replace(" ", "_");
                if (string.IsNullOrEmpty(series)) continue;

                var columnMappings = new Dictionary<string, double?>
                {
                    { $"{series}_BASE_BOAT", item.BaseBoatMarginPercent },
                    { $"{series}_ENGINE", item.EngineMarginPercent },
                    { $"{series}_OPTIONS", item.OptionsMarginPercent },
                    { $"{series}_FREIGHT", item.FreightMarginDollars },
                    { $"{series}_PREP", item.PrepMarginDollars },
                    { $"{series}_VOL_DISC", item.VolumeMarginPercent }
                };

                foreach (var mapping in columnMappings)
                {
                    if (!pivotTable.Columns.Contains(mapping.Key))
                    {
                        pivotTable.Columns.Add(mapping.Key, typeof(decimal));
                    }
                    row[mapping.Key] = Convert.ToDecimal(mapping.Value ?? 0.0);
                }
            }
            pivotTable.Rows.Add(row);
        }

        // Define the final column order
        var finalColumns = new List<string>
        {
            "DealerID", "Dealership",
            "Q_BASE_BOAT", "Q_ENGINE", "Q_OPTIONS", "Q_FREIGHT", "Q_PREP", "Q_VOL_DISC",
            "QX_BASE_BOAT", "QX_ENGINE", "QX_OPTIONS", "QX_FREIGHT", "QX_PREP", "QX_VOL_DISC",
            "QXS_BASE_BOAT", "QXS_ENGINE", "QXS_OPTIONS", "QXS_FREIGHT", "QXS_PREP", "QXS_VOL_DISC",
            "R_BASE_BOAT", "R_ENGINE", "R_OPTIONS", "R_FREIGHT", "R_PREP", "R_VOL_DISC",
            "RX_BASE_BOAT", "RX_ENGINE", "RX_OPTIONS", "RX_FREIGHT", "RX_PREP", "RX_VOL_DISC",
            "RT_BASE_BOAT", "RT_ENGINE", "RT_OPTIONS", "RT_FREIGHT", "RT_PREP", "RT_VOL_DISC",
            "G_BASE_BOAT", "G_ENGINE", "G_OPTIONS", "G_FREIGHT", "G_PREP", "G_VOL_DISC",
            "S_BASE_BOAT", "S_ENGINE", "S_OPTIONS", "S_FREIGHT", "S_PREP", "S_VOL_DISC",
            "SX_BASE_BOAT", "SX_ENGINE", "SX_OPTIONS", "SX_FREIGHT", "SX_PREP", "SX_VOL_DISC",
            "L_BASE_BOAT", "L_ENGINE", "L_OPTIONS", "L_FREIGHT", "L_PREP", "L_VOL_DISC",
            "LX_BASE_BOAT", "LX_ENGINE", "LX_OPTIONS", "LX_FREIGHT", "LX_PREP", "LX_VOL_DISC",
            "LT_BASE_BOAT", "LT_ENGINE", "LT_OPTIONS", "LT_FREIGHT", "LT_PREP", "LT_VOL_DISC",
            "S_23_BASE_BOAT", "S_23_ENGINE", "S_23_OPTIONS", "S_23_FREIGHT", "S_23_PREP", "S_23_VOL_DISC",
            "SV_23_BASE_BOAT", "SV_23_ENGINE", "SV_23_OPTIONS", "SV_23_FREIGHT", "SV_23_PREP", "SV_23_VOL_DISC",
            "M_BASE_BOAT", "M_ENGINE", "M_OPTIONS", "M_FREIGHT", "M_PREP", "M_VOL_DISC"
        };

        var finalTable = new DataTable();
        foreach (var colName in finalColumns)
        {
            finalTable.Columns.Add(colName, pivotTable.Columns.Contains(colName) ? pivotTable.Columns[colName].DataType : typeof(decimal));
        }

        foreach (DataRow oldRow in pivotTable.Rows)
        {
            var newRow = finalTable.NewRow();
            foreach (var colName in finalColumns)
            {
                if (pivotTable.Columns.Contains(colName))
                {
                    newRow[colName] = oldRow[colName];
                }
                else
                {
                    newRow[colName] = 0.0m;
                }
            }
            finalTable.Rows.Add(newRow);
        }

        return finalTable;
    }
}

public class CsvWriterService
{
    public async Task WriteToCsvAsync(DataTable dataTable, string csvPath)
    {
        await using var writer = new StreamWriter(csvPath, false, Encoding.UTF8);
        await using var csv = new CsvWriter(writer, CultureInfo.InvariantCulture);
        
        foreach (DataColumn column in dataTable.Columns)
        {
            csv.WriteField(column.ColumnName);
        }
        await csv.NextRecordAsync();

        foreach (DataRow row in dataTable.Rows)
        {
            for (var i = 0; i < dataTable.Columns.Count; i++)
            {
                csv.WriteField(row[i]);
            }
            await csv.NextRecordAsync();
        }
        Console.WriteLine($"✅ Successfully created dealer quotes CSV: {csvPath}");
    }
}

public static class Program
{
    public static async Task Main(string[] args)
    {
        Console.WriteLine("🚀 Starting dealer margins downloader...");
        var startTime = DateTime.UtcNow;

        try
        {
            var seriesToDownload = new List<string> { "Q", "QX", "QXS", "R", "RX", "RT", "G", "S", "SX", "L", "LX", "LT", "S 23", "SV 23", "M" };
            var csvOutputPath = "dealer_quotes.csv";

            if (File.Exists(csvOutputPath)) File.Delete(csvOutputPath);

            var tokenManager = new TokenManager();
            var apiService = new ApiService(tokenManager);
            var pivotService = new PivotService();
            var csvWriterService = new CsvWriterService();

            var allItems = new List<MarginData>();
            foreach (var series in seriesToDownload)
            {
                Console.WriteLine("\n--- Processing series: '" + series + "' ---");
                var items = await apiService.GetAllDealerMarginsAsync(new List<string> { series });
                if (items != null)
                {
                    allItems.AddRange(items);
                }
                else
                {
                    Console.WriteLine($"❌ Download failed for series '{series}'.");
                }
            }

            if (allItems.Any())
            {
                var pivotData = pivotService.PivotData(allItems);
                await csvWriterService.WriteToCsvAsync(pivotData, csvOutputPath);
                Console.WriteLine("\n🎉 All operations completed successfully!");
            }
            else
            {
                Console.WriteLine("\n⚠️ No data downloaded or processed.");
            }
        }
        catch (Exception e)
        {
            Console.WriteLine($"\n💥 Unexpected error: {e.Message}");
        }
        finally
        {
            var totalTime = DateTime.UtcNow - startTime;
            Console.WriteLine($"⏱️  Total time: {totalTime.TotalSeconds:F1} seconds");
        }
    }
}

// Data models
public class TokenResponse
{
    [JsonProperty("access_token")]
    public string? AccessToken { get; set; }

    [JsonProperty("expires_in")]
    public int ExpiresIn { get; set; }
}

public class ApiResponse
{
    [JsonProperty("items")]
    public List<MarginData>? Items { get; set; }

    [JsonProperty("totalItems")]
    public int? TotalItems { get; set; }
}

public class MarginData
{
    [JsonProperty("C_DealerName")]
    public string? DealerName { get; set; }

    [JsonProperty("C_DealerId")]
    public string? DealerId { get; set; }

    [JsonProperty("C_Series")]
    public string? Series { get; set; }

    [JsonProperty("C_Volume")]
    public double? VolumeMarginPercent { get; set; }

    [JsonProperty("C_BaseBoat")]
    public double? BaseBoatMarginPercent { get; set; }

    [JsonProperty("C_Engine")]
    public double? EngineMarginPercent { get; set; }

    [JsonProperty("C_Options")]
    public double? OptionsMarginPercent { get; set; }

    [JsonProperty("C_Freight")]
    public double? FreightMarginDollars { get; set; }

    [JsonProperty("C_Prep")]
    public double? PrepMarginDollars { get; set; }
}

using System;
using System.Collections.Generic;
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

    public async Task<(int totalItems, int totalPages)?> GetDownloadMetadataAsync(string filterQuery = "")
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

            if (data == null || data.TotalItems == null)
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

    public async Task<List<MarginData>?> FetchPageWithRetryAsync(int page, int itemsPerPage, string filterQuery = "")
    {
        var skipCount = (page - 1) * itemsPerPage;
        var url = $"{Config.DealerMarginEndpoint}?top={itemsPerPage}&skip={skipCount}{filterQuery}";

        for (var attempt = 0; attempt < Config.MaxRetries; attempt++)
        {
            try
            {
                var token = await _tokenManager.GetTokenAsync();
                if (token == null)
                {
                    Console.WriteLine($"❌ No token available for page {page}");
                    return null;
                }

                using var request = new HttpRequestMessage(HttpMethod.Get, url);
                request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);

                var response = await HttpClient.SendAsync(request);
                response.EnsureSuccessStatusCode();

                var content = await response.Content.ReadAsStringAsync();
                var data = JsonConvert.DeserializeObject<ApiResponse>(content);
                return data?.Items;
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

public class CsvWriterService
{
    public async Task WriteToCsvAsync(List<MarginData> items, string csvPath)
    {
        var fileExists = File.Exists(csvPath);
        var config = new CsvConfiguration(CultureInfo.InvariantCulture)
        {
            HasHeaderRecord = !fileExists,
        };

        await using var writer = new StreamWriter(csvPath, append: true, Encoding.UTF8);
        await using var csv = new CsvWriter(writer, config);
        
        // Manually map to the desired column names and order
        csv.Context.RegisterClassMap<MarginDataMap>();

        await csv.WriteRecordsAsync(items);
        Console.WriteLine($"✅ Successfully appended {items.Count:N0} records to: {csvPath}");
    }
}

public sealed class MarginDataMap : ClassMap<MarginData>
{
    public MarginDataMap()
    {
        Map(m => m.DealerName).Name("DealerName");
        Map(m => m.DealerId).Name("DealerId");
        Map(m => m.Series).Name("Series");
        Map(m => m.VolumeMarginPercent).Name("Volume_Margin_Percent");
        Map(m => m.BaseBoatMarginPercent).Name("BaseBoat_Margin_Percent");
        Map(m => m.EngineMarginPercent).Name("Engine_Margin_Percent");
        Map(m => m.OptionsMarginPercent).Name("Options_Margin_Percent");
        Map(m => m.FreightMarginDollars).Name("Freight_Margin_Dollars");
        Map(m => m.PrepMarginDollars).Name("Prep_Margin_Dollars");
        Map(m => m.IsEnabled).Name("IsEnabled");
        Map(m => m.DealerGuid).Name("Dealer_GUID");
    }
}


public class DealerMarginsOrchestrator
{
    private readonly ApiService _apiService;
    private readonly CsvWriterService _csvWriterService;

    public DealerMarginsOrchestrator(ApiService apiService, CsvWriterService csvWriterService)
    {
        _apiService = apiService;
        _csvWriterService = csvWriterService;
    }

    public async Task<bool> GetAllDealerMarginsOptimizedAsync(string csvPath, List<string>? seriesFilters = null)
    {
        Console.WriteLine("🚀 Starting optimized dealer margins download...");

        var filterQuery = "";
        if (seriesFilters != null && seriesFilters.Any())
        {
            var uniqueSeries = seriesFilters.Distinct().ToList();
            Console.WriteLine($"🔍 Filtering for series: {string.Join(", ", uniqueSeries)}");
            var filterConditions = uniqueSeries.Select(s => $"C_Series eq '{s}'");
            filterQuery = "&$filter=" + string.Join(" or ", filterConditions);
        }

        var metadata = await _apiService.GetDownloadMetadataAsync(filterQuery);
        if (metadata == null)
        {
            Console.WriteLine("❌ Could not retrieve download metadata. Aborting.");
            return false;
        }

        var (totalItems, totalPages) = metadata.Value;

        if (totalItems == 0)
        {
            Console.WriteLine("\n✅ No items found matching the filter criteria. Nothing to download.");
            return true;
        }

        var allItems = new List<MarginData>();
        var progress = 0;

        var parallelOptions = new ParallelOptions { MaxDegreeOfParallelism = Config.MaxWorkers };
        
        await Parallel.ForEachAsync(Enumerable.Range(1, totalPages), parallelOptions, async (page, token) =>
        {
            var items = await _apiService.FetchPageWithRetryAsync(page, Config.ItemsPerPage, filterQuery);
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

        if (!allItems.Any())
        {
            Console.WriteLine("❌ No data was successfully downloaded");
            return false;
        }

        await _csvWriterService.WriteToCsvAsync(allItems, csvPath);
        return true;
    }
}

public static class Program
{
    public static async Task Main(string[] args)
    {
        Console.WriteLine("🚀 Starting optimized dealer margins downloader...");
        var startTime = DateTime.UtcNow;

        try
        {
            var seriesToDownload = new List<string> { "Q", "R", "S", "L", "M" };
            var csvOutputPath = "margins_optimized.csv";

            if (File.Exists(csvOutputPath))
            {
                File.Delete(csvOutputPath);
                Console.WriteLine($"🧹 Removed old CSV file: {csvOutputPath}");
            }

            var tokenManager = new TokenManager();
            var apiService = new ApiService(tokenManager);
            var csvWriterService = new CsvWriterService();
            var orchestrator = new DealerMarginsOrchestrator(apiService, csvWriterService);

            var allSeriesSuccessful = true;
            for (var i = 0; i < seriesToDownload.Count; i++)
            {
                var series = seriesToDownload[i];
                Console.WriteLine($"\n--- Processing series {i + 1}/{seriesToDownload.Count}: '{series}' ---");

                var downloadSuccess = await orchestrator.GetAllDealerMarginsOptimizedAsync(csvOutputPath, new List<string> { series });

                if (downloadSuccess)
                {
                    Console.WriteLine($"✅ Download for series '{series}' completed.");
                }
                else
                {
                    Console.WriteLine($"❌ Download failed for series '{series}'.");
                    allSeriesSuccessful = false;
                }
            }

            if (allSeriesSuccessful)
            {
                Console.WriteLine("\n🎉 All operations completed successfully!");
            }
            else
            {
                Console.WriteLine("\n⚠️  Some operations failed. Please review the logs.");
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

    [JsonProperty("C_Enabled")]
    public bool IsEnabled { get; set; }

    [JsonProperty("C_Dealer")]
    public string? DealerGuid { get; set; }
}

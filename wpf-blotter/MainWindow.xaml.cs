using System;
using System.Collections.ObjectModel;
using System.Net.Http;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Threading;
using System.Windows.Input;
using System.Linq;

namespace wpf_blotter
{
    public class PositionRow
    {
        public string InstrumentId { get; set; }
        public string Product { get; set; }
        public string NotionalFormatted { get; set; }
        public string RiskFormatted { get; set; }
        public string MarketFormatted { get; set; }
    }

    public class PortfolioRisk
    {
        [JsonPropertyName("position_count")]
        public int PositionCount { get; set; }
        
        [JsonPropertyName("total_cs01")]
        public double TotalCs01 { get; set; }
        
        [JsonPropertyName("total_dv01")]
        public double TotalDv01 { get; set; }
    }

    public class RiskData
    {
        [JsonPropertyName("instrument_id")]
        public string InstrumentId { get; set; }
        
        [JsonPropertyName("product")]
        public string Product { get; set; }
        
        [JsonPropertyName("dirty_price")]
        public double? DirtyPrice { get; set; }
        
        [JsonPropertyName("dv01")]
        public double? Dv01 { get; set; }
        
        [JsonPropertyName("upfront")]
        public double? Upfront { get; set; }
        
        [JsonPropertyName("cs01")]
        public double? Cs01 { get; set; }
        
        [JsonPropertyName("notional")]
        public double Notional { get; set; }
        
        [JsonPropertyName("spread_bps")]
        public double? SpreadBps { get; set; }
        
        [JsonPropertyName("rate")]
        public double? Rate { get; set; }
    }

    public partial class MainWindow : Window
    {
        private static readonly HttpClient _client = new HttpClient() { Timeout = TimeSpan.FromSeconds(60) };
        private const string API = "http://localhost:8000";
        private ObservableCollection<PositionRow> _positions = new ObservableCollection<PositionRow>();
        
        private static readonly string[] SampleIds = {
            "BOND-00001", "BOND-00003", "BOND-00005", "BOND-00007", "BOND-00009",
            "CDS-00000", "CDS-00002", "CDS-00004", "CDS-00006", "CDS-00008"
        };
        private bool _isLookupMode = false;

        public MainWindow()
        {
            InitializeComponent();
            PositionsGrid.ItemsSource = _positions;
            StartRefresh();
        }
            private async void LookupButton_Click(object sender, RoutedEventArgs e)
{
    await LookupInstrument();
}

private async void SearchBox_KeyDown(object sender, KeyEventArgs e)
{
    if (e.Key == Key.Enter)
        await LookupInstrument();
}

private async Task LookupInstrument()
{
    string id = SearchBox.Text.Trim().ToUpper();
    if (string.IsNullOrEmpty(id)) return;

    _isLookupMode = true;

    try
    {
        string json = await _client.GetStringAsync($"{API}/risk/{id}");
        var risk = JsonSerializer.Deserialize<RiskData>(json);

        _positions.Clear();
        _positions.Add(new PositionRow
        {
            InstrumentId = risk.InstrumentId,
            Product = risk.Product,
            NotionalFormatted = $"${risk.Notional / 1000000:F1}M",
            RiskFormatted = risk.Product == "CDS" ? $"{risk.Cs01:F2}" : $"{risk.Dv01:F4}",
            MarketFormatted = risk.Product == "CDS" ? $"{risk.SpreadBps:F1} bps" : $"{risk.Rate * 100:F2}%"
        });

        Status.Text = $"Found: {id}";
    }
    catch (Exception ex)
    {
        Status.Text = ex.Message;
        _isLookupMode = false;
    }
}
private void ClearButton_Click(object sender, RoutedEventArgs e)
{
    _isLookupMode = false;
    SearchBox.Text = "";
    Status.Text = "Live";
}

        private void StartRefresh()
        {
            var timer = new DispatcherTimer();
            timer.Interval = TimeSpan.FromSeconds(10);
            timer.Tick += async (s, e) => await RefreshData();
            timer.Start();
            _ = RefreshData();
            _ = RefreshPortfolio();
        }

private async Task RefreshData()
{
    if (_isLookupMode) return;
    try
    {
        foreach (var id in SampleIds)
        {
            try
            {
                string riskJson = await _client.GetStringAsync($"{API}/risk/{id}");
                var risk = JsonSerializer.Deserialize<RiskData>(riskJson);
                var existing = _positions.FirstOrDefault(p => p.InstrumentId == id);
                if (existing != null) _positions.Remove(existing);
                _positions.Add(new PositionRow
                {
                    InstrumentId = risk.InstrumentId,
                    Product = risk.Product,
                    NotionalFormatted = $"${risk.Notional/1000000:F1}M",
                    RiskFormatted = risk.Product == "CDS" ? $"{risk.Cs01:F2}" : $"{risk.Dv01:F4}",
                    MarketFormatted = risk.Product == "CDS" ? $"{risk.SpreadBps:F1} bps" : $"{risk.Rate*100:F2}%"
                });
            }
            catch { }
        }
        Status.Text = "Live";
    }
    catch (Exception ex)
    {
        Status.Text = ex.Message;
    }
}
private async Task RefreshPortfolio()
{
    while (true)
    {
        try
        {
            string portfolioJson = await _client.GetStringAsync($"{API}/risk/portfolio");
            var portfolio = JsonSerializer.Deserialize<PortfolioRisk>(portfolioJson);
            PositionCount.Text = portfolio.PositionCount.ToString("N0");
            TotalCs01.Text = $"${portfolio.TotalCs01/1000000:F1}M";
            TotalDv01.Text = $"${portfolio.TotalDv01:N0}";
        }
        catch { }
        await Task.Delay(60000);
    }
}
  }
}
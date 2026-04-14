using System;
using System.Net.Http;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading.Tasks;

namespace CreditRiskClient
{
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

    class Program
        {
            private static readonly HttpClient client = new HttpClient();
            private const string API = "http://localhost:8000";
            static async Task Main(string[] args)
        {
            Console.WriteLine("Credit Risk Engine — C# Client");
            Console.WriteLine("==============================\n");

            try
            {
                string portfolioJson = await client.GetStringAsync($"{API}/risk/portfolio");
                PortfolioRisk portfolio = JsonSerializer.Deserialize<PortfolioRisk>(portfolioJson);
                
                Console.WriteLine("Portfolio Risk Summary");
                Console.WriteLine($"Positions:  {portfolio.PositionCount:N0}");
                Console.WriteLine($"Total CS01: {portfolio.TotalCs01:C0}");
                Console.WriteLine($"Total DV01: {portfolio.TotalDv01:N0}");
                Console.WriteLine();

                string riskJson = await client.GetStringAsync($"{API}/risk/BOND-00001");
                RiskData risk = JsonSerializer.Deserialize<RiskData>(riskJson);
                
                Console.WriteLine("Single Position — BOND-00001");
                Console.WriteLine($"Product:     {risk.Product}");
                Console.WriteLine($"Notional:    {risk.Notional:C0}");
                Console.WriteLine($"Dirty Price: {risk.DirtyPrice:F4}");
                Console.WriteLine($"DV01:        {risk.Dv01:F4}");
                Console.WriteLine();

                string cdsJson = await client.GetStringAsync($"{API}/risk/CDS-00000");
                RiskData cds = JsonSerializer.Deserialize<RiskData>(cdsJson);
                
                Console.WriteLine("Single Position — CDS-00000");
                Console.WriteLine($"Product:     {cds.Product}");
                Console.WriteLine($"Notional:    {cds.Notional:C0}");
                Console.WriteLine($"Upfront:     {cds.Upfront:C0}");
                Console.WriteLine($"CS01:        {cds.Cs01:F4}");
                Console.WriteLine();

                }
            catch (Exception ex)
            {
                Console.WriteLine($"Error: {ex.Message}");
                Console.WriteLine("Is the API running? Start with: docker-compose up");
            }
        }
    }
}
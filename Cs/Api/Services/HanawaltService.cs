using Microsoft.Data.Sqlite;
using MySqlConnector;
using Api.Models;
using System.Net.Http.Json;
using System.Text.Json;
using System.Text.Json.Serialization;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using System.Linq;
using System.IO;

namespace Api.Services
{
    public class HanawaltService
    {
        private readonly HttpClient _httpClient;
        private readonly string _sqliteConn;
        private readonly string _mysqlConn = "Server=sql.crystallography.net;Port=3306;Database=cod;Uid=cod_reader;Pwd=;";

        public HanawaltService()
        {
            _httpClient = new HttpClient();
            string dbPath = Path.Combine(AppContext.BaseDirectory, "HanawaltIndex.db");
            _sqliteConn = $"Data Source={dbPath}";
        }

        public async Task<List<CodResult>> PipelineSearchAsync(List<double> dValues, double[] xExp, double[] yExp, string anode)
        {
            var finalResults = new List<CodResult>();
            if (dValues == null || dValues.Count == 0) return finalResults;

            
            var rawIds = await GetRawIdsFromSqlite(dValues);
            if (rawIds.Count == 0) return finalResults;

            var pythonPayload = new 
            {
                ids = rawIds,
                x = xExp,
                y = yExp,
                anode = anode
            };

            var pyResponse = await _httpClient.PostAsJsonAsync("http://localhost:8000/api/math/pipeline-score", pythonPayload);
            if (!pyResponse.IsSuccessStatusCode) 
            {
                throw new Exception($"El motor Python falló: {pyResponse.ReasonPhrase}");
            }

            var pyResult = await pyResponse.Content.ReadFromJsonAsync<ScoredResponse>();
            if (pyResult == null || pyResult.Candidates.Count == 0) return finalResults;

            finalResults = await EnrichWithMetadata(pyResult.Candidates);

            return finalResults;
        }


        private async Task<List<int>> GetRawIdsFromSqlite(List<double> dValues)
        {
            var ids = new List<int>();
            double d1 = dValues[0];
            double d2 = dValues.Count > 1 ? dValues[1] : 0;
            double d3 = dValues.Count > 2 ? dValues[2] : 0;
            double tol = 0.04; 

            using var conn = new SqliteConnection(_sqliteConn);
            await conn.OpenAsync();
            var cmd = conn.CreateCommand();
            
            cmd.CommandText = @"
                SELECT cod_id, COUNT(*) as hit_count 
        FROM hanawalt_peaks 
        WHERE (d_spacing BETWEEN @d1_min AND @d1_max)
           OR (@d2 > 0 AND d_spacing BETWEEN @d2_min AND @d2_max)
           OR (@d3 > 0 AND d_spacing BETWEEN @d3_min AND @d3_max)
        GROUP BY cod_id
        ORDER BY hit_count DESC
        LIMIT 800"; 

    cmd.Parameters.AddWithValue("@d1_min", d1 - tol);
    cmd.Parameters.AddWithValue("@d1_max", d1 + tol);
    cmd.Parameters.AddWithValue("@d2", d2);
    cmd.Parameters.AddWithValue("@d2_min", d2 - tol);
    cmd.Parameters.AddWithValue("@d2_max", d2 + tol);
    cmd.Parameters.AddWithValue("@d3", d3);
    cmd.Parameters.AddWithValue("@d3_min", d3 - tol);
    cmd.Parameters.AddWithValue("@d3_max", d3 + tol);

    using var reader = await cmd.ExecuteReaderAsync();
    while (reader.Read()) 
    {
        ids.Add(reader.GetInt32(0));
    }
    
    Console.WriteLine($"[HANAWALT] Red de arrastre inteligente encontró {ids.Count} candidatos pre-filtrados.");
    return ids;
}

        private async Task<List<CodResult>> EnrichWithMetadata(List<PythonCandidate> pyCandidates)
        {
            var enrichedList = new List<CodResult>();
            if (pyCandidates == null || pyCandidates.Count == 0) return enrichedList;

            using var conn = new MySqlConnection(_mysqlConn);
            await conn.OpenAsync();

            string ids = string.Join(",", pyCandidates.Select(c => c.Id));
            string sql = $@"SELECT file, formula, commonname, chemname, a, b, c, alpha, beta, gamma 
                            FROM data WHERE file IN ({ids})";

            using var cmd = new MySqlCommand(sql, conn);
            using var reader = await cmd.ExecuteReaderAsync();

            while (reader.Read())
            {
                int id = reader.GetInt32("file");
                var pyData = pyCandidates.FirstOrDefault(c => c.Id == id);

                enrichedList.Add(new CodResult {
                    Id = id,
                    MatchScore = pyData?.Match_score ?? 0, 
                    Formula = reader.IsDBNull(1) ? "N/A" : reader.GetString(1),
                    Name = !reader.IsDBNull(2) ? reader.GetString(2) : (!reader.IsDBNull(3) ? reader.GetString(3) : "Fase Desconocida"),
                    A = reader.IsDBNull(4) ? 0 : reader.GetDouble(4),
                    B = reader.IsDBNull(5) ? 0 : reader.GetDouble(5),
                    C = reader.IsDBNull(6) ? 0 : reader.GetDouble(6),
                    Alpha = reader.IsDBNull(7) ? 90 : reader.GetDouble(7),
                    Beta = reader.IsDBNull(8) ? 90 : reader.GetDouble(8),
                    Gamma = reader.IsDBNull(9) ? 90 : reader.GetDouble(9),
                    TheoreticalPeaks = pyData?.TheoreticalPeaks ?? new List<PeakData>()
                });
            }

            return enrichedList.OrderByDescending(x => x.MatchScore).ToList();
        }

        private class ScoredResponse 
        { 
            public List<PythonCandidate> Candidates { get; set; } = new(); 
        }

        private class PythonCandidate 
{ 
    [JsonPropertyName("id")]
    public int Id { get; set; } 
    
    [JsonPropertyName("match_score")]
    public double Match_score { get; set; } 
    
    [JsonPropertyName("theoreticalPeaks")] 
    public List<PeakData> TheoreticalPeaks { get; set; } = new();
}
    }
}
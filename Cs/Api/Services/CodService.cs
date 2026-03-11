using MySqlConnector;
using Api.Models;

namespace Api.Services
{
    public class CodService
    {
        private readonly string _connectionString;

        public CodService(string connectionString)
        {
            _connectionString = connectionString;
        }

        public async Task<List<string>> SearchCandidatesAsync(double[] mainPeaks)
        {
            var candidates = new List<string>();
            
            using var connection = new MySqlConnection(_connectionString);
            await connection.OpenAsync();

            string query = @"SELECT file_id, formula FROM data 
                             WHERE d_spacing BETWEEN @min AND @max 
                             LIMIT 10;";

            using var command = new MySqlCommand(query, connection);
            command.Parameters.AddWithValue("@min", mainPeaks[0] - 0.05);
            command.Parameters.AddWithValue("@max", mainPeaks[0] + 0.05);

            using var reader = await command.ExecuteReaderAsync();
            while (await reader.ReadAsync())
            {
                candidates.Add($"{reader.GetString("file_id")} - {reader.GetString("formula")}");
            }

            return candidates;
        }
    }
}
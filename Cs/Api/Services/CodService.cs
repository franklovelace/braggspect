using MySqlConnector;
using Api.Models;

namespace Api.Services;

public class CodService
{
    private readonly string _connectionString = 
        "Server=sql.crystallography.net;Port=3306;Database=cod;Uid=cod_reader;Pwd=;";

  public async Task<List<CodResult>> SearchByFormulaAsync(string searchTerm)
{
    var results = new List<CodResult>();
    using var connection = new MySqlConnection(_connectionString);
    await connection.OpenAsync();

    string sql = @"
        SELECT file, formula, commonname, year, a, b, c, alpha, beta, gamma 
        FROM data 
        WHERE (formula LIKE @term 
           OR commonname LIKE @term 
           OR chemname LIKE @term 
           OR mineral LIKE @term)
        ORDER BY year DESC 
        LIMIT 15";

    using var command = new MySqlCommand(sql, connection);
    command.Parameters.AddWithValue("@term", $"%{searchTerm}%");

    using var reader = await command.ExecuteReaderAsync();
    while (await reader.ReadAsync())
    {
        results.Add(new CodResult {
            Id = reader.GetInt32("file"),
            Formula = reader.IsDBNull(reader.GetOrdinal("formula")) ? "N/A" : reader.GetString("formula"),
            Name = reader.IsDBNull(reader.GetOrdinal("commonname")) ? "Mineral" : reader.GetString("commonname"),
            Year = reader.IsDBNull(reader.GetOrdinal("year")) ? null : reader.GetInt32("year"),
            A = reader.IsDBNull(4) ? null : Convert.ToDouble(reader.GetValue(4)),
            B = reader.IsDBNull(5) ? null : Convert.ToDouble(reader.GetValue(5)),
            C = reader.IsDBNull(6) ? null : Convert.ToDouble(reader.GetValue(6)),
            Alpha = reader.IsDBNull(7) ? null : Convert.ToDouble(reader.GetValue(7)),
            Beta = reader.IsDBNull(8) ? null : Convert.ToDouble(reader.GetValue(8)),
            Gamma = reader.IsDBNull(9) ? null : Convert.ToDouble(reader.GetValue(9))
        });
    }
    return results;
}
}
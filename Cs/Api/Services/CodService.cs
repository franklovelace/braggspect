using MySqlConnector;
using Api.Models;

namespace Api.Services;

public class CodService
{
    private readonly string _connectionString = 
        "Server=sql.crystallography.net;Port=3306;Database=cod;Uid=cod_reader;Pwd=;";

   public async Task<List<CodResult>> SearchByFormulaAsync(string formula)
{
    var results = new List<CodResult>();
    using var connection = new MySqlConnection(_connectionString);
    await connection.OpenAsync();

    string sql = "SELECT file, formula, commonname, year, a, b, c, alpha, beta, gamma FROM data WHERE formula LIKE @formula LIMIT 10";

    using var command = new MySqlCommand(sql, connection);
    command.Parameters.AddWithValue("@formula", $"%{formula}%");

    using var reader = await command.ExecuteReaderAsync();
    while (await reader.ReadAsync())
    {
        results.Add(new CodResult 
        {
            Id = reader.GetInt32(reader.GetOrdinal("file")),
            Formula = reader.IsDBNull(reader.GetOrdinal("formula")) ? "N/A" : reader.GetString("formula"),
            Name = reader.IsDBNull(reader.GetOrdinal("commonname")) ? "Mineral" : reader.GetString("commonname"),
            Year = reader.IsDBNull(reader.GetOrdinal("year")) ? null : reader.GetInt32("year"),
            
            A = reader.IsDBNull(reader.GetOrdinal("a")) ? null : Convert.ToDouble(reader.GetValue(reader.GetOrdinal("a"))),
            B = reader.IsDBNull(reader.GetOrdinal("b")) ? null : Convert.ToDouble(reader.GetValue(reader.GetOrdinal("b"))),
            C = reader.IsDBNull(reader.GetOrdinal("c")) ? null : Convert.ToDouble(reader.GetValue(reader.GetOrdinal("c"))),
            Alpha = reader.IsDBNull(reader.GetOrdinal("alpha")) ? null : Convert.ToDouble(reader.GetValue(reader.GetOrdinal("alpha"))),
            Beta = reader.IsDBNull(reader.GetOrdinal("beta")) ? null : Convert.ToDouble(reader.GetValue(reader.GetOrdinal("beta"))),
            Gamma = reader.IsDBNull(reader.GetOrdinal("gamma")) ? null : Convert.ToDouble(reader.GetValue(reader.GetOrdinal("gamma")))
        });
    }

    return results; 
}
}
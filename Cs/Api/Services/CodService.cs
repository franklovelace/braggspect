using MySqlConnector;

namespace Api.Services;

public class CodService
{
    private readonly string _connectionString = 
        "Server=sql.crystallography.net;Port=3306;Database=cod;Uid=cod_reader;Pwd=;";

    public async Task<List<string>> SearchByFormulaAsync(string formula)
{
    var results = new List<string>();
    using var connection = new MySqlConnection(_connectionString);
    await connection.OpenAsync();

    string sql = @"SELECT file, formula, commonname, year 
                   FROM data 
                   WHERE formula LIKE @formula OR commonname LIKE @formula 
                   ORDER BY year DESC 
                   LIMIT 10";

    using var command = new MySqlCommand(sql, connection);
    command.Parameters.AddWithValue("@formula", $"%{formula}%");

    using var reader = await command.ExecuteReaderAsync();
    while (await reader.ReadAsync())
    {
        var id = reader.GetInt32("file");
        var f = reader.IsDBNull(reader.GetOrdinal("formula")) ? "?" : reader.GetString("formula");
        var n = reader.IsDBNull(reader.GetOrdinal("commonname")) ? "Mineral" : reader.GetString("commonname");
        var y = reader.IsDBNull(reader.GetOrdinal("year")) ? "" : reader.GetInt32("year").ToString();
        
        results.Add($"[COD {id}] {f} - {n} ({y})");
    }
    return results;
}
}
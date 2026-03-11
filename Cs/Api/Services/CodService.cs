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

    string sql = "SELECT * FROM data WHERE formula LIKE @formula LIMIT 5";

    using var command = new MySqlCommand(sql, connection);
    command.Parameters.AddWithValue("@formula", $"%{formula}%");

    using var reader = await command.ExecuteReaderAsync();
    
    var columnNames = Enumerable.Range(0, reader.FieldCount).Select(reader.GetName).ToList();
    Console.WriteLine("Columnas encontradas en COD: " + string.Join(", ", columnNames));

    while (await reader.ReadAsync())
    {
        var idValue = reader.GetValue(0); 
        var formulaValue = reader["formula"]?.ToString() ?? "N/A";
        
        results.Add($"Resultado: ID {idValue} - Formula: {formulaValue}");
    }
    return results;
}

}
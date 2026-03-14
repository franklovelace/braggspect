using MySqlConnector;
using Api.Models;

namespace Api.Services;

public class HanawaltService
{
    private readonly string _connectionString = 
        "Server=sql.crystallography.net;Port=3306;Database=cod;Uid=cod_reader;Pwd=;";

 public async Task<List<CodResult>> SearchByDSpacingAsync(List<double> dValues, double tolerance = 0.01)
{
    var results = new List<CodResult>();
    double d1 = dValues[0];

    using var connection = new MySqlConnection(_connectionString);
    await connection.OpenAsync();

    string sql = @"
        SELECT file, formula, commonname, year, a, b, c, alpha, beta, gamma 
        FROM data 
        WHERE (a BETWEEN @min AND @max OR b BETWEEN @min AND @max OR c BETWEEN @min AND @max)
        LIMIT 1000"; 

    using var command = new MySqlCommand(sql, connection);
    command.Parameters.AddWithValue("@min", d1 - tolerance);
    command.Parameters.AddWithValue("@max", d1 + tolerance);

    using var reader = await command.ExecuteReaderAsync();
    while (await reader.ReadAsync()) {
        results.Add(new CodResult { 
            Id = reader.GetInt32("file"),
        });
    }

    Console.WriteLine($"[DEBUG] Búsqueda Hanawalt finalizada.");
    Console.WriteLine($"[DEBUG] d1: {d1} Å | Tolerancia: {tolerance}");
    Console.WriteLine($"[DEBUG] TOTAL DE CANDIDATOS ENCONTRADOS: {results.Count}");

    return results;
}
}
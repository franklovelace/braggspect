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
        if (dValues == null || dValues.Count == 0) return results;
        
        double d1 = dValues[0];

        using var connection = new MySqlConnection(_connectionString);
        await connection.OpenAsync();

        string sql = @"
            SELECT file, formula, commonname, chemname, mineral, year, a, b, c, alpha, beta, gamma 
            FROM data 
            WHERE (a BETWEEN @min AND @max OR b BETWEEN @min AND @max OR c BETWEEN @min AND @max)
            AND a IS NOT NULL AND a > 0
            LIMIT 200"; 

        using var command = new MySqlCommand(sql, connection);
        command.Parameters.AddWithValue("@min", d1 - tolerance);
        command.Parameters.AddWithValue("@max", d1 + tolerance);

        using var reader = await command.ExecuteReaderAsync();
        while (await reader.ReadAsync()) 
        {
            string name = "Fase Desconocida";
            if (!reader.IsDBNull(reader.GetOrdinal("commonname"))) 
                name = reader.GetString("commonname");
            else if (!reader.IsDBNull(reader.GetOrdinal("chemname"))) 
                name = reader.GetString("chemname");
            else if (!reader.IsDBNull(reader.GetOrdinal("mineral"))) 
                name = reader.GetString("mineral");
            else if (!reader.IsDBNull(reader.GetOrdinal("formula"))) 
                name = reader.GetString("formula");

            results.Add(new CodResult 
            { 
                Id = reader.GetInt32("file"),
                Formula = reader.IsDBNull(reader.GetOrdinal("formula")) ? "N/A" : reader.GetString("formula"),
                Name = name,
                Year = reader.IsDBNull(reader.GetOrdinal("year")) ? null : reader.GetInt32("year"),
                
                A = reader.IsDBNull(reader.GetOrdinal("a")) ? 0 : Convert.ToDouble(reader.GetValue(reader.GetOrdinal("a"))),
                B = reader.IsDBNull(reader.GetOrdinal("b")) ? 0 : Convert.ToDouble(reader.GetValue(reader.GetOrdinal("b"))),
                C = reader.IsDBNull(reader.GetOrdinal("c")) ? 0 : Convert.ToDouble(reader.GetValue(reader.GetOrdinal("c"))),
                
                Alpha = reader.IsDBNull(reader.GetOrdinal("alpha")) ? 90 : Convert.ToDouble(reader.GetValue(reader.GetOrdinal("alpha"))),
                Beta = reader.IsDBNull(reader.GetOrdinal("beta")) ? 90 : Convert.ToDouble(reader.GetValue(reader.GetOrdinal("beta"))),
                Gamma = reader.IsDBNull(reader.GetOrdinal("gamma")) ? 90 : Convert.ToDouble(reader.GetValue(reader.GetOrdinal("gamma")))
            });
        }

        Console.WriteLine($"[DEBUG] Búsqueda Hanawalt finalizada.");
        Console.WriteLine($"[DEBUG] d1 buscado: {d1} Å | Tolerancia: {tolerance}");
        Console.WriteLine($"[DEBUG] TOTAL DE CANDIDATOS VÁLIDOS ENCONTRADOS: {results.Count}");

        return results;
    }
}
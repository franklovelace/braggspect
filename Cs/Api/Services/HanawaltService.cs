using MySqlConnector;
using Api.Models;

namespace Api.Services;

public class HanawaltService
{
    private readonly string _connectionString = 
        "Server=sql.crystallography.net;Port=3306;Database=cod;Uid=cod_reader;Pwd=;";

    public async Task<List<CodResult>> SearchByDSpacingAsync(List<double> dValues, double tolerance = 0.05)
    {
        var results = new List<CodResult>();

        if (dValues == null || dValues.Count == 0) return results;
         double d1 = dValues[0];
         double d2 = dValues.Count > 1 ? dValues[1] : 0;

        using var connection = new MySqlConnection(_connectionString);
        try 
        {
            await connection.OpenAsync();
            
             string sql = @"
        SELECT file, formula, commonname, year, a, b, c, alpha, beta, gamma 
        FROM data 
        WHERE (a BETWEEN @d1min AND @d1max OR b BETWEEN @d1min AND @d1max OR c BETWEEN @d1min AND @d1max)
        AND (@d2 = 0 OR a BETWEEN @d2min AND @d2max OR b BETWEEN @d2min AND @d2max OR c BETWEEN @d2min AND @d2max)
        ORDER BY year DESC LIMIT 20";

             using var command = new MySqlCommand(sql, connection);
    command.Parameters.AddWithValue("@d1min", d1 - tolerance);
    command.Parameters.AddWithValue("@d1max", d1 + tolerance);
    command.Parameters.AddWithValue("@d2", d2);
    command.Parameters.AddWithValue("@d2min", d2 - (tolerance * 2)); 
    command.Parameters.AddWithValue("@d2max", d2 + (tolerance * 2));

            using var reader = await command.ExecuteReaderAsync();
            while (await reader.ReadAsync())
            {
                results.Add(new CodResult {
                    Id = reader.GetInt32("file"),
                    Formula = reader.IsDBNull(1) ? "N/A" : reader.GetString(1),
                    Name = reader.IsDBNull(2) ? "Fase Desconocida" : reader.GetString(2),
                    Year = reader.IsDBNull(3) ? null : reader.GetInt32(3),
                    A = reader.IsDBNull(4) ? null : Convert.ToDouble(reader.GetValue(4)),
                    B = reader.IsDBNull(5) ? null : Convert.ToDouble(reader.GetValue(5)),
                    C = reader.IsDBNull(6) ? null : Convert.ToDouble(reader.GetValue(6))
                });
            }
        }
        catch (MySqlException ex)
        {
            throw new Exception("La base de datos de picos de la COD no respondió. Verifique su conexión.", ex);
        }

        return results;
    }
}
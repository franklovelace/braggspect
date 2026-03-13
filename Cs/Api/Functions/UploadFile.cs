using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Azure.Functions.Worker;
using Api.Parsers;
using Api.Models;
using System.Text.Json;
using System.Net.Http.Json;

namespace Api.Functions;

public class UploadFile
{
    private readonly CsvParser _parser;
    private readonly HttpClient _httpClient;

    public UploadFile(CsvParser parser)
    {
        _parser = parser;
        _httpClient = new HttpClient();
    }

    [Function("UploadFile")]
public async Task<IActionResult> Run(
    [HttpTrigger(AuthorizationLevel.Anonymous, "post", Route = "upload")] HttpRequest req)
{
    var form = await req.ReadFormAsync();
    var file = form.Files.GetFile("file");
    
    if (file == null) 
        return new BadRequestObjectResult("No se subió ningún archivo.");

    var anode = form.ContainsKey("anode") ? form["anode"].ToString() : "Cu";
    var isStripped = form.ContainsKey("isStripped") && form["isStripped"] == "true";

    using var stream = file.OpenReadStream();
    var data = _parser.Parse(stream);
    data.Anode = anode;

    try
    {
        var pyRequest = new {
            two_theta = data.TwoTheta,
            intensity = data.Intensity,
            anode = anode,
            is_stripped = isStripped 
        };

        var response = await _httpClient.PostAsJsonAsync("http://localhost:8000/api/math/process", pyRequest);
        
        if (response.IsSuccessStatusCode)
        {
            var pyResult = await response.Content.ReadFromJsonAsync<JsonElement>();
            
            var cleanedArray = pyResult.GetProperty("cleaned_intensity").EnumerateArray().Select(x => x.GetDouble()).ToArray();
            data.Intensity = cleanedArray; 
            
            if (pyResult.TryGetProperty("top_peaks", out JsonElement peaksElement))
            {
                data.TopPeaks = JsonSerializer.Deserialize<List<PeakData>>(peaksElement.GetRawText(), 
                    new JsonSerializerOptions { PropertyNameCaseInsensitive = true }) ?? new List<PeakData>();
            }
        }
    }
    catch (Exception ex)
    {
        Console.WriteLine($"Error conectando al motor Python: {ex.Message}");
    }

    return new OkObjectResult(data);
}
}
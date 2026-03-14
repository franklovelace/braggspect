using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Azure.Functions.Worker;
using Api.Services;
using System.Text.Json;

namespace Api.Functions;

public class SearchHanawalt
{
    private readonly HanawaltService _hanawaltService;

    public SearchHanawalt(HanawaltService hanawaltService)
    {
        _hanawaltService = hanawaltService;
    }

    [Function("SearchHanawalt")]
    public async Task<IActionResult> Run(
        [HttpTrigger(AuthorizationLevel.Anonymous, "post", Route = "search/hanawalt")] HttpRequest req)
    {
        var body = await new StreamReader(req.Body).ReadToEndAsync();
        var dValues = JsonSerializer.Deserialize<List<double>>(body);

        if (dValues == null) return new BadRequestObjectResult("Se requieren distancias d.");

        try 
        {
            var results = await _hanawaltService.SearchByDSpacingAsync(dValues);
            return new OkObjectResult(results);
        }
        catch (Exception)
        {
            return new StatusCodeResult(503); 
        }
    }
}
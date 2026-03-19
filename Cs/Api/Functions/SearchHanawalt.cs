using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Azure.Functions.Worker;
using Api.Services;
using Api.Models;
using System.Text.Json;
using System.IO;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using System.Linq;

namespace Api.Functions
{
    public class SearchRequest 
    {
        public List<double> DValues { get; set; } = new();
        public double[] X { get; set; } = Array.Empty<double>();
        public double[] Y { get; set; } = Array.Empty<double>();
        public string Anode { get; set; } = "Cu";
    }

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
            try 
            {
                string requestBody = await new StreamReader(req.Body).ReadToEndAsync();
                var options = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
                var data = JsonSerializer.Deserialize<SearchRequest>(requestBody, options);

                if (data == null || data.DValues.Count == 0) 
                {
                    return new BadRequestObjectResult("Datos insuficientes: Se requieren DValues, X e Y.");
                }

                var results = await _hanawaltService.PipelineSearchAsync(
                    data.DValues, 
                    data.X, 
                    data.Y, 
                    data.Anode
                );

                return new OkObjectResult(results);
            }
            catch (Exception ex)
            {
                Console.WriteLine("\n[PIPELINE EXCEPTION]");
                Console.WriteLine($"Mensaje: {ex.Message}");
                if (ex.InnerException != null) 
                    Console.WriteLine($"Inner: {ex.InnerException.Message}");
                
                return new ObjectResult(new { error = ex.Message }) { StatusCode = 500 };
            }
        }
    }
}
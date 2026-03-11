using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Azure.Functions.Worker;
using Api.Services;

namespace Api.Functions
{
    public class SearchCod
    {
        private readonly CodService _codService;

        public SearchCod(CodService codService)
        {
            _codService = codService;
        }

        [Function("SearchCod")]
        public async Task<IActionResult> Run(
            [HttpTrigger(AuthorizationLevel.Anonymous, "get", Route = "search/{formula}")] HttpRequest req,
            string formula)
        {
            var results = await _codService.SearchByFormulaAsync(formula);
            return new OkObjectResult(results);
        }
    }
}
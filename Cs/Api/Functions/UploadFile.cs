using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Azure.Functions.Worker;
using Api.Parsers;

namespace Api.Functions;

public class UploadFile
{
    private readonly CsvParser _parser; 

    public UploadFile(CsvParser parser)
    {
        _parser = parser;
    }

    [Function("UploadFile")]
    public async Task<IActionResult> Run(
        [HttpTrigger(AuthorizationLevel.Anonymous, "post")] HttpRequest req)
    {
        var file = req.Form.Files.GetFile("file");
        if (file == null) return new BadRequestObjectResult("No se subió ningún archivo.");

        using var stream = file.OpenReadStream();
        var data = _parser.Parse(stream);

        return new OkObjectResult(data);
    }
}
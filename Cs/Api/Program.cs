using Microsoft.Azure.Functions.Worker;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.DependencyInjection;
using Api.Services;
using Api.Parsers;

var host = new HostBuilder()
    .ConfigureFunctionsWebApplication() 
    .ConfigureServices(services =>
    {
        services.AddApplicationInsightsTelemetryWorkerService();
        services.ConfigureFunctionsApplicationInsights();

        services.AddSingleton<CodService>();
        services.AddSingleton<CsvParser>();
        services.AddSingleton<HanawaltService>(); 


    })
    .Build();

host.Run();
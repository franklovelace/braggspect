using Api.Models;
using System.Globalization;

namespace Api.Parsers;

public class CsvParser : IParser
{
    public string SupportedExtension => ".csv";

    public DrxDisplayData Parse(Stream stream)
    {
        var twoTheta = new List<double>();
        var intensity = new List<double>();

        using var reader = new StreamReader(stream);
        while (!reader.EndOfStream)
        {
            var line = reader.ReadLine();
            if (string.IsNullOrWhiteSpace(line)) continue;

            var parts = line.Split(new[] { ',', ';' });
            if (parts.Length >= 2 &&
                double.TryParse(parts[0], CultureInfo.InvariantCulture, out double tt) &&
                double.TryParse(parts[1], CultureInfo.InvariantCulture, out double i))
            {
                twoTheta.Add(tt);
                intensity.Add(i);
            }
        }

        return new DrxDisplayData 
        { 
            SampleName = "Archivo Importado",
            TwoTheta = twoTheta.ToArray(),
            Intensity = intensity.ToArray()
        };
    }
}
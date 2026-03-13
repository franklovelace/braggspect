using System.Text.Json.Serialization;

namespace Api.Models; 
public class PeakData
{
    [JsonPropertyName("two_theta")] 
    public double TwoTheta { get; set; }

    [JsonPropertyName("d_spacing")]
    public double DSpacing { get; set; }

    [JsonPropertyName("intensity")]
    public double Intensity { get; set; }
}

public class DrxDisplayData
{
    public string SampleName { get; set; } = string.Empty;
    public double[] TwoTheta { get; set; } = Array.Empty<double>();
    public double[] Intensity { get; set; } = Array.Empty<double>();
    public string Anode { get; set; } = "Cu";
    public List<PeakData> TopPeaks { get; set; } = new List<PeakData>();
}
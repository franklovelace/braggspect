namespace Api.Models; 
public class DrxDisplayData
{
    public string SampleName { get; set; } = string.Empty;
    public double[] TwoTheta { get; set; } = Array.Empty<double>();
    public double[] Intensity { get; set; } = Array.Empty<double>();
    public string Anode { get; set; } = "Cu";
    public double Wavelength { get; set; } = 1.5406;
}
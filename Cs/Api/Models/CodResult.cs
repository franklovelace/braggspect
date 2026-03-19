namespace Api.Models;

public class CodResult
{
    public int Id { get; set; }
    public string Formula { get; set; } = "";
    public string Name { get; set; } = "";
    public double MatchScore { get; set; }
    public int? Year { get; set; }
    public double? A { get; set; }
    public double? B { get; set; }
    public double? C { get; set; }//oh, ya las habia hecho nulleables, perfecto
    public double? Alpha { get; set; }
    public double? Beta { get; set; }
    public double? Gamma { get; set; }
    public List<PeakData> TheoreticalPeaks { get; set; } = new List<PeakData>();
}
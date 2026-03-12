using Api.Models;

namespace Api.Parsers;

public interface IParser
{
    string SupportedExtension { get; }
    DrxDisplayData Parse(Stream stream);
}
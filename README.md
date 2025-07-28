# Earnings Presentations and Corporate Materials Fetcher

A comprehensive Python tool to fetch earnings presentations, corporate presentations, CEO interviews, product demos, investor day recordings, podcasts, and special events for publicly traded companies from the most recent fiscal quarter.

## Features

- **Multi-Source Scraping**: Searches across multiple trusted financial sources
- **Intelligent Date Filtering**: Focuses on the most recent fiscal quarter
- **Duplicate Detection**: Eliminates duplicate content across sources
- **Rate Limiting**: Respectful scraping with configurable delays
- **Multiple Output Formats**: Text, CSV, and JSON export options
- **Parallel Processing**: Efficient multi-threaded scraping
- **Comprehensive Error Handling**: Robust error handling and logging

## Document Types Supported

- Earnings presentation decks (quarterly earnings slides)
- Capital Markets Day or Investor Update decks
- CEO/CFO/Executive interviews
- Investor-related podcasts or presentations
- Product demo videos or technical briefings
- Special investor media or strategic announcements

## Trusted Sources (Priority Order)

1. **Company's Official Investor Relations Website**
2. **SEC EDGAR Filings** (10-Q or 8-K filings containing presentations)
3. **Nasdaq Official Company Profile**
4. **Yahoo Finance Events**
5. **Company's Official YouTube, Vimeo, or Media Channels**

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Required Packages

- `requests` - HTTP library for making requests
- `beautifulsoup4` - HTML/XML parsing
- `yfinance` - Yahoo Finance API wrapper
- `lxml` - XML/HTML parser

## Usage

### Basic Usage

```bash
# Basic usage with stock symbol
python enhanced_earnings_fetcher.py AAPL

# Basic usage with the original script
python earnings_fetcher.py AAPL
```

### Advanced Usage

```bash
# Export to specific format only
python enhanced_earnings_fetcher.py AAPL --format csv

# Customize rate limiting (requests per second)
python enhanced_earnings_fetcher.py AAPL --rate-limit 2.0

# Set custom days threshold for recent content
python enhanced_earnings_fetcher.py AAPL --days 120

# Export to all formats (default)
python enhanced_earnings_fetcher.py AAPL --format all
```

### Command Line Options

- `symbol`: Stock symbol (required, e.g., AAPL, MSFT, GOOGL)
- `--format`: Output format (`text`, `csv`, `json`, `all`)
- `--rate-limit`: Rate limit between requests in seconds (default: 1.0)
- `--days`: Days threshold for recent content (default: 90)

## Output Format

The tool returns results in the exact format specified:

```
Title: [Document Title]
Date: [Publication Date]
Speaker(s): [CEO, CFO, or Executive Name]
Format: [PDF / MP4 / HTML / Web Archive]
Direct Source URL: [Direct Link to Document]
```

## Example Output

```
Earnings Presentations and Corporate Materials for AAPL
================================================================================

Source: SEC EDGAR
----------------------------------------
1. Title: Apple Inc. Q1 2024 Earnings Call Presentation
   Date: 2024-01-25
   Speaker(s): Tim Cook, Luca Maestri
   Format: PDF
   Direct Source URL: https://www.sec.gov/Archives/edgar/data/320193/000032019324000006/aapl-20231230.htm
   Description: Q1 2024 earnings presentation materials

Source: Company IR Site
----------------------------------------
1. Title: Apple Q1 2024 Earnings Conference Call
   Date: 2024-01-25
   Speaker(s): Tim Cook, Luca Maestri
   Format: MP4
   Direct Source URL: https://investor.apple.com/events-and-presentations/event-details/2024/Apple-Q1-2024-Earnings-Conference-Call/default.aspx
   Description: Webcast recording of Q1 2024 earnings call

2. Title: Apple Q1 2024 Financial Results
   Date: 2024-01-25
   Speaker(s): Company Executive
   Format: PDF
   Direct Source URL: https://investor.apple.com/earnings-call-transcripts/2024/01/25/apple-q1-2024-financial-results
   Description: Quarterly financial results presentation
```

## File Types Returned

- **PDF**: Presentation slides, financial reports
- **MP4**: Video recordings, webcasts, product demos
- **PPT/PPTX**: PowerPoint presentations
- **MP3**: Audio recordings, podcasts
- **HTML**: Web pages with embedded content
- **XLS/XLSX**: Financial data spreadsheets

## Scripts Overview

### 1. `earnings_fetcher.py` (Basic Version)
- Simple, single-threaded implementation
- Good for basic use cases
- Easier to understand and modify

### 2. `enhanced_earnings_fetcher.py` (Advanced Version)
- Multi-threaded parallel processing
- Enhanced error handling and logging
- Multiple export formats (CSV, JSON, Text)
- More sophisticated source detection
- Better duplicate handling

## Error Handling

The tool includes comprehensive error handling:

- **Network Errors**: Automatic retry with exponential backoff
- **Rate Limiting**: Respectful delays between requests
- **Invalid URLs**: Graceful handling of broken links
- **Missing Data**: Fallback to alternative sources
- **Logging**: Detailed logs for debugging

## Rate Limiting and Ethics

The tool implements ethical scraping practices:

- Configurable delays between requests (default: 1 second)
- Respectful User-Agent headers
- No aggressive crawling
- Compliance with robots.txt (where applicable)

## Troubleshooting

### Common Issues

1. **No results found**
   - Check if the stock symbol is correct
   - Verify the company has recent earnings materials
   - Try increasing the `--days` parameter

2. **Network errors**
   - Check your internet connection
   - Increase the `--rate-limit` parameter
   - Some sources may be temporarily unavailable

3. **Import errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python version (requires 3.7+)

### Debug Mode

For detailed logging, the script automatically logs all operations. Check the console output for detailed information about the scraping process.

## Limitations

- **Paywalled Content**: Cannot access premium or paywalled materials
- **Dynamic Content**: Some modern websites use JavaScript that may not be fully parsed
- **Rate Limits**: Some sources may block requests if too frequent
- **Data Availability**: Depends on what companies actually publish

## Contributing

To improve the tool:

1. Add new source integrations
2. Enhance parsing logic for existing sources
3. Improve error handling
4. Add support for additional file formats
5. Optimize performance

## License

This tool is provided for educational and research purposes. Please respect the terms of service of the websites being scraped.

## Disclaimer

This tool is designed for legitimate research and analysis purposes. Users are responsible for:

- Complying with website terms of service
- Respecting rate limits and robots.txt
- Using the data responsibly and legally
- Verifying the accuracy of retrieved information

The authors are not responsible for any misuse of this tool or the data it retrieves.
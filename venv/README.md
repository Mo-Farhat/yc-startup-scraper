# YC Startup Scraper

A Python scraper that collects structured data for Y Combinator startups, including company metadata and founder LinkedIn information.

## Features

- **Fast Async Scraping**: Uses `aiohttp` for concurrent requests (~3-5 min for 500 companies)
- **Founder Extraction**: Parses founder names and LinkedIn URLs from YC company pages
- **Progress Tracking**: Real-time progress bar with `tqdm`
- **Resilient**: Includes retry logic, rate limiting, and error handling

## Installation

```bash
# Activate the virtual environment
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Scrape 500 companies (default)
python main.py

# Scrape a specific number of companies
python main.py --limit 100

# Custom output filename
python main.py --output my_data.csv
```

## Output Format

The scraper generates a CSV file with the following columns:

| Column                 | Description                           |
| ---------------------- | ------------------------------------- |
| `company_name`         | Name of the startup                   |
| `batch`                | YC batch (e.g., "Winter 2012")        |
| `short_description`    | One-liner description                 |
| `founder_name`         | Founder's full name                   |
| `founder_linkedin_url` | LinkedIn profile URL (when available) |

> **Note**: Companies with multiple founders will have multiple rows in the output.

## Approach Summary

1. **Fetch Company List**: Use YC OSS public API (`yc-oss.github.io/api/companies/all.json`)
2. **Extract Metadata**: Parse company name, batch, description, and slug
3. **Scrape Detail Pages**: Fetch HTML from `ycombinator.com/companies/{slug}`
4. **Parse Founders**: Extract founder names and LinkedIn URLs using BeautifulSoup
5. **Export CSV**: Generate timestamped CSV with pandas

## Project Structure

```
├── main.py              # Entry point with CLI
├── requirements.txt     # Dependencies
├── scraper/
│   ├── api_client.py    # YC API fetching
│   ├── html_parser.py   # Founder extraction
│   ├── csv_exporter.py  # CSV generation
│   └── utils.py         # Rate limiting, logging
└── output/              # Generated CSV files
```

## Limitations

- Founder LinkedIn URLs may not be available for all companies
- HTML structure changes on YC website may require parser updates
- Rate limiting is applied to avoid overwhelming the server

## License

MIT

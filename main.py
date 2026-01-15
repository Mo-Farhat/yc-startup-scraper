#!/usr/bin/env python3
"""
YC Startup Scraper - Main Entry Point

Scrapes Y Combinator startup data including company metadata and founder LinkedIn information.
Uses async/await for fast, concurrent scraping of 500+ companies.

Usage:
    python main.py                    # Scrape 500 companies (default)
    python main.py --limit 100        # Scrape 100 companies
    python main.py --output data.csv  # Custom output filename
"""

import argparse
import asyncio
import sys
from datetime import datetime

import aiohttp
from tqdm.asyncio import tqdm_asyncio

from scraper.api_client import fetch_all_companies, extract_company_metadata, fetch_company_page
from scraper.html_parser import parse_founders_from_html
from scraper.csv_exporter import export_to_csv, generate_summary
from scraper.utils import logger


async def scrape_company(
    session: aiohttp.ClientSession,
    company: dict,
    pbar: tqdm_asyncio = None
) -> dict:
    """
    Scrape a single company's data including founder information.
    
    Args:
        session: aiohttp client session
        company: Raw company data from API
        pbar: Optional progress bar to update
    
    Returns:
        Company dictionary with extracted metadata and founders
    """
    # Extract basic metadata
    metadata = extract_company_metadata(company)
    
    # Fetch company detail page
    html = await fetch_company_page(session, metadata['slug'])
    
    # Parse founders from HTML
    founders = []
    if html:
        founders = parse_founders_from_html(html, metadata['company_name'])
    
    # Combine metadata with founders
    result = {
        **metadata,
        'founders': founders
    }
    
    if pbar:
        pbar.update(1)
    
    return result


async def scrape_all_companies(
    companies: list[dict],
    concurrency: int = 20
) -> list[dict]:
    """
    Scrape all companies concurrently.
    
    Args:
        companies: List of company data from API
        concurrency: Maximum concurrent requests
    
    Returns:
        List of scraped company data with founders
    """
    connector = aiohttp.TCPConnector(limit=concurrency)
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        # Create progress bar
        pbar = tqdm_asyncio(total=len(companies), desc="Scraping companies")
        
        # Create tasks for all companies
        tasks = [
            scrape_company(session, company, pbar)
            for company in companies
        ]
        
        # Run all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        pbar.close()
    
    # Filter out failed results
    scraped = []
    errors = 0
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.warning(f"Error scraping company {i}: {result}")
            errors += 1
        else:
            scraped.append(result)
    
    if errors > 0:
        logger.warning(f"Encountered {errors} errors during scraping")
    
    return scraped


async def main_async(limit: int = 500, output: str = None) -> str:
    """
    Main async scraper workflow.
    
    Args:
        limit: Maximum number of companies to scrape
        output: Optional custom output filename
    
    Returns:
        Path to the generated CSV file
    """
    start_time = datetime.now()
    logger.info(f"Starting YC Startup Scraper (limit: {limit})")
    
    # Step 1: Fetch all companies from API
    async with aiohttp.ClientSession() as session:
        all_companies = await fetch_all_companies(session)
    
    # Step 2: Select first N companies
    companies_to_scrape = all_companies[:limit]
    logger.info(f"Selected {len(companies_to_scrape)} companies for scraping")
    
    # Step 3: Scrape company details and founders
    scraped_data = await scrape_all_companies(companies_to_scrape)
    
    # Step 4: Export to CSV
    output_path = export_to_csv(scraped_data, filename=output)
    
    # Step 5: Print summary
    summary = generate_summary(scraped_data)
    elapsed = datetime.now() - start_time
    
    print("\n" + "=" * 50)
    print("SCRAPING COMPLETE")
    print("=" * 50)
    print(f"Time elapsed: {elapsed}")
    print(f"Companies scraped: {summary['total_companies']}")
    print(f"Companies with founders: {summary['companies_with_founders']} "
          f"({summary['founder_coverage_pct']:.1f}%)")
    print(f"Total founders found: {summary['total_founders']}")
    print(f"Founders with LinkedIn: {summary['founders_with_linkedin']} "
          f"({summary['linkedin_coverage_pct']:.1f}%)")
    print(f"Output file: {output_path}")
    print("=" * 50)
    
    return output_path


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Scrape YC startup data including founder LinkedIn information"
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=500,
        help="Maximum number of companies to scrape (default: 500)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Custom output filename (default: yc_startups_TIMESTAMP.csv)"
    )
    
    args = parser.parse_args()
    
    # Run async main
    try:
        asyncio.run(main_async(limit=args.limit, output=args.output))
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

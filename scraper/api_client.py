"""
API Client for fetching YC company data.
Uses the public YC OSS API to retrieve company listings.
"""

import aiohttp
from typing import Optional

from .utils import logger, RateLimiter, retry_async


# YC OSS API endpoint for all companies
API_URL = "https://yc-oss.github.io/api/companies/all.json"

# Shared rate limiter instance
rate_limiter = RateLimiter(requests_per_second=10, max_concurrent=20)


async def fetch_all_companies(session: aiohttp.ClientSession) -> list[dict]:
    """
    Fetch all companies from the YC OSS API.
    
    Args:
        session: aiohttp client session for making requests
    
    Returns:
        List of company dictionaries with full metadata
    """
    logger.info(f"Fetching company list from {API_URL}")
    
    async def _fetch():
        await rate_limiter.acquire()
        try:
            async with session.get(API_URL) as response:
                response.raise_for_status()
                return await response.json()
        finally:
            rate_limiter.release()
    
    companies = await retry_async(_fetch)
    logger.info(f"Retrieved {len(companies)} companies from API")
    return companies


def extract_company_metadata(company: dict) -> dict:
    """
    Extract required fields from raw API company data.
    
    Args:
        company: Raw company dictionary from API
    
    Returns:
        Dictionary with standardized fields:
        - company_name, batch, short_description, slug, website, yc_url
    """
    return {
        "company_name": company.get("name", ""),
        "batch": company.get("batch", ""),
        "short_description": company.get("one_liner", ""),
        "slug": company.get("slug", ""),
        "website": company.get("website", ""),
        "yc_url": company.get("url", ""),
    }


async def fetch_company_page(
    session: aiohttp.ClientSession, 
    slug: str
) -> Optional[str]:
    """
    Fetch the HTML content of a YC company detail page.
    
    Args:
        session: aiohttp client session
        slug: Company slug for URL construction
    
    Returns:
        HTML content as string, or None if fetch fails
    """
    url = f"https://www.ycombinator.com/companies/{slug}"
    
    async def _fetch():
        await rate_limiter.acquire()
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; YC-Scraper/1.0)"
            }
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"Failed to fetch {url}: HTTP {response.status}")
                    return None
        finally:
            rate_limiter.release()
    
    try:
        return await retry_async(_fetch, max_retries=2)
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return None

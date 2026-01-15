"""
CSV Exporter for YC Startup Scraper output.
Handles data transformation and file export using pandas.
"""

import os
from datetime import datetime
from typing import Optional

import pandas as pd

from .utils import logger


def create_output_rows(companies_data: list[dict]) -> list[dict]:
    """
    Transform scraped data into CSV rows format.
    Creates one row per founder (companies with multiple founders get multiple rows).
    
    Args:
        companies_data: List of company dictionaries with founder info
        
    Returns:
        List of flattened dictionaries ready for CSV export
    """
    rows = []
    
    for company in companies_data:
        founders = company.get('founders', [])
        
        if founders:
            # Create one row per founder
            for founder in founders:
                rows.append({
                    'company_name': company.get('company_name', ''),
                    'batch': company.get('batch', ''),
                    'short_description': company.get('short_description', ''),
                    'founder_name': founder.get('name', ''),
                    'founder_linkedin_url': founder.get('linkedin_url', ''),
                })
        else:
            # Company with no founders found - still include it
            rows.append({
                'company_name': company.get('company_name', ''),
                'batch': company.get('batch', ''),
                'short_description': company.get('short_description', ''),
                'founder_name': '',
                'founder_linkedin_url': '',
            })
    
    return rows


def export_to_csv(
    data: list[dict], 
    output_dir: str = "output",
    filename: Optional[str] = None
) -> str:
    """
    Export scraped data to a CSV file.
    
    Args:
        data: List of company dictionaries with founder info
        output_dir: Directory to save the output file
        filename: Optional custom filename (defaults to timestamped name)
    
    Returns:
        Path to the created CSV file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename with timestamp if not provided
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"yc_startups_{timestamp}.csv"
    
    # Ensure .csv extension
    if not filename.endswith('.csv'):
        filename += '.csv'
    
    output_path = os.path.join(output_dir, filename)
    
    # Transform data to rows
    rows = create_output_rows(data)
    
    # Create DataFrame and export
    df = pd.DataFrame(rows)
    
    # Ensure column order matches PRD requirements
    columns = [
        'company_name',
        'batch', 
        'short_description',
        'founder_name',
        'founder_linkedin_url'
    ]
    
    # Only include columns that exist
    df = df[[col for col in columns if col in df.columns]]
    
    # Export to CSV
    df.to_csv(output_path, index=False, encoding='utf-8')
    
    logger.info(f"Exported {len(rows)} rows to {output_path}")
    
    return output_path


def generate_summary(data: list[dict]) -> dict:
    """
    Generate summary statistics for the scraped data.
    
    Args:
        data: List of company dictionaries with founder info
    
    Returns:
        Dictionary with summary statistics
    """
    total_companies = len(data)
    companies_with_founders = sum(1 for c in data if c.get('founders'))
    
    total_founders = sum(len(c.get('founders', [])) for c in data)
    founders_with_linkedin = sum(
        1 for c in data 
        for f in c.get('founders', []) 
        if f.get('linkedin_url')
    )
    
    return {
        'total_companies': total_companies,
        'companies_with_founders': companies_with_founders,
        'founder_coverage_pct': (
            companies_with_founders / total_companies * 100 
            if total_companies > 0 else 0
        ),
        'total_founders': total_founders,
        'founders_with_linkedin': founders_with_linkedin,
        'linkedin_coverage_pct': (
            founders_with_linkedin / total_founders * 100 
            if total_founders > 0 else 0
        ),
    }
